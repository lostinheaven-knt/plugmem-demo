from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from plugmem.core.llm.json_utils import extract_json_object
from plugmem.core.llm.structured_validation import StructuredOutputError, ValidationRule, coerce_bool, validate_object


MergeRelationship = Literal[
    "UPDATE_SAME_FACT",
    "SAME_TOPIC_MERGE_WELL",
    "WEAK_RELATED_STITCH_RISK",
    "UNRELATED",
]


@dataclass(frozen=True)
class MergeDecision:
    relationship: MergeRelationship
    merged_statement: str
    deactivate_earlier: bool
    deactivate_later: bool
    confidence: float
    reason: str


_ALLOWED_REL: set[str] = {
    "UPDATE_SAME_FACT",
    "SAME_TOPIC_MERGE_WELL",
    "WEAK_RELATED_STITCH_RISK",
    "UNRELATED",
}


def parse_merge_decision(text: str) -> MergeDecision:
    """Parse and validate a MergeDecision from model output."""
    obj = extract_json_object(text)
    validate_object(
        obj,
        required=[
            ValidationRule("relationship", (str,), allowed=_ALLOWED_REL),
            ValidationRule("merged_statement", (str,), non_empty=True),
            ValidationRule("deactivate_earlier", (bool, str)),
            ValidationRule("deactivate_later", (bool, str)),
            ValidationRule("confidence", (int, float)),
            ValidationRule("reason", (str,)),
        ],
    )

    deactivate_earlier = coerce_bool(obj["deactivate_earlier"])
    deactivate_later = coerce_bool(obj["deactivate_later"])

    conf = float(obj["confidence"])
    if not (0.0 <= conf <= 1.0):
        raise StructuredOutputError(f"confidence out of range: {conf}")

    return MergeDecision(
        relationship=obj["relationship"],
        merged_statement=str(obj["merged_statement"]).strip(),
        deactivate_earlier=deactivate_earlier,
        deactivate_later=deactivate_later,
        confidence=conf,
        reason=str(obj.get("reason") or "").strip(),
    )
