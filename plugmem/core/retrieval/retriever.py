from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from plugmem.core.schema import RetrievedMemory
from plugmem.core.storage.sqlite_store import SQLiteStore


@dataclass
class RetrievalInput:
    query: str
    instruction: str = ""
    state: str = ""


class MemoryRetriever:
    """Minimal retrieval over SQLite-backed semantic and procedural memory."""

    def __init__(
        self,
        store: SQLiteStore | None = None,
        semantic_top_k: int = 5,
        procedural_top_k: int = 3,
    ) -> None:
        self.store = store
        self.semantic_top_k = semantic_top_k
        self.procedural_top_k = procedural_top_k

    def retrieve(self, retrieval_input: RetrievalInput) -> RetrievedMemory:
        if not self.store:
            return RetrievedMemory(query=retrieval_input.query)

        query_text = " ".join(
            part for part in [retrieval_input.query, retrieval_input.instruction, retrieval_input.state] if part
        )
        query_tokens = self._tokenize(query_text)

        proposition_rows = self.store.fetch_propositions()
        prescription_rows = self.store.fetch_prescriptions()

        proposition_scores = self._score_propositions(proposition_rows, query_tokens)
        prescription_scores = self._score_prescriptions(prescription_rows, query_tokens)

        top_prop_ids = [item["proposition_id"] for item in proposition_scores[: self.semantic_top_k] if item["score"] > 0]
        top_pres_ids = [item["prescription_id"] for item in prescription_scores[: self.procedural_top_k] if item["score"] > 0]

        evidence_step_ids = self._collect_evidence(top_prop_ids, top_pres_ids)
        scores = {
            **{item["proposition_id"]: item["score"] for item in proposition_scores[: self.semantic_top_k] if item["score"] > 0},
            **{item["prescription_id"]: item["score"] for item in prescription_scores[: self.procedural_top_k] if item["score"] > 0},
        }

        return RetrievedMemory(
            query=retrieval_input.query,
            proposition_ids=top_prop_ids,
            prescription_ids=top_pres_ids,
            evidence_step_ids=evidence_step_ids,
            scores=scores,
            metadata={
                "query_tokens": sorted(query_tokens),
            },
        )

    def _score_propositions(self, proposition_rows: list[Any], query_tokens: set[str]) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for row in proposition_rows:
            content_tokens = self._tokenize(row["content"])
            concept_tokens = self._tokenize(" ".join(row["concept_names"] or []))
            overlap = len(query_tokens & content_tokens)
            concept_overlap = len(query_tokens & concept_tokens)
            score = overlap + 0.5 * concept_overlap
            scored.append(
                {
                    "proposition_id": row["proposition_id"],
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored

    def _score_prescriptions(self, prescription_rows: list[Any], query_tokens: set[str]) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for row in prescription_rows:
            workflow = row["workflow"] if isinstance(row["workflow"], list) else []
            workflow_tokens = self._tokenize(" ".join(workflow))
            intent_tokens = self._tokenize(row["intent_text"])
            overlap = len(query_tokens & workflow_tokens)
            intent_overlap = len(query_tokens & intent_tokens)
            score = overlap + 1.5 * intent_overlap
            scored.append(
                {
                    "prescription_id": row["prescription_id"],
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored

    def _collect_evidence(self, proposition_ids: list[str], prescription_ids: list[str]) -> list[str]:
        evidence = []
        for item_id in proposition_ids + prescription_ids:
            for row in self.store.fetch_source_links(item_id=item_id):
                source_step_id = row["source_step_id"]
                if source_step_id not in evidence:
                    evidence.append(source_step_id)
        return evidence

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9_-]+", text.lower()))
