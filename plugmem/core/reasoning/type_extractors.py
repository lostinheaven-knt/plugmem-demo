from __future__ import annotations

import json
from typing import Any

from plugmem.core.llm.base import LLMClient
from plugmem.core.llm.json_utils import extract_json_object
from plugmem.core.llm.structured_validation import StructuredOutputError, ValidationRule, validate_object


def extract_key_items(
    llm: LLMClient | None,
    query: str,
    semantic_items: list[dict[str, Any]],
    procedural_items: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Per-type extraction pass to select/condense relevant info.

    Inputs are lists of items with ids included.
    Output is JSON with three lists containing text + citations.
    """
    if not llm:
        return {"semantic": [], "procedural": [], "evidence": []}

    def _fmt(items: list[dict[str, Any]], kind: str) -> str:
        lines: list[str] = []
        for it in items[:30]:
            lines.append(f"- [{kind}:{it['id']}] {it.get('text','')}")
        return "\n".join(lines)

    prompt = (
        "You are selecting and condensing useful information to answer a user query. "
        "Return JSON ONLY with keys semantic, procedural, evidence.\n\n"
        "Each list must contain objects: {id: string, type: proposition|prescription|episode_step, text: string}.\n"
        "Only include items that are helpful; keep text short and quote original phrasing when possible.\n\n"
        f"Query: {query}\n\n"
        "Semantic candidates:\n"
        + _fmt(semantic_items, "proposition")
        + "\n\nProcedural candidates:\n"
        + _fmt(procedural_items, "prescription")
        + "\n\nEvidence candidates:\n"
        + _fmt(evidence_items, "episode_step")
    )

    schema = {
        "type": "object",
        "properties": {
            "semantic": {"type": "array"},
            "procedural": {"type": "array"},
            "evidence": {"type": "array"},
        },
        "required": ["semantic", "procedural", "evidence"],
    }
    data = llm.generate_json(prompt, schema)
    text = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
    obj = extract_json_object(text)
    validate_object(
        obj,
        required=[
            ValidationRule("semantic", (list,)),
            ValidationRule("procedural", (list,)),
            ValidationRule("evidence", (list,)),
        ],
    )

    def _validate_list(lst: list[Any], allowed_type: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i, it in enumerate(lst):
            if not isinstance(it, dict):
                raise StructuredOutputError(f"items[{i}] must be object")
            validate_object(
                it,
                required=[
                    ValidationRule("id", (str,), non_empty=True),
                    ValidationRule("type", (str,), allowed={allowed_type}),
                    ValidationRule("text", (str,)),
                ],
            )
            out.append({"id": it["id"], "type": it["type"], "text": it["text"]})
        return out

    return {
        "semantic": _validate_list(obj["semantic"], "proposition"),
        "procedural": _validate_list(obj["procedural"], "prescription"),
        "evidence": _validate_list(obj["evidence"], "episode_step"),
    }
