#!/usr/bin/env python3
"""Promotion decision helper for skill evolution v0.1.

Usage:
  python promote_candidate.py <candidate_dir>
Updates candidate.json with a conservative promotion decision.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from common import ScriptError, load_json_file, load_project_config, setup_logging, validate_against_schema, write_json_file


CONFIG = load_project_config()
CANDIDATE_CFG = CONFIG.get("candidate", {}) if isinstance(CONFIG.get("candidate"), dict) else {}
ALLOWED_PROMOTION_STATUS = set(
    CANDIDATE_CFG.get("allowed_promotion_status", ["draft", "experimental", "stable", "deprecated", "archived"])
)

logger = setup_logging("promote_candidate")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: promote_candidate.py <candidate_dir>", file=sys.stderr)
        return 1

    candidate_dir = Path(sys.argv[1]).resolve()
    candidate_json_path = candidate_dir / "candidate.json"
    validation_json_path = candidate_dir / "VALIDATION.json"

    try:
        candidate = load_json_file(candidate_json_path, require_dict=True, description="candidate.json")
        validation = load_json_file(validation_json_path, require_dict=True, description="VALIDATION.json")

        if candidate.get("promotion_status") not in ALLOWED_PROMOTION_STATUS:
            candidate["promotion_status"] = "draft"

        if validation.get("passed") is True:
            candidate["promotion_status"] = "experimental"
            candidate["validation_status"] = "passed"
            candidate["promotion_recommendation"] = "review_required"
            candidate["promotion_reason"] = (
                "Passed structural validation and candidate materialization checks; keep as experimental until human review verifies behavior"
            )
        else:
            candidate["promotion_status"] = "draft"
            candidate["validation_status"] = "failed"
            candidate["promotion_recommendation"] = "reject"
            candidate["promotion_reason"] = "Failed candidate validation"

        validate_against_schema(candidate, "skill-candidate.schema.json", description="promoted candidate")
        write_json_file(candidate_json_path, candidate)
        logger.info(
            "Promotion recommendation for %s: %s",
            candidate.get("candidate_id", ""),
            candidate.get("promotion_recommendation", ""),
        )
        print(json.dumps(candidate, ensure_ascii=False, indent=2))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while promoting candidate")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
