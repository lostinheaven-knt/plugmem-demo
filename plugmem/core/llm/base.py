from __future__ import annotations

from typing import Any, Protocol


class LLMClient(Protocol):
    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        ...

    def generate_text(self, prompt: str) -> str:
        ...
