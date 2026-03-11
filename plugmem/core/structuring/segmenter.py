from __future__ import annotations

from collections.abc import Sequence

from plugmem.core.schema import Episode, EpisodeStep


class Segmenter:
    """Split an episode into subgoal-coherent segments."""

    def __init__(self, similarity_threshold: float = 0.76) -> None:
        self.similarity_threshold = similarity_threshold

    def segment(self, episode: Episode) -> list[list[EpisodeStep]]:
        if not episode.steps:
            return []

        segments: list[list[EpisodeStep]] = [[episode.steps[0]]]
        for step in episode.steps[1:]:
            if self._is_same_segment(segments[-1][-1], step):
                segments[-1].append(step)
            else:
                segments.append([step])
        return segments

    def _is_same_segment(self, left: EpisodeStep, right: EpisodeStep) -> bool:
        left_tokens = set(self._normalize(left.subgoal))
        right_tokens = set(self._normalize(right.subgoal))
        if not left_tokens and not right_tokens:
            return True
        union = left_tokens | right_tokens
        if not union:
            return True
        similarity = len(left_tokens & right_tokens) / len(union)
        return similarity >= self.similarity_threshold

    @staticmethod
    def _normalize(text: str) -> Sequence[str]:
        return [token.strip().lower() for token in text.split() if token.strip()]
