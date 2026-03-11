from __future__ import annotations

from plugmem.core.llm.base import LLMClient
from plugmem.core.schema import EpisodeStep, Prescription
from plugmem.core.structuring.deduplicator import LLMDeduplicator


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
            "Extract an environment-agnostic intent and workflow from the trajectory segment.\n"
            f"Segment:\n{segment_text}\n"
        )
        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "workflow": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["intent", "workflow"],
        }
        data = self.llm.generate_json(prompt, schema)
        return Prescription(
            intent=data["intent"],
            workflow=data.get("workflow", []),
            source_step_ids=[step.step_id for step in segment_steps],
        )
