from __future__ import annotations

from plugmem.core.llm.base import LLMClient
from plugmem.core.schema import EpisodeStep, Proposition
from plugmem.core.structuring.deduplicator import LLMDeduplicator


class SemanticExtractor:
    """Extract propositions from a standardized episode step."""

    def __init__(self, llm: LLMClient | None = None, deduplicator: LLMDeduplicator | None = None) -> None:
        self.llm = llm
        self.deduplicator = deduplicator

    def extract(self, step: EpisodeStep, existing_items: list[Proposition] | None = None) -> list[Proposition]:
        propositions = self._extract_raw(step)
        if not self.deduplicator:
            return propositions
        return self.deduplicator.deduplicate_propositions(propositions, existing_items or [])

    def _extract_raw(self, step: EpisodeStep) -> list[Proposition]:
        if not self.llm:
            return []

        prompt = (
            "Extract 1-3 atomic propositions and concepts from the standardized episode step.\n"
            f"Observation: {step.observation}\n"
            f"State: {step.state}\n"
            f"Action: {step.action}\n"
            f"Subgoal: {step.subgoal}\n"
        )
        schema = {
            "type": "object",
            "properties": {
                "propositions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "concepts": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["content", "concepts"],
                    },
                }
            },
            "required": ["propositions"],
        }
        data = self.llm.generate_json(prompt, schema)
        return [
            Proposition(
                content=item["content"],
                concepts=item.get("concepts", []),
                source_step_ids=[step.step_id],
            )
            for item in data.get("propositions", [])
        ]
