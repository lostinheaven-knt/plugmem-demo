#!/usr/bin/env python3
"""Shared helpers for skill evolution scripts."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "default.json"
SCHEMA_DIR = PROJECT_ROOT / "schemas"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class ScriptError(Exception):
    """Expected operational error with a controlled exit code."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def load_json_file(path: Path, *, require_dict: bool = False, description: str | None = None) -> Any:
    target = path.resolve()
    label = description or str(target)
    if not target.exists():
        raise ScriptError(f"Missing file: {label}")
    if not target.is_file():
        raise ScriptError(f"Expected a file but found something else: {label}")

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ScriptError(f"Invalid JSON in {label}: {exc}") from exc
    except OSError as exc:
        raise ScriptError(f"Failed to read {label}: {exc}") from exc

    if require_dict and not isinstance(data, dict):
        raise ScriptError(f"Expected JSON object in {label}")
    return data


def write_json_file(path: Path, payload: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise ScriptError(f"Failed to write JSON file {path}: {exc}") from exc


def read_text_file(path: Path, description: str | None = None) -> str:
    target = path.resolve()
    label = description or str(target)
    if not target.exists():
        raise ScriptError(f"Missing file: {label}")
    if not target.is_file():
        raise ScriptError(f"Expected a file but found something else: {label}")
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScriptError(f"Failed to read {label}: {exc}") from exc


def write_text_file(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ScriptError(f"Failed to write file {path}: {exc}") from exc


def ensure_directory(path: Path, *, description: str | None = None) -> Path:
    label = description or str(path)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ScriptError(f"Failed to create directory {label}: {exc}") from exc
    return path


def load_project_config() -> dict[str, Any]:
    if not DEFAULT_CONFIG_PATH.exists():
        return {}

    data = load_json_file(DEFAULT_CONFIG_PATH, require_dict=True, description="project default config")
    return data if isinstance(data, dict) else {}


def setup_logging(name: str) -> logging.Logger:
    config = load_project_config()
    logging_cfg = config.get("logging", {}) if isinstance(config.get("logging"), dict) else {}
    level_name = os.environ.get("SKILL_EVOLUTION_LOG_LEVEL") or logging_cfg.get("level") or "INFO"
    fmt = logging_cfg.get("format") or DEFAULT_LOG_FORMAT

    logger = logging.getLogger(name)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=getattr(logging, str(level_name).upper(), logging.INFO), format=fmt)
    logger.setLevel(getattr(logging, str(level_name).upper(), logging.INFO))
    return logger


def load_schema(schema_filename: str) -> dict[str, Any]:
    schema_path = SCHEMA_DIR / schema_filename
    data = load_json_file(schema_path, require_dict=True, description=f"schema {schema_filename}")
    return data if isinstance(data, dict) else {}


def _validate_type(value: Any, expected_type: str, path: str) -> list[str]:
    errors: list[str] = []
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "boolean": bool,
        "number": (int, float),
        "integer": int,
    }
    expected = type_map.get(expected_type)
    if expected is None:
        return errors
    if expected_type == "integer":
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    else:
        valid = isinstance(value, expected)
    if not valid:
        errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
    return errors


def _validate_schema_node(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str):
        errors.extend(_validate_type(value, expected_type, path))
        if errors:
            return errors

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{path}: expected one of {enum_values!r}, got {value!r}")
        return errors

    if expected_type == "object":
        assert isinstance(value, dict)
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{path}.{key}: missing required field")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, subschema in properties.items():
                if key in value and isinstance(subschema, dict):
                    errors.extend(_validate_schema_node(value[key], subschema, f"{path}.{key}"))
        return errors

    if expected_type == "array":
        assert isinstance(value, list)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate_schema_node(item, item_schema, f"{path}[{index}]"))
        return errors

    return errors


def validate_against_schema(payload: Any, schema_filename: str, *, description: str) -> None:
    schema = load_schema(schema_filename)
    errors = _validate_schema_node(payload, schema, description)
    if errors:
        raise ScriptError(f"Schema validation failed for {description}: {'; '.join(errors)}")


def fail(message: str, *, exit_code: int = 1) -> ScriptError:
    return ScriptError(message, exit_code=exit_code)


__all__ = [
    "PROJECT_ROOT",
    "SCHEMA_DIR",
    "ScriptError",
    "ensure_directory",
    "fail",
    "load_json_file",
    "load_project_config",
    "load_schema",
    "read_text_file",
    "setup_logging",
    "validate_against_schema",
    "write_json_file",
    "write_text_file",
]
