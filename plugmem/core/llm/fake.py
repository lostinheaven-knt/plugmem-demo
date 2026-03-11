from __future__ import annotations

from typing import Any


class FakeLLM:
    """Deterministic fake LLM for local MVP demos."""

    def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if "Infer state, subgoal, and reward" in prompt:
            return {
                "state": "The agent is processing the current interaction step.",
                "subgoal": self._infer_subgoal(prompt),
                "reward": 1.0,
            }

        if "Extract 1-3 atomic propositions and concepts" in prompt:
            return {
                "propositions": [
                    {
                        "content": self._infer_proposition(prompt),
                        "concepts": self._infer_concepts(prompt),
                    }
                ]
            }

        # Phase 2: workflow DSL
        if "strict JSON workflow DSL" in prompt and "steps" in str(schema):
            return {
                "intent": self._infer_intent(prompt),
                "steps": [
                    {"op": "navigate", "target": "search page"},
                    {"op": "type", "target": "search box", "value": "wireless mouse"},
                    {"op": "click", "target": "search button"},
                    {"op": "verify", "target": "results list", "note": "results are shown"},
                ],
                "preconditions": ["User is on the relevant site"],
                "postconditions": ["Search results are visible"],
            }

        if "Extract an environment-agnostic intent and workflow" in prompt:
            return {
                "intent": self._infer_intent(prompt),
                "workflow": [
                    "Inspect the current context to identify the immediate objective",
                    "Take an action that advances the identified objective",
                    "Verify the outcome and continue if progress is made",
                ],
            }

        # Phase 1: merge/evolve semantic facts
        if "deduplicating and evolving semantic facts" in prompt and "merged_statement" in str(schema):
            lower = prompt.lower()
            if "wireless mouse" in lower:
                relationship = "UPDATE_SAME_FACT"
                merged_statement = "The target item is a wireless mouse."
            else:
                relationship = "UNRELATED"
                merged_statement = ""

            return {
                "relationship": relationship,
                "merged_statement": merged_statement or self._infer_proposition(prompt),
                "deactivate_earlier": relationship != "UNRELATED",
                "deactivate_later": relationship != "UNRELATED",
                "confidence": 0.9,
                "reason": "Deterministic fake merge decision.",
            }

        if "Determine whether the following two" in prompt:
            return {
                "decision": self._infer_duplicate_decision(prompt),
                "confidence": 0.9,
                "reason": "Deterministic fake judge based on surface overlap.",
            }

        raise ValueError(f"Unsupported fake prompt: {prompt[:120]}")

    def generate_text(self, prompt: str) -> str:
        return ""

    def _infer_subgoal(self, prompt: str) -> str:
        lower = prompt.lower()
        if "price" in lower or "cheapest" in lower:
            return "find the cheapest relevant product"
        if "search" in lower:
            return "search for relevant information"
        if "reply" in lower or "assistant" in lower:
            return "respond to the user request"
        return "make progress on the current task"

    def _infer_proposition(self, prompt: str) -> str:
        lower = prompt.lower()
        if "low sugar" in lower:
            return "The user prefers low-sugar options."
        if "sort" in lower and "price" in lower:
            return "Sorting by price helps identify cheaper candidates."
        if "wireless mouse" in lower:
            return "The target item is a wireless mouse."
        return "This step contains task-relevant information for future decisions."

    def _infer_concepts(self, prompt: str) -> list[str]:
        lower = prompt.lower()
        concepts: list[str] = []
        if "price" in lower:
            concepts.append("price")
        if "wireless mouse" in lower:
            concepts.append("wireless mouse")
        if "low sugar" in lower:
            concepts.append("low-sugar preference")
        if not concepts:
            concepts.append("task context")
        return concepts

    def _infer_intent(self, prompt: str) -> str:
        lower = prompt.lower()
        if "price" in lower or "cheapest" in lower:
            return "find the cheapest relevant product"
        if "search" in lower:
            return "search for relevant information"
        return "complete the current task efficiently"

    def _infer_duplicate_decision(self, prompt: str) -> str:
        lower = prompt.lower()
        if "wireless mouse" in lower and prompt.count("wireless mouse") > 1:
            return "duplicate"
        if "low-sugar" in lower and prompt.count("low-sugar") > 1:
            return "duplicate"
        return "different"
