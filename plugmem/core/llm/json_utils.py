from __future__ import annotations

import json


def extract_json_object(text: str) -> dict:
    """Best-effort extraction of a JSON object from model output.

    Handles cases like:
    - leading/trailing explanations
    - fenced ```json blocks

    Raises ValueError if no valid JSON object can be extracted.
    """
    if text is None:
        raise ValueError("Empty response")

    s = text.strip()
    if not s:
        raise ValueError("Empty response")

    # Fast path
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Strip fenced blocks if present
    if "```" in s:
        parts = s.split("```")
        # Try inside each fenced segment (odd indexes are inside fences)
        for i in range(1, len(parts), 2):
            inner = parts[i].strip()
            # remove optional language tag like `json\n`
            if "\n" in inner and inner.split("\n", 1)[0].strip().lower() in {"json", "javascript"}:
                inner = inner.split("\n", 1)[1].strip()
            try:
                obj = json.loads(inner)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

    # Generic brace scan: extract first balanced {...}
    start = s.find("{")
    if start == -1:
        raise ValueError("No JSON object start '{' found")

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s[start : i + 1]
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Failed to parse extracted JSON object: {e}") from e

    raise ValueError("Unbalanced braces; could not extract JSON object")
