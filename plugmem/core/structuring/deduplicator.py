from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plugmem.core.llm.base import LLMClient
from plugmem.core.schema import Prescription, Proposition
from plugmem.core.storage.sqlite_store import SQLiteStore


@dataclass
class DedupDecision:
    decision: str
    confidence: float
    reason: str


class LLMDeduplicator:
    """LLM-based semantic deduplication for propositions and prescriptions."""

    def __init__(self, llm: LLMClient | None = None, store: SQLiteStore | None = None) -> None:
        self.llm = llm
        self.store = store

    def deduplicate_propositions(
        self,
        new_items: list[Proposition],
        existing_items: list[Proposition],
    ) -> list[Proposition]:
        if not self.llm:
            return new_items

        deduped: list[Proposition] = []
        pool = list(existing_items)
        for item in new_items:
            matched = False
            for existing in pool:
                decision = self._judge_duplicate(item.content, existing.content, item_type="proposition")
                self._log_decision(
                    item_type="proposition",
                    candidate_id=item.proposition_id,
                    existing_id=existing.proposition_id,
                    decision=decision,
                    metadata={"candidate": item.content, "existing": existing.content},
                )
                if decision.decision == "duplicate":
                    existing.source_step_ids = list(set(existing.source_step_ids + item.source_step_ids))
                    matched = True
                    break
            if not matched:
                deduped.append(item)
                pool.append(item)
        return deduped

    def deduplicate_prescription(
        self,
        new_item: Prescription,
        existing_items: list[Prescription],
    ) -> Prescription:
        if not self.llm:
            return new_item

        for existing in existing_items:
            left = f"Intent: {new_item.intent}\nWorkflow: {new_item.workflow}"
            right = f"Intent: {existing.intent}\nWorkflow: {existing.workflow}"
            decision = self._judge_duplicate(left, right, item_type="prescription")
            self._log_decision(
                item_type="prescription",
                candidate_id=new_item.prescription_id,
                existing_id=existing.prescription_id,
                decision=decision,
                metadata={"candidate": left, "existing": right},
            )
            if decision.decision == "duplicate":
                existing.source_step_ids = list(set(existing.source_step_ids + new_item.source_step_ids))
                return existing
        return new_item

    def _judge_duplicate(self, left: str, right: str, item_type: str) -> DedupDecision:
        prompt = (
            f"Determine whether the following two {item_type}s are duplicates.\n"
            f"A: {left}\n"
            f"B: {right}\n"
            "Return one of: duplicate, related_but_distinct, different."
        )
        schema = {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": ["decision", "confidence", "reason"],
        }
        data = self.llm.generate_json(prompt, schema)
        return DedupDecision(
            decision=data["decision"],
            confidence=float(data["confidence"]),
            reason=data["reason"],
        )

    def _log_decision(
        self,
        item_type: str,
        candidate_id: str,
        existing_id: str,
        decision: DedupDecision,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.store:
            return
        self.store.write_dedup_audit(
            item_type=item_type,
            candidate_id=candidate_id,
            existing_id=existing_id,
            judge_result=decision.decision,
            confidence=decision.confidence,
            reason=decision.reason,
            metadata=metadata,
        )
