#!/usr/bin/env python3
"""Initialize a demo runtime tree for skill evolution v0.1.

Usage:
  python init_runtime_demo.py <runtime_dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

from common import ScriptError, ensure_directory, setup_logging, write_json_file, write_text_file


logger = setup_logging("init_runtime_demo")

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARENT_SKILL = (WORKSPACE_ROOT / "table-analysis-pro").resolve()

EXAMPLE_FAILURE = {
    "event_type": "skill_failure",
    "skill_name": "table-analysis-pro",
    "trace_id": "trace-demo-001",
    "task_summary": "Analyze sales table and produce metric summary",
    "error_summary": "Output missing comparison section and incomplete metric explanation",
    "evidence": [
        "Expected a comparison section between current and previous period",
        "Metric definition explanation was incomplete"
    ],
    "ts": "2026-03-26T14:40:00+08:00",
    "host_framework": "openclaw-like",
    "skill_path": str(DEFAULT_PARENT_SKILL)
}

EXAMPLE_CORRECTION = {
    "event_type": "user_correction",
    "skill_name": "table-analysis-pro",
    "trace_id": "trace-demo-002",
    "task_summary": "Review table analysis output",
    "user_correction": "The skill should explicitly compare current period vs previous period before giving conclusions.",
    "evidence": [
        "User asked for more explicit before/after comparison"
    ],
    "ts": "2026-03-26T14:41:00+08:00",
    "host_framework": "openclaw-like",
    "skill_path": str(DEFAULT_PARENT_SKILL)
}

EXAMPLE_SUCCESS = {
    "event_type": "repeated_success_pattern",
    "workflow_summary": "Read table schema -> define metrics -> compare periods -> summarize risks",
    "participating_skills": ["table-analysis-pro"],
    "trace_ids": ["trace-demo-003", "trace-demo-004", "trace-demo-005"],
    "success_count_window": 3,
    "ts": "2026-03-26T14:42:00+08:00",
    "host_framework": "openclaw-like",
    "skill_name": "table-analysis-pro",
    "skill_path": str(DEFAULT_PARENT_SKILL)
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: init_runtime_demo.py <runtime_dir>", file=sys.stderr)
        return 1

    runtime_dir = Path(sys.argv[1]).resolve()

    try:
        for sub in ["inbox", "transactions", "reports", "candidates", "lineage", "examples"]:
            ensure_directory(runtime_dir / sub)

        config = {
            "skills_root": str(WORKSPACE_ROOT),
            "parent_skill_paths": {
                "table-analysis-pro": str(DEFAULT_PARENT_SKILL)
            }
        }
        write_json_file(runtime_dir / "config.json", config)

        write_json_file(runtime_dir / "examples" / "skill_failure.json", EXAMPLE_FAILURE)
        write_json_file(runtime_dir / "examples" / "user_correction.json", EXAMPLE_CORRECTION)
        write_json_file(runtime_dir / "examples" / "repeated_success_pattern.json", EXAMPLE_SUCCESS)

        inbox_lines = [
            __import__("json").dumps(EXAMPLE_FAILURE, ensure_ascii=False),
            __import__("json").dumps(EXAMPLE_CORRECTION, ensure_ascii=False),
            __import__("json").dumps(EXAMPLE_SUCCESS, ensure_ascii=False),
        ]
        write_text_file(runtime_dir / "inbox" / "hook-events.jsonl", "\n".join(inbox_lines) + "\n")

        logger.info("Initialized runtime demo at %s", runtime_dir)
        print(str(runtime_dir))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while initializing runtime demo")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
