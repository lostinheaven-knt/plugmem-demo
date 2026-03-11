from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from plugmem.core.llm.json_utils import extract_json_object


class DeepSeekLLM:
    """Real LLM client backed by DeepSeek's OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
        self.temperature = temperature
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY.")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise information extraction engine. Return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Follow this JSON schema exactly:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
                        f"Task:\n{prompt}"
                    ),
                },
            ],
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("DeepSeek returned empty JSON response.")

        try:
            return extract_json_object(text)
        except ValueError as e:
            truncated = text[:800]
            raise ValueError(f"DeepSeek returned non-JSON or invalid JSON. raw=<{truncated}> error={e}") from e

    def generate_text(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
