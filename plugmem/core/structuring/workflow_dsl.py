from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from plugmem.core.llm.json_utils import extract_json_object
from plugmem.core.llm.structured_validation import StructuredOutputError, ValidationRule, validate_object


WorkflowOp = Literal["navigate", "click", "type", "wait", "verify"]


@dataclass(frozen=True)
class WorkflowStep:
    op: WorkflowOp
    target: str
    value: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class WorkflowDSL:
    intent: str
    steps: list[WorkflowStep]
    preconditions: list[str]
    postconditions: list[str]


_ALLOWED_OPS: set[str] = {"navigate", "click", "type", "wait", "verify"}


def parse_workflow_dsl(text: str) -> WorkflowDSL:
    obj = extract_json_object(text)
    validate_object(
        obj,
        required=[
            ValidationRule("intent", (str,), non_empty=True),
            ValidationRule("steps", (list,)),
            ValidationRule("preconditions", (list,)),
            ValidationRule("postconditions", (list,)),
        ],
    )

    steps: list[WorkflowStep] = []
    for i, step in enumerate(obj["steps"]):
        if not isinstance(step, dict):
            raise StructuredOutputError(f"steps[{i}] must be an object")
        validate_object(
            step,
            required=[
                ValidationRule("op", (str,), allowed=_ALLOWED_OPS),
                ValidationRule("target", (str,), non_empty=True),
            ],
        )
        op = step["op"]
        target = step["target"].strip()
        value = step.get("value")
        note = step.get("note")
        if value is not None and not isinstance(value, str):
            raise StructuredOutputError(f"steps[{i}].value must be string|null")
        if note is not None and not isinstance(note, str):
            raise StructuredOutputError(f"steps[{i}].note must be string|null")
        steps.append(WorkflowStep(op=op, target=target, value=value, note=note))

    return WorkflowDSL(
        intent=obj["intent"].strip(),
        steps=steps,
        preconditions=[str(x).strip() for x in obj.get("preconditions", [])],
        postconditions=[str(x).strip() for x in obj.get("postconditions", [])],
    )


def workflow_dsl_to_json(dsl: WorkflowDSL) -> dict[str, Any]:
    return {
        "intent": dsl.intent,
        "steps": [
            {k: v for k, v in {"op": s.op, "target": s.target, "value": s.value, "note": s.note}.items() if v is not None}
            for s in dsl.steps
        ],
        "preconditions": dsl.preconditions,
        "postconditions": dsl.postconditions,
    }
