from __future__ import annotations

import json

from plugmem.core.llm.base import LLMClient
from plugmem.core.schema import EpisodeStep, Prescription
from plugmem.core.structuring.deduplicator import LLMDeduplicator
from plugmem.core.structuring.mermaid import workflow_dsl_to_mermaid_flowchart
from plugmem.core.structuring.workflow_dsl import parse_workflow_dsl, workflow_dsl_to_json


class ProceduralExtractor:
    """Extract reusable prescriptions from segmented trajectories."""

    def __init__(self, llm: LLMClient | None = None, deduplicator: LLMDeduplicator | None = None) -> None:
        self.llm = llm
        self.deduplicator = deduplicator

    def extract(
        self,
        segment_steps: list[EpisodeStep],
        existing_items: list[Prescription] | None = None,
    ) -> Prescription | None:
        prescription = self._extract_raw(segment_steps)
        if prescription is None or not self.deduplicator:
            return prescription
        return self.deduplicator.deduplicate_prescription(prescription, existing_items or [])

    def _extract_raw(self, segment_steps: list[EpisodeStep]) -> Prescription | None:
        if not self.llm or not segment_steps:
            return None

        segment_text = "\n".join(
            f"Step {step.t}: obs={step.observation}; action={step.action}; subgoal={step.subgoal}; reward={step.reward}"
            for step in segment_steps
        )
        prompt = (
            "Extract an environment-agnostic intent and a *strict JSON workflow DSL* from the trajectory segment.\n"
            "Return JSON ONLY with this schema:\n"
            "{\n"
            "  \"intent\": <string>,\n"
            "  \"steps\": [ {\"op\": <navigate|click|type|wait|verify>, \"target\": <string>, \"value\": <string optional>, \"note\": <string optional>} ... ],\n"
            "  \"preconditions\": [<string>...],\n"
            "  \"postconditions\": [<string>...]\n"
            "}\n\n"
            f"Segment:\n{segment_text}\n"
        )
        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "op": {"type": "string"},
                            "target": {"type": "string"},
                            "value": {"type": "string"},
                            "note": {"type": "string"},
                        },
                        "required": ["op", "target"],
                    },
                },
                "preconditions": {"type": "array", "items": {"type": "string"}},
                "postconditions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["intent", "steps", "preconditions", "postconditions"],
        }

        data = self.llm.generate_json(prompt, schema)
        # Validate/normalize with our parser (best-effort) to enforce ops/fields.
        dsl = parse_workflow_dsl(json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data))
        workflow_json = workflow_dsl_to_json(dsl)
        workflow_mermaid = workflow_dsl_to_mermaid_flowchart(dsl)

        return Prescription(
            intent=dsl.intent,
            # Backward compatibility: keep workflow as list[str]. Put serialized DSL in it.
            workflow=[json.dumps(workflow_json, ensure_ascii=False)],
            source_step_ids=[step.step_id for step in segment_steps],
            metadata={"workflow_dsl": workflow_json, "workflow_mermaid": workflow_mermaid},
        )
