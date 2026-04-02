#!/usr/bin/env python3
"""Create an EvolutionReport JSON from a hook event JSON.

v0.1 helper script: intentionally simple and host-agnostic.
Usage:
  python emit_evolution_report.py event.json report.json
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from common import ScriptError, load_json_file, setup_logging, validate_against_schema, write_json_file


logger = setup_logging("emit_evolution_report")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: emit_evolution_report.py <event.json> <report.json>", file=sys.stderr)
        return 1

    in_path = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve()

    try:
        event = load_json_file(in_path, require_dict=True, description="hook event")

        report = {
            "report_id": f"report-{uuid.uuid4().hex[:12]}",
            "transaction_id": event.get("transaction_id", f"txn-{uuid.uuid4().hex[:12]}"),
            "trigger_type": event.get("event_type", "unknown"),
            "skill_name": event.get("skill_name", ""),
            "task_summary": event.get("task_summary", ""),
            "input_summary": event.get("input_summary", ""),
            "observed_failure": event.get("error_summary", ""),
            "user_feedback": event.get("user_correction", ""),
            "environment_notes": event.get("environment_notes", ""),
            "evidence": event.get("evidence", []),
        }

        validate_against_schema(report, "evolution-report.schema.json", description="evolution report")
        write_json_file(out_path, report)
        logger.info("Wrote evolution report to %s", out_path)
        print(str(out_path))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while emitting evolution report")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
