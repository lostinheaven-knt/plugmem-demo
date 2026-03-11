from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CitedItem(BaseModel):
    type: str
    id: str
    quote: str = ""


class StructuredAnswer(BaseModel):
    answer: str
    reasoning_brief: str = ""
    cited_items: list[CitedItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
