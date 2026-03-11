from __future__ import annotations

import json
from typing import Any

from plugmem.core.llm.base import LLMClient
from plugmem.core.llm.json_utils import extract_json_object
from plugmem.core.llm.structured_validation import StructuredOutputError, ValidationRule, validate_object
from plugmem.core.schema.answer import StructuredAnswer


_ALLOWED_TYPES = {"proposition", "prescription", "episode_step"}


def answer_with_citations(llm: LLMClient | None, query: str, memory_block: str) -> StructuredAnswer:
    """Produce a structured answer with citations.

    memory_block is expected to contain facts/procedures/evidence with ids embedded.
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
    if isinstance(data, dict):
        text = json.dumps(data, ensure_ascii=False)
    else:
        text = str(data)

    obj = extract_json_object(text)
    validate_object(
        obj,
        required=[
            ValidationRule("answer", (str,)),
            ValidationRule("reasoning_brief", (str,)),
            ValidationRule("cited_items", (list,)),
        ],
    )

    # Validate cited items
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
