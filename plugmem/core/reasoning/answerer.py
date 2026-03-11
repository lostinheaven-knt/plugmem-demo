from __future__ import annotations

import json
from typing import Any

from plugmem.core.llm.base import LLMClient
from plugmem.core.llm.json_utils import extract_json_object
from plugmem.core.llm.structured_validation import StructuredOutputError, ValidationRule, validate_object
from plugmem.core.schema.answer import StructuredAnswer


_ALLOWED_TYPES = {"proposition", "prescription", "episode_step"}


def answer_with_citations(llm: LLMClient | None, query: str, memory_block: str) -> StructuredAnswer:
    """Produce a structured answer with citations from a prebuilt memory block.

    This is kept for backward compatibility; prefer answer_with_citations_from_items.
    """
    if not llm:
        return StructuredAnswer(answer="", reasoning_brief="", cited_items=[], metadata={"error": "no_llm"})

    prompt = (
        "You are answering the user query using the provided memory. "
        "Return JSON ONLY with keys: answer, reasoning_brief, cited_items.\n\n"
        "cited_items must be a list of objects: {type: proposition|prescription|episode_step, id: string, quote: string}.\n\n"
        f"Query: {query}\n\n"
        f"Memory:\n{memory_block}\n"
    )

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "reasoning_brief": {"type": "string"},
            "cited_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "id": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["type", "id", "quote"],
                },
            },
        },
        "required": ["answer", "reasoning_brief", "cited_items"],
    }

    data = llm.generate_json(prompt, schema)
    text = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
    return _parse_structured_answer(text)


def answer_with_citations_from_items(
    llm: LLMClient | None,
    query: str,
    semantic: list[dict[str, Any]],
    procedural: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> StructuredAnswer:
    """Phase 3 (type-aware): answer using per-type extracted items.

    Each input list should contain objects with keys: id, type, text.
    """
    if not llm:
        return StructuredAnswer(answer="", reasoning_brief="", cited_items=[], metadata={"error": "no_llm"})

    def fmt(items: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for it in items[:30]:
            lines.append(f"- [{it['type']}:{it['id']}] {it.get('text','')}")
        return "\n".join(lines)

    prompt = (
        "You are answering a user query using memory items of different types.\n"
        "Return JSON ONLY with keys: answer, reasoning_brief, cited_items.\n\n"
        "Rules:\n"
        "- cited_items must cite ONLY ids that appear in the provided lists.\n"
        "- Prefer citing semantic facts for claims, procedures for how-to, and evidence for grounding.\n\n"
        f"Query: {query}\n\n"
        f"Semantic facts:\n{fmt(semantic) or '- None'}\n\n"
        f"Procedures:\n{fmt(procedural) or '- None'}\n\n"
        f"Evidence:\n{fmt(evidence) or '- None'}\n"
    )

    schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "reasoning_brief": {"type": "string"},
            "cited_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "id": {"type": "string"},
                        "quote": {"type": "string"},
                    },
                    "required": ["type", "id", "quote"],
                },
            },
        },
        "required": ["answer", "reasoning_brief", "cited_items"],
    }

    data = llm.generate_json(prompt, schema)
    text = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
    return _parse_structured_answer(text)


def _parse_structured_answer(text: str) -> StructuredAnswer:
    obj = extract_json_object(text)
    validate_object(
        obj,
        required=[
            ValidationRule("answer", (str,)),
            ValidationRule("reasoning_brief", (str,)),
            ValidationRule("cited_items", (list,)),
        ],
    )

    cited: list[dict[str, Any]] = []
    for i, ci in enumerate(obj["cited_items"]):
        if not isinstance(ci, dict):
            raise StructuredOutputError(f"cited_items[{i}] must be object")
        validate_object(
            ci,
            required=[
                ValidationRule("type", (str,), allowed=_ALLOWED_TYPES),
                ValidationRule("id", (str,), non_empty=True),
                ValidationRule("quote", (str,)),
            ],
        )
        cited.append(ci)

    return StructuredAnswer(
        answer=obj["answer"].strip(),
        reasoning_brief=obj["reasoning_brief"].strip(),
        cited_items=cited,  # pydantic will coerce
        metadata={},
    )
