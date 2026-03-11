from __future__ import annotations

from typing import Any

from plugmem.core.schema import Episode, EpisodeStep
from plugmem.core.llm.base import LLMClient


class EpisodicStandardizer:
    """Convert raw traces into standardized Episode objects."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm

    def standardize(
        self,
        raw_trace: list[dict[str, Any]],
        task_type: str,
        instruction: str,
        metadata: dict[str, Any] | None = None,
    ) -> Episode:
        steps: list[EpisodeStep] = []
        episode = Episode(
            task_type=task_type,
            instruction=instruction,
            metadata=metadata or {},
        )

        for t, item in enumerate(raw_trace, start=1):
            observation = str(item.get("observation") or item.get("obs") or item.get("content") or "")
            action = str(item.get("action") or item.get("role") or "observe")

            state, subgoal, reward = self._infer_step_fields(
                instruction=instruction,
                item=item,
                previous_step=steps[-1] if steps else None,
            )

            steps.append(
                EpisodeStep(
                    episode_id=episode.episode_id,
                    t=t,
                    observation=observation,
                    state=state,
                    action=action,
                    reward=reward,
                    subgoal=subgoal,
                    metadata=item,
                )
            )

        episode.steps = steps
        return episode

    def _infer_step_fields(
        self,
        instruction: str,
        item: dict[str, Any],
        previous_step: EpisodeStep | None,
    ) -> tuple[str, str, float | None]:
        if not self.llm:
            return "", "", None

        prompt = (
            "Infer state, subgoal, and reward for the current episode step.\n"
            f"Instruction: {instruction}\n"
            f"Previous state: {previous_step.state if previous_step else ''}\n"
            f"Current item: {item}\n"
        )
        schema = {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "subgoal": {"type": "string"},
                "reward": {"type": ["number", "null"]},
            },
            "required": ["state", "subgoal", "reward"],
        }
        data = self.llm.generate_json(prompt, schema)
        return data.get("state", ""), data.get("subgoal", ""), data.get("reward")
