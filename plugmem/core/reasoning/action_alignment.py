from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plugmem.core.llm.structured_validation import StructuredOutputError


def actions_align_to_workflow_dsl(
    suggested_actions: list[dict[str, Any]],
    workflow_dsl: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Best-effort align suggested actions to a stored WorkflowDSL.

    - Keeps op/target/value/note fields
    - Adds `source_prescription_step` (index) when target/op matches a DSL step

    This is a lightweight heuristic for agent traceability.
    """
    if not workflow_dsl or not isinstance(workflow_dsl, dict):
        return suggested_actions

    steps = workflow_dsl.get("steps")
    if not isinstance(steps, list):
        return suggested_actions

    def norm(s: str) -> str:
        return (s or "").strip().lower()

    aligned: list[dict[str, Any]] = []
    for act in suggested_actions:
        if not isinstance(act, dict):
            raise StructuredOutputError("suggested_actions item must be object")
        op = norm(str(act.get("op", "")))
        target = norm(str(act.get("target", "")))

        best_idx: int | None = None
        for i, st in enumerate(steps):
            if not isinstance(st, dict):
                continue
            if norm(str(st.get("op", ""))) == op and norm(str(st.get("target", ""))) == target:
                best_idx = i
                break

        out = dict(act)
        if best_idx is not None:
            out["source_prescription_step"] = best_idx
        aligned.append(out)

    return aligned
