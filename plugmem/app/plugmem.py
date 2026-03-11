from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from plugmem.core.graph.graph_store import MemoryGraphStore
from plugmem.core.llm.deepseek import DeepSeekLLM
from plugmem.core.reasoning.memory_reasoner import MemoryReasoner
from plugmem.core.retrieval.retriever import MemoryRetriever, RetrievalInput
from plugmem.core.storage.sqlite_store import SQLiteStore
from plugmem.core.structuring.deduplicator import LLMDeduplicator
from plugmem.core.structuring.procedural_extractor import ProceduralExtractor
from plugmem.core.structuring.segmenter import Segmenter
from plugmem.core.structuring.semantic_extractor import SemanticExtractor
from plugmem.core.structuring.standardizer import EpisodicStandardizer


class PlugMem:
    """Top-level PlugMem orchestration skeleton."""

    def __init__(
        self,
        sqlite_store: SQLiteStore,
        graph_store: MemoryGraphStore,
        standardizer: EpisodicStandardizer,
        semantic_extractor: SemanticExtractor,
        segmenter: Segmenter,
        procedural_extractor: ProceduralExtractor,
        retriever: MemoryRetriever,
        reasoner: MemoryReasoner,
    ) -> None:
        self.sqlite_store = sqlite_store
        self.graph_store = graph_store
        self.standardizer = standardizer
        self.semantic_extractor = semantic_extractor
        self.segmenter = segmenter
        self.procedural_extractor = procedural_extractor
        self.retriever = retriever
        self.reasoner = reasoner

    @classmethod
    def build_default(cls, db_path: str, llm: Any | None = None) -> "PlugMem":
        sqlite_store = SQLiteStore(db_path)
        sqlite_store.configure_pragmas()
        sqlite_store.initialize()
        graph_store = MemoryGraphStore()
        llm = llm or cls.build_llm_from_env()
        deduplicator = LLMDeduplicator(llm=llm, store=sqlite_store)
        return cls(
            sqlite_store=sqlite_store,
            graph_store=graph_store,
            standardizer=EpisodicStandardizer(llm=llm),
            semantic_extractor=SemanticExtractor(llm=llm, deduplicator=deduplicator),
            segmenter=Segmenter(),
            procedural_extractor=ProceduralExtractor(llm=llm, deduplicator=deduplicator),
            retriever=MemoryRetriever(store=sqlite_store),
            reasoner=MemoryReasoner(store=sqlite_store),
        )

    @staticmethod
    def build_llm_from_env(config_path: str | None = None) -> Any | None:
        PlugMem._load_local_env()
        config = PlugMem._load_config(config_path)
        llm_config = config.get("llm", {}) if isinstance(config, dict) else {}
        provider = str(llm_config.get("provider") or os.getenv("PLUGMEM_LLM_PROVIDER") or "deepseek").lower()

        if provider == "none":
            return None

        if provider == "deepseek":
            return DeepSeekLLM(
                api_key=llm_config.get("api_key") or os.getenv("DEEPSEEK_API_KEY"),
                base_url=llm_config.get("base_url") or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
                model=llm_config.get("model") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat",
                temperature=float(llm_config.get("temperature", 0.1)),
            )

        raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def _load_config(config_path: str | None = None) -> dict[str, Any]:
        path = Path(config_path) if config_path else Path(__file__).resolve().parents[1] / "config" / "default.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _load_local_env() -> None:
        candidates = [
            Path.cwd() / ".secrets.env",
            Path(__file__).resolve().parents[2] / ".secrets.env",
        ]
        for path in candidates:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)
            return

    def ingest(
        self,
        raw_trace: list[dict[str, Any]],
        task_type: str,
        instruction: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        episode = self.standardizer.standardize(raw_trace, task_type, instruction, metadata)

        propositions = []
        for step in episode.steps:
            propositions.extend(self.semantic_extractor.extract(step, existing_items=propositions))

        prescriptions = []
        for segment in self.segmenter.segment(episode):
            prescription = self.procedural_extractor.extract(segment, existing_items=prescriptions)
            if prescription is not None and prescription not in prescriptions:
                prescriptions.append(prescription)

        with self.sqlite_store.transaction():
            self.sqlite_store.write_episode(episode)
            self.sqlite_store.write_propositions(propositions)
            self.sqlite_store.write_prescriptions(prescriptions)

        self.graph_store.add_episode(episode)
        self.graph_store.add_propositions(propositions)
        self.graph_store.add_prescriptions(prescriptions)

    def retrieve(self, query: str, instruction: str = "", state: str = ""):
        retrieved = self.retriever.retrieve(RetrievalInput(query=query, instruction=instruction, state=state))
        return self.reasoner.build_context(query=query, retrieved=retrieved)
