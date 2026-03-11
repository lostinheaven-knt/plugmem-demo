from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from plugmem.core.graph.graph_store import MemoryGraphStore
from plugmem.core.llm.deepseek import DeepSeekLLM
from plugmem.core.reasoning.action_alignment import actions_align_to_workflow_dsl
from plugmem.core.reasoning.answerer import answer_with_citations, answer_with_citations_from_items
from plugmem.core.reasoning.memory_reasoner import MemoryReasoner
from plugmem.core.reasoning.type_extractors import extract_key_items
from plugmem.core.retrieval.retriever import MemoryRetriever, RetrievalInput
from plugmem.core.schema import StructuredAnswer
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
        """Backward-compatible retrieve: returns a MemoryContext."""
        retrieved = self.retriever.retrieve(RetrievalInput(query=query, instruction=instruction, state=state))
        return self.reasoner.build_context(query=query, retrieved=retrieved)

    def retrieve_structured(self, query: str, instruction: str = "", state: str = "") -> StructuredAnswer:
        """Return a structured answer with citations and agent-friendly suggested actions."""
        retrieved = self.retriever.retrieve(RetrievalInput(query=query, instruction=instruction, state=state))
        ctx = self.reasoner.build_context(query=query, retrieved=retrieved)
        llm = getattr(self.standardizer, "llm", None)

        semantic_candidates = [{"id": pid, "type": "proposition", "text": ""} for pid in retrieved.proposition_ids]
        procedural_candidates = [{"id": rid, "type": "prescription", "text": ""} for rid in retrieved.prescription_ids]
        evidence_candidates = [{"id": sid, "type": "episode_step", "text": ""} for sid in retrieved.evidence_step_ids]

        primary_workflow_dsl: dict[str, Any] | None = None

        if self.sqlite_store:
            props = {r["proposition_id"]: r for r in self.sqlite_store.fetch_propositions()}
            pres = {r["prescription_id"]: r for r in self.sqlite_store.fetch_prescriptions()}
            steps = {r["step_id"]: r for r in self.sqlite_store.fetch_episode_steps(retrieved.evidence_step_ids)}

            for it in semantic_candidates:
                row = props.get(it["id"])
                if row:
                    it["text"] = row["content"]

            for idx, it in enumerate(procedural_candidates):
                row = pres.get(it["id"])
                if row:
                    meta = row.get("metadata") or {}
                    dsl = meta.get("workflow_dsl") if isinstance(meta, dict) else None
                    it["text"] = f"Intent: {row['intent_text']}" + (f" | DSL: {dsl}" if dsl else "")
                    if idx == 0 and isinstance(dsl, dict):
                        primary_workflow_dsl = dsl

            for it in evidence_candidates:
                row = steps.get(it["id"])
                if row:
                    it["text"] = f"Step {row['t']}: obs={row['observation']} action={row['action']} subgoal={row['subgoal']}"

        extracted = extract_key_items(
            llm=llm,
            query=query,
            semantic_items=semantic_candidates,
            procedural_items=procedural_candidates,
            evidence_items=evidence_candidates,
        )

        try:
            ans = answer_with_citations_from_items(
                llm=llm,
                query=query,
                semantic=extracted["semantic"],
                procedural=extracted["procedural"],
                evidence=extracted["evidence"],
            )
        except Exception:
            ans = answer_with_citations(llm=llm, query=query, memory_block=ctx.final_prompt_block)

        # Enforce citations resolve to existing ids.
        allowed_prop = set(retrieved.proposition_ids)
        allowed_pres = set(retrieved.prescription_ids)
        allowed_step = set(retrieved.evidence_step_ids)

        filtered = []
        for ci in ans.cited_items:
            if ci.type == "proposition" and ci.id in allowed_prop:
                filtered.append(ci)
            elif ci.type == "prescription" and ci.id in allowed_pres:
                filtered.append(ci)
            elif ci.type == "episode_step" and ci.id in allowed_step:
                filtered.append(ci)

        ans.cited_items = filtered
        ans.metadata["citations_filtered"] = True
        ans.metadata["candidate_counts"] = {
            "propositions": len(allowed_prop),
            "prescriptions": len(allowed_pres),
            "episode_steps": len(allowed_step),
        }

        # Align suggested actions to procedural DSL (best-effort) and keep as Pydantic objects.
        try:
            from plugmem.core.schema.answer import SuggestedAction

            aligned_dicts = actions_align_to_workflow_dsl(
                [a.model_dump() for a in ans.suggested_actions],
                workflow_dsl=primary_workflow_dsl,
            )
            ans.suggested_actions = [SuggestedAction(**d) for d in aligned_dicts]
            ans.metadata["actions_aligned_to_dsl"] = primary_workflow_dsl is not None
        except Exception:
            ans.metadata["actions_aligned_to_dsl"] = False

        return ans
