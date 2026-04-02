#!/usr/bin/env python3
"""Append candidate lineage info to a skill lineage JSON file.

Usage:
  python write_lineage_record.py <lineage_dir> <skill_name> <candidate_json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from common import ScriptError, ensure_directory, load_json_file, setup_logging, write_json_file


logger = setup_logging("write_lineage_record")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: write_lineage_record.py <lineage_dir> <skill_name> <candidate_json>", file=sys.stderr)
        return 1

    lineage_dir = Path(sys.argv[1]).resolve()
    skill_name = sys.argv[2].strip()
    candidate_json_path = Path(sys.argv[3]).resolve()

    try:
        if not skill_name:
            raise ScriptError("skill_name must not be empty")

        candidate = load_json_file(candidate_json_path, require_dict=True, description="candidate.json")
        ensure_directory(lineage_dir)
        out_path = lineage_dir / f"{skill_name}.json"

        if out_path.exists():
            data = load_json_file(out_path, require_dict=True, description=f"lineage record for {skill_name}")
        else:
            data = {
                "skill_name": skill_name,
                "stable_ref": None,
                "candidates": [],
                "links": [],
            }

        data.setdefault("candidates", []).append({
            "candidate_id": candidate.get("candidate_id"),
            "candidate_type": candidate.get("candidate_type"),
            "promotion_status": candidate.get("promotion_status"),
            "candidate_location": candidate.get("candidate_location"),
        })

        write_json_file(out_path, data)
        logger.info("Updated lineage record %s", out_path)
        print(str(out_path))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while writing lineage record")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
