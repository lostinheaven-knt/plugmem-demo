from __future__ import annotations

from plugmem.core.structuring.workflow_dsl import WorkflowDSL


def workflow_dsl_to_mermaid_flowchart(dsl: WorkflowDSL) -> str:
    """Render a WorkflowDSL as Mermaid flowchart TD.

    This is for presentation only (docs/UI). DSL remains the source of truth.
    """
    # Basic escaping for quotes/newlines
    def esc(s: str) -> str:
        return s.replace("\n", " ").replace('"', "\\\"").strip()

    lines: list[str] = ["flowchart TD"]

    # Title / intent node
    lines.append(f"  I[\"Intent: {esc(dsl.intent)}\"]")

    prev = "I"
    for idx, step in enumerate(dsl.steps, start=1):
        label_parts = [f"{step.op}: {step.target}"]
        if step.value:
            label_parts.append(f"value={step.value}")
        if step.note:
            label_parts.append(f"note={step.note}")
        label = esc(" | ".join(label_parts))
        node_id = f"S{idx}"
        lines.append(f"  {node_id}[\"{label}\"]")
        lines.append(f"  {prev} --> {node_id}")
        prev = node_id

    # Preconditions / postconditions as side notes
    if dsl.preconditions:
        lines.append(f"  P[\"Pre: {esc('; '.join(dsl.preconditions))}\"]")
        lines.append("  P -.-> I")
    if dsl.postconditions:
        lines.append(f"  O[\"Post: {esc('; '.join(dsl.postconditions))}\"]")
        lines.append(f"  {prev} --> O")

    return "\n".join(lines) + "\n"
