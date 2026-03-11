from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EpisodeStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"step_{uuid4().hex}")
    episode_id: str
    t: int

    observation: str
    state: str = ""
    action: str
    reward: float | None = None
    subgoal: str = ""

    metadata: dict[str, Any] = Field(default_factory=dict)


class Episode(BaseModel):
    episode_id: str = Field(default_factory=lambda: f"episode_{uuid4().hex}")
    task_id: str = ""
    task_type: str
    instruction: str
    steps: list[EpisodeStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
