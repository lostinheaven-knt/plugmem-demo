from __future__ import annotations

from plugmem.core.llm.base import LLMClient


class MergeFakeLLM(LLMClient):
    """FakeLLM that forces proposition merge decisions for testing."""

    def __init__(self, relationship: str = "UPDATE_SAME_FACT") -> None:
        self.relationship = relationship

    def generate_json(self, prompt: str, schema: dict) -> dict:
        # Detect merge_decide prompt by presence of EARLIER/LATER markers
        if "EARLIER:" in prompt and "LATER:" in prompt and "merged_statement" in str(schema):
            return {
                "relationship": self.relationship,
                "merged_statement": "Merged fact: user likes wireless mice",
                "deactivate_earlier": True,
                "deactivate_later": True,
                "confidence": 0.9,
                "reason": "They describe the same preference; keep the merged statement.",
            }
        # Fallback for other schema calls used in tests
        # Return minimally valid structures based on required keys
        required = schema.get("required", [])
        out = {}
        for k in required:
            if k in {"decision"}:
                out[k] = "different"
            elif k in {"confidence"}:
                out[k] = 0.5
            elif k in {"reason"}:
                out[k] = ""
            elif k == "propositions":
                out[k] = []
            else:
                out[k] = None
        return out

    def generate_text(self, prompt: str) -> str:
        return ""
