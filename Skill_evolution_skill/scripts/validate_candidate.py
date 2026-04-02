#!/usr/bin/env python3
"""Candidate validation for skill evolution v0.1.

Usage:
  python validate_candidate.py <candidate_dir>
Writes VALIDATION.json and prints it.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

from common import ScriptError, load_json_file, load_project_config, read_text_file, setup_logging, validate_against_schema, write_json_file


CONFIG = load_project_config()
CANDIDATE_CFG = CONFIG.get("candidate", {}) if isinstance(CONFIG.get("candidate"), dict) else {}
ALLOWED_TYPES = set(CANDIDATE_CFG.get("allowed_types", ["patch", "replacement", "composition"]))
ALLOWED_VALIDATION_STATUS = set(CANDIDATE_CFG.get("allowed_validation_status", ["pending", "passed", "failed", "warning"]))
STUB_MARKERS = ["TBD", "_TBD_", "name: TBD", "description: TBD"]

logger = setup_logging("validate_candidate")


def has_frontmatter_fields(text: str) -> bool:
    if not text.strip().startswith("---"):
        return False
    lower = text.lower()
    return "name:" in lower and "description:" in lower


def extract_frontmatter_name_description(text: str) -> tuple[str, str]:
    if not text.strip().startswith("---"):
        return "", ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", ""
    frontmatter = parts[1]
    name_match = re.search(r"(?mi)^name:\s*(.+?)\s*$", frontmatter)
    desc_match = re.search(r"(?mi)^description:\s*(.+?)\s*$", frontmatter)
    name = name_match.group(1).strip() if name_match else ""
    description = desc_match.group(1).strip() if desc_match else ""
    return name, description


def list_skill_files(skill_dir: Path) -> list[Path]:
    if not skill_dir.exists():
        return []
    return [p for p in skill_dir.rglob("*") if p.is_file()]


def summarize_smoke(candidate: dict, parent_exists: bool, warnings: list[str]) -> str:
    materialized = candidate.get("materialized_from_parent") is True
    if materialized and parent_exists and not warnings:
        return "Materialized candidate from parent skill; structural and content smoke checks passed"
    if materialized and parent_exists:
        return "Materialized candidate from parent skill; passed with warnings requiring review"
    return "Structural validation passed, but behavior remains unverified and/or parent comparison is incomplete"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_candidate.py <candidate_dir>", file=sys.stderr)
        return 1

    candidate_dir = Path(sys.argv[1]).resolve()
    candidate_json = candidate_dir / "candidate.json"
    skill_dir = candidate_dir / "skill"
    skill_md = skill_dir / "SKILL.md"

    checks_run: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, object] = {}

    try:
        if not candidate_dir.exists() or not candidate_dir.is_dir():
            raise ScriptError(f"candidate_dir not found or not a directory: {candidate_dir}")

        checks_run.append("candidate_json_exists")
        if not candidate_json.exists():
            failed.append("candidate_json_missing")
            candidate = {}
        else:
            try:
                candidate = load_json_file(candidate_json, require_dict=True, description="candidate.json")
            except ScriptError:
                candidate = {}
                failed.append("candidate_json_invalid")

        checks_run.append("skill_md_exists")
        if not skill_md.exists():
            failed.append("skill_md_missing")
            skill_text = ""
        else:
            skill_text = read_text_file(skill_md, description="candidate SKILL.md")

        checks_run.append("candidate_type_valid")
        if candidate.get("candidate_type") not in ALLOWED_TYPES:
            failed.append("invalid_candidate_type")

        checks_run.append("skill_frontmatter_has_name_description")
        if skill_text and not has_frontmatter_fields(skill_text):
            failed.append("invalid_skill_frontmatter")

        checks_run.append("frontmatter_name_description_not_stub")
        frontmatter_name, frontmatter_description = extract_frontmatter_name_description(skill_text) if skill_text else ("", "")
        if skill_text:
            if not frontmatter_name or frontmatter_name.upper() == "TBD":
                failed.append("skill_name_stub_or_missing")
            if not frontmatter_description or frontmatter_description.upper() == "TBD":
                failed.append("skill_description_stub_or_missing")

        checks_run.append("skill_content_not_stub")
        if skill_text:
            found_stub_markers = [marker for marker in STUB_MARKERS if marker in skill_text]
            if found_stub_markers:
                failed.append("skill_content_still_stub")
                metrics["stub_markers"] = found_stub_markers

        checks_run.append("proposed_changes_summary_present")
        if not str(candidate.get("proposed_changes_summary", "")).strip():
            failed.append("proposed_changes_summary_missing")

        checks_run.append("skill_contains_actionable_body")
        body_text = skill_text.split("---", 2)[-1].strip() if skill_text else ""
        body_lines = [line for line in body_text.splitlines() if line.strip()]
        metrics["skill_body_nonempty_lines"] = len(body_lines)
        if skill_text and len(body_lines) < 8:
            warnings.append("skill_body_is_very_short")

        checks_run.append("candidate_skill_has_multiple_files")
        skill_files = list_skill_files(skill_dir)
        metrics["skill_file_count"] = len(skill_files)
        if skill_text and len(skill_files) <= 1:
            warnings.append("candidate_contains_only_skill_md")

        checks_run.append("materialization_and_parent_consistency")
        parent_path_value = candidate.get("parent_skill_path")
        parent_path = Path(parent_path_value).resolve() if isinstance(parent_path_value, str) and parent_path_value.strip() else None
        parent_exists = bool(parent_path and parent_path.exists() and (parent_path / "SKILL.md").exists())
        compared_against_parent = parent_exists
        metrics["parent_skill_path"] = str(parent_path) if parent_path else ""
        metrics["parent_skill_exists"] = parent_exists

        if candidate.get("materialized_from_parent") is True:
            if not parent_exists:
                failed.append("materialized_parent_missing")
            elif len(skill_files) < 2:
                warnings.append("materialized_candidate_has_low_file_count")
        else:
            if parent_exists:
                warnings.append("candidate_not_marked_materialized")
            else:
                warnings.append("parent_skill_unresolved_for_comparison")

        checks_run.append("candidate_metadata_status_values_reasonable")
        validation_status = candidate.get("validation_status")
        if validation_status and validation_status not in ALLOWED_VALIDATION_STATUS:
            warnings.append("candidate_validation_status_nonstandard")

        checks_run.append("diff_file_present")
        if not (candidate_dir / "DIFF.md").exists():
            warnings.append("diff_file_missing")

        checks_run.append("candidate_patch_notes_present")
        if skill_text and "## Candidate Patch Notes" not in skill_text:
            warnings.append("candidate_patch_notes_missing")

        passed = len(failed) == 0
        result = {
            "validation_id": f"val-{uuid.uuid4().hex[:12]}",
            "candidate_id": candidate.get("candidate_id", ""),
            "checks_run": checks_run,
            "passed": passed,
            "failed_checks": failed,
            "warnings": warnings,
            "smoke_test_summary": summarize_smoke(candidate, parent_exists, warnings),
            "compared_against_parent": compared_against_parent,
            "behavioral_verification": "unverified",
            "metrics": metrics,
        }

        validate_against_schema(result, "validation-result.schema.json", description="validation result")
        write_json_file(candidate_dir / "VALIDATION.json", result)
        logger.info("Validated candidate %s: passed=%s", candidate.get("candidate_id", ""), passed)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if passed else 2
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while validating candidate")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
