from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class StructuredOutputError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationRule:
    key: str
    types: tuple[type, ...] = (object,)
    allowed: set[Any] | None = None
    non_empty: bool = False


def validate_object(obj: Any, required: Iterable[ValidationRule]) -> dict[str, Any]:
    """Lightweight dict validation/normalization.

    - Enforces presence of required keys
    - Enforces value types
    - Optionally enforces allowed values and non-empty strings

    Returns the original dict (mutated only by callers).
    """
    if not isinstance(obj, dict):
        raise StructuredOutputError(f"Expected JSON object/dict, got {type(obj)}")

    for rule in required:
        if rule.key not in obj:
            raise StructuredOutputError(f"Missing required key: {rule.key}")
        val = obj[rule.key]
        if rule.types and not isinstance(val, rule.types):
            raise StructuredOutputError(f"Key '{rule.key}' expected types {rule.types}, got {type(val)}")
        if rule.non_empty and isinstance(val, str) and not val.strip():
            raise StructuredOutputError(f"Key '{rule.key}' must be a non-empty string")
        if rule.allowed is not None and val not in rule.allowed:
            raise StructuredOutputError(f"Key '{rule.key}' invalid value {val!r}; allowed={sorted(rule.allowed)}")

    return obj


def coerce_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str) and x.strip().lower() in {"true", "false"}:
        return x.strip().lower() == "true"
    raise StructuredOutputError(f"Expected boolean, got {x!r} ({type(x)})")
