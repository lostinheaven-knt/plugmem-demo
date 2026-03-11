from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Prescription(BaseModel):
    prescription_id: str = Field(default_factory=lambda: f"pres_{uuid4().hex}")
    intent: str
    workflow: list[str] = Field(default_factory=list)
    source_step_ids: list[str] = Field(default_factory=list)
    success_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Intent(BaseModel):
    intent_id: str = Field(default_factory=lambda: f"intent_{uuid4().hex}")
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
