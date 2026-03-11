from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Proposition(BaseModel):
    proposition_id: str = Field(default_factory=lambda: f"prop_{uuid4().hex}")
    content: str
    concepts: list[str] = Field(default_factory=list)
    source_step_ids: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class Concept(BaseModel):
    concept_id: str = Field(default_factory=lambda: f"concept_{uuid4().hex}")
    name: str
    aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
