#!/usr/bin/env python3
"""Create a candidate stub directory for skill evolution.

Usage:
  python create_candidate_stub.py <candidates_dir> <skill_name> <candidate_type>
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

from common import (
    ScriptError,
    ensure_directory,
    load_project_config,
    setup_logging,
    validate_against_schema,
    write_json_file,
    write_text_file,
)


logger = setup_logging("create_candidate_stub")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: create_candidate_stub.py <candidates_dir> <skill_name> <candidate_type>", file=sys.stderr)
        return 1

    candidates_dir = Path(sys.argv[1]).resolve()
    skill_name = sys.argv[2].strip()
    candidate_type = sys.argv[3].strip()

    config = load_project_config()
    allowed_types = set(config.get("candidate", {}).get("allowed_types", [])) or {"patch", "replacement", "composition"}

    try:
        if not skill_name:
            raise ScriptError("skill_name must not be empty")
        if candidate_type not in allowed_types:
            raise ScriptError(
                f"candidate_type must be one of: {', '.join(sorted(allowed_types))}"
            )

        candidate_id = f"cand-{uuid.uuid4().hex[:12]}"
        root = candidates_dir / candidate_id
        skill_dir = root / "skill"
        refs_dir = skill_dir / "references"
        scripts_dir = skill_dir / "scripts"

        ensure_directory(refs_dir)
        ensure_directory(scripts_dir)

        candidate = {
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "skill_name": skill_name,
            "parent_skill_id": skill_name,
            "trigger_type": "",
            "promotion_status": "draft",
            "validation_status": "pending",
            "proposed_changes_summary": "",
            "candidate_location": str(root),
        }

        validate_against_schema(candidate, "skill-candidate.schema.json", description="candidate stub")
        write_json_file(root / "candidate.json", candidate)
        write_json_file(root / "VALIDATION.json", {"status": "pending"})
        write_text_file(root / "DIFF.md", "# Diff\n\n_TBD_\n")
        write_text_file(
            skill_dir / "SKILL.md",
            "---\nname: TBD\ndescription: TBD\n---\n\n# Candidate Skill\n\n_TBD_\n",
        )

        logger.info("Created candidate stub %s for parent skill %s", candidate_id, skill_name)
        print(str(root))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while creating candidate stub")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
