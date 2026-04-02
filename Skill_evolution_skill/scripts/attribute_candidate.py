#!/usr/bin/env python3
"""Heuristic attribution for skill evolution v0.1.

Usage:
  python attribute_candidate.py <report.json>
Prints a JSON decision to stdout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from common import ScriptError, load_json_file, setup_logging


logger = setup_logging("attribute_candidate")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: attribute_candidate.py <report.json>", file=sys.stderr)
        return 1

    report_path = Path(sys.argv[1]).resolve()

    try:
        report = load_json_file(report_path, require_dict=True, description="evolution report")

        trigger = report.get("trigger_type", "")
        failure = (report.get("observed_failure", "") or "").lower()
        feedback = (report.get("user_feedback", "") or "").lower()

        action = "no_change"
        reason = "insufficient evidence"

        env_markers = ["timeout", "permission", "credential", "auth", "network", "quota"]
        if any(m in failure for m in env_markers):
            action = "no_change"
            reason = "likely environment/tooling issue"
        elif trigger == "user_correction":
            action = "patch"
            reason = "explicit user correction suggests skill patch"
        elif trigger == "repeated_success_pattern":
            action = "composition"
            reason = "repeated successful workflow suggests higher-level composition"
        elif trigger == "skill_failure":
            if any(m in failure for m in ["missing", "wrong", "incorrect", "incomplete"]) or feedback:
                action = "patch"
                reason = "output/problem shape suggests patchable skill issue"
            elif any(m in failure for m in ["drift", "mismatch", "bad structure", "not relevant"]):
                action = "replacement"
                reason = "failure suggests larger skill mismatch"
            else:
                action = "patch"
                reason = "default conservative choice for skill failure"

        decision = {"recommended_action": action, "reason": reason}
        logger.info("Attributed report %s -> %s", report_path.name, action)
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while attributing candidate")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
