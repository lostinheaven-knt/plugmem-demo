from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plugmem.core.llm.base import LLMClient
from plugmem.core.schema import Prescription, Proposition
from plugmem.core.storage.sqlite_store import SQLiteStore
from plugmem.core.structuring.merge_decision import MergeDecision, parse_merge_decision


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
        """Deduplicate + evolve propositions.

        Policy (Phase 1): for each new proposition, ask the LLM for a structured MergeDecision
        against existing pool items. When a merge is requested, mark the earlier item inactive
        via metadata and link it to the merged proposition.
        """
        if not self.llm:
            return new_items

        deduped: list[Proposition] = []
        pool = list(existing_items)

        for item in new_items:
            merged_into_existing = False

            for existing in pool:
                decision = self._merge_decide(item.content, existing.content)
                self._log_merge_decision(
                    candidate_id=item.proposition_id,
                    existing_id=existing.proposition_id,
                    decision=decision,
                    metadata={"candidate": item.content, "existing": existing.content},
                )

                if decision.relationship == "UNRELATED":
                    continue

                # Any non-UNRELATED relationship is treated as a merge/evolution signal.
                # Create/keep the merged proposition as the surviving one.
                merged = Proposition(
                    content=decision.merged_statement,
                    concepts=list(set(existing.concepts + item.concepts)),
                    source_step_ids=list(set(existing.source_step_ids + item.source_step_ids)),
                    confidence=min(existing.confidence, item.confidence, decision.confidence),
                    metadata={
                        **(existing.metadata or {}),
                        "merge": {
                            "relationship": decision.relationship,
                            "confidence": decision.confidence,
                            "reason": decision.reason,
                            "earlier_id": existing.proposition_id,
                            "later_id": item.proposition_id,
                        },
                    },
                )

                # Mark older propositions as inactive/superseded (metadata-only, no schema migration)
                if decision.deactivate_earlier:
                    existing.metadata = {**(existing.metadata or {}), "active": False, "superseded_by": merged.proposition_id}
                if decision.deactivate_later:
                    item.metadata = {**(item.metadata or {}), "active": False, "superseded_by": merged.proposition_id}

                deduped.append(merged)
                pool.append(merged)
                merged_into_existing = True
                break

            if not merged_into_existing:
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

    def _merge_decide(self, later: str, earlier: str) -> MergeDecision:
        prompt = (
            "You are deduplicating and evolving semantic facts. "
            "Given an EARLIER fact and a LATER fact, decide their relationship and produce a merged statement.\n\n"
            f"EARLIER: {earlier}\n"
            f"LATER: {later}\n\n"
            "Return a JSON object with keys: "
            "relationship (one of UPDATE_SAME_FACT, SAME_TOPIC_MERGE_WELL, WEAK_RELATED_STITCH_RISK, UNRELATED), "
            "merged_statement (string), deactivate_earlier (bool), deactivate_later (bool), confidence (0-1), reason (string)."
        )
        # Use JSON mode if available; still parse+validate ourselves.
        schema = {
            "type": "object",
            "properties": {
                "relationship": {"type": "string"},
                "merged_statement": {"type": "string"},
                "deactivate_earlier": {"type": "boolean"},
                "deactivate_later": {"type": "boolean"},
                "confidence": {"type": "number"},
                "reason": {"type": "string"},
            },
            "required": [
                "relationship",
                "merged_statement",
                "deactivate_earlier",
                "deactivate_later",
                "confidence",
                "reason",
            ],
        }
        data = self.llm.generate_json(prompt, schema)
        if isinstance(data, dict):
            import json

            text = json.dumps(data, ensure_ascii=False)
        else:
            text = str(data)
        return parse_merge_decision(text)

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

    def _log_merge_decision(
        self,
        candidate_id: str,
        existing_id: str,
        decision: MergeDecision,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.store:
            return
        self.store.write_dedup_audit(
            item_type="proposition_merge",
            candidate_id=candidate_id,
            existing_id=existing_id,
            judge_result=decision.relationship,
            confidence=decision.confidence,
            reason=decision.reason,
            metadata=metadata,
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
