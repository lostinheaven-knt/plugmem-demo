from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RetrievedMemory(BaseModel):
    query: str
    proposition_ids: list[str] = Field(default_factory=list)
    prescription_ids: list[str] = Field(default_factory=list)
    evidence_step_ids: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryContext(BaseModel):
    semantic_summary: str = ""
    procedural_summary: str = ""
    evidence_summary: str = ""
    final_prompt_block: str = ""
