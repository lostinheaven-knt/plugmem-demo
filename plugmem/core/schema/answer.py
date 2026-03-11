from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ActionOp = Literal[
    "navigate",
    "click",
    "type",
    "wait",
    "verify",
    "ask_user",
]


class CitedItem(BaseModel):
    type: str
    id: str
    quote: str = ""


class SuggestedAction(BaseModel):
    """A lightweight, agent-friendly next action suggestion."""

    op: ActionOp
    target: str = ""
    value: str = ""
    note: str = ""


class StructuredAnswer(BaseModel):
    answer: str
    reasoning_brief: str = ""
    cited_items: list[CitedItem] = Field(default_factory=list)

    # Agent-friendly: optional next actions derived from memory
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)
