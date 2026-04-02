#!/usr/bin/env python3
"""Generate a conservative promotion review draft for a candidate.

Usage:
  python generate_promotion_review.py <candidate_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from common import ScriptError, load_json_file, setup_logging, validate_against_schema, write_json_file


logger = setup_logging("generate_promotion_review")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: generate_promotion_review.py <candidate_dir>", file=sys.stderr)
        return 1

    candidate_dir = Path(sys.argv[1]).resolve()
    candidate_json_path = candidate_dir / "candidate.json"
    validation_json_path = candidate_dir / "VALIDATION.json"

    try:
        candidate = load_json_file(candidate_json_path, require_dict=True, description="candidate.json")
        validation = load_json_file(validation_json_path, require_dict=True, description="VALIDATION.json")
        tags = candidate.get("patch_tags", [])
        warnings = validation.get("warnings", [])

        structural_validity = "pass" if validation.get("passed") else "fail"
        trigger_alignment = "strong" if tags else "unknown"
        behavioral_improvement = "unknown"
        risk_delta = "low" if validation.get("passed") and not warnings else "medium"
        recommendation = candidate.get("promotion_recommendation") or ("review_required" if validation.get("passed") else "reject")

        review = {
            "candidate_id": candidate.get("candidate_id", ""),
            "structural_validity": structural_validity,
            "trigger_alignment": trigger_alignment,
            "behavioral_improvement": behavioral_improvement,
            "risk_delta": risk_delta,
            "recommendation": recommendation,
            "review_notes": (
                "Conservative draft review: structural checks passed and parent-derived materialization looks coherent; "
                "behavior improvement still requires human spot-check."
                if validation.get("passed")
                else "Validation failed; do not advance this candidate without repairs."
            ),
            "rollback_ready": True,
        }

        out = candidate_dir / "PROMOTION_REVIEW.json"
        validate_against_schema(review, "promotion-review.schema.json", description="promotion review")
        write_json_file(out, review)
        logger.info("Generated promotion review for %s", candidate.get("candidate_id", ""))
        print(json.dumps(review, ensure_ascii=False, indent=2))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while generating promotion review")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
