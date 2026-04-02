#!/usr/bin/env python3
"""Materialize a first-pass candidate from an existing skill directory.

Usage:
  python materialize_candidate_from_skill.py <parent_skill_dir> <report.json> <candidate_dir>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from common import ScriptError, load_json_file, read_text_file, setup_logging, write_json_file, write_text_file


logger = setup_logging("materialize_candidate_from_skill")


def append_patch_notes(skill_md: Path, report: dict) -> None:
    original = read_text_file(skill_md) if skill_md.exists() else ""
    note = (
        "\n\n## Candidate Patch Notes\n\n"
        f"- Trigger: {report.get('trigger_type', '')}\n"
        f"- Task: {report.get('task_summary', '')}\n"
        f"- Observed issue: {report.get('observed_failure', '') or report.get('user_feedback', '')}\n"
        "- Intent: create a safer, reviewable first-pass evolution candidate.\n"
    )
    write_text_file(skill_md, original + note)


def build_patch_blocks(report: dict, parent_skill_name: str) -> tuple[dict[str, str], str, list[str]]:
    trigger = report.get("trigger_type", "")
    observed = (report.get("observed_failure", "") or "").lower()
    feedback = (report.get("user_feedback", "") or "").lower()
    task = report.get("task_summary", "")

    tags: list[str] = []
    section_blocks: dict[str, list[str]] = {}
    fallback_lines = ["\n\n## Directed Evolution Patch\n", f"Target skill: `{parent_skill_name}`\n", f"Trigger type: `{trigger}`\n"]
    if task:
        fallback_lines.append(f"Task context: {task}\n")

    def add_block(section: str, content: str) -> None:
        section_blocks.setdefault(section, []).append(content)

    if any(k in observed or k in feedback for k in ["compare", "comparison", "previous period", "current vs previous"]):
        tags.append("comparison")
        block = (
            "\n#### Evolution Patch Insert: comparison\n"
            "- Explicitly compare the current slice against the requested baseline or previous period before concluding when such comparison is implied or requested.\n"
            "- Confirm metric definitions, grouping grain, and time windows are comparable before presenting comparison findings.\n"
            "- If comparison parity is uncertain, downgrade confidence and ask for clarification instead of implying equivalence.\n"
        )
        add_block("## Core rules", block)
        add_block("### 5. Validate before concluding", block)
        fallback_lines.extend(["\n### Comparison-first reinforcement\n", block])

    if any(k in observed or k in feedback for k in ["missing", "incomplete", "omitted"]):
        tags.append("completeness")
        block = (
            "\n#### Evolution Patch Insert: completeness\n"
            "- Add a final completeness check before returning: confirm that all requested sections, comparisons, and metric explanations are present.\n"
            "- If any requested output section is missing, explicitly state what remains incomplete instead of presenting the answer as complete.\n"
        )
        add_block("### 5. Validate before concluding", block)
        add_block("### 6. Present results cleanly", block)
        fallback_lines.extend(["\n### Completeness reinforcement\n", block])

    if trigger == "user_correction" and report.get("user_feedback"):
        tags.append("correction")
        block = (
            "\n#### Evolution Patch Insert: correction\n"
            f"- Convert this correction into an explicit execution rule for future runs: {report.get('user_feedback')}\n"
        )
        add_block("## Gotchas", block)
        add_block("## Core rules", block)
        fallback_lines.extend(["\n### Correction-to-rule reinforcement\n", block])

    if trigger == "repeated_success_pattern":
        tags.append("composition")
        block = (
            "\n### Composition hint\n"
            "- This repeated success pattern suggests a higher-level reusable workflow candidate rather than only patching the parent skill.\n"
        )
        fallback_lines.append(block)

    if not tags:
        tags.append("generic")
        block = (
            "\n#### Evolution Patch Insert: generic\n"
            "- Tighten self-check and output coverage before returning results.\n"
        )
        add_block("## Core rules", block)
        fallback_lines.extend(["\n### Generic reinforcement\n", block])

    return {k: "".join(v) for k, v in section_blocks.items()}, "".join(fallback_lines), tags


def insert_after_heading(text: str, heading: str, insert_block: str) -> tuple[str, bool]:
    marker = heading + "\n"
    idx = text.find(marker)
    if idx == -1:
        return text, False
    insert_pos = idx + len(marker)
    return text[:insert_pos] + insert_block + text[insert_pos:], True


def apply_section_targeted_patches(skill_text: str, section_blocks: dict[str, str], fallback_patch: str) -> tuple[str, list[str], list[str]]:
    used_sections: list[str] = []
    fallback_sections: list[str] = []
    updated = skill_text

    for heading, block in section_blocks.items():
        next_text, ok = insert_after_heading(updated, heading, block)
        if ok:
            updated = next_text
            used_sections.append(heading)
        else:
            fallback_sections.append(heading)

    if fallback_sections:
        updated = updated + fallback_patch

    return updated, used_sections, fallback_sections


def count_files(root: Path) -> int:
    return sum(1 for p in root.rglob("*") if p.is_file())


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: materialize_candidate_from_skill.py <parent_skill_dir> <report.json> <candidate_dir>", file=sys.stderr)
        return 1

    parent_skill_dir = Path(sys.argv[1]).resolve()
    report_json = Path(sys.argv[2]).resolve()
    candidate_dir = Path(sys.argv[3]).resolve()

    try:
        if not parent_skill_dir.exists() or not parent_skill_dir.is_dir():
            raise ScriptError(f"Parent skill dir not found: {parent_skill_dir}")
        if not (parent_skill_dir / "SKILL.md").exists():
            raise ScriptError(f"Parent skill dir does not contain SKILL.md: {parent_skill_dir}")
        if not candidate_dir.exists() or not candidate_dir.is_dir():
            raise ScriptError(f"Candidate dir not found: {candidate_dir}")

        report = load_json_file(report_json, require_dict=True, description="evolution report")
        skill_dst = candidate_dir / "skill"
        skill_dst.mkdir(parents=True, exist_ok=True)

        copied_items: list[str] = []
        for item in parent_skill_dir.iterdir():
            if item.name in {".git", "dist", "__pycache__"}:
                continue
            dst = skill_dst / item.name
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)
            copied_items.append(item.name)

        skill_md = skill_dst / "SKILL.md"
        append_patch_notes(skill_md, report)

        original = read_text_file(skill_md) if skill_md.exists() else ""
        section_blocks, fallback_patch, tags = build_patch_blocks(report, parent_skill_dir.name)
        patched, used_sections, fallback_sections = apply_section_targeted_patches(original, section_blocks, fallback_patch)
        write_text_file(skill_md, patched)

        diff_md = candidate_dir / "DIFF.md"
        write_text_file(
            diff_md,
            "# Diff\n\n"
            f"- Parent skill: {parent_skill_dir.name}\n"
            f"- Parent skill path: {parent_skill_dir}\n"
            f"- Added Candidate Patch Notes based on report: {report_json.name}\n"
            f"- Directed patch tags: {', '.join(tags)}\n"
            f"- Section-targeted inserts applied to: {', '.join(used_sections) if used_sections else '(none)'}\n"
            f"- Fallback append used for missing sections: {', '.join(fallback_sections) if fallback_sections else '(none)'}\n"
            f"- Copied top-level items: {', '.join(copied_items) if copied_items else '(none)'}\n"
            "- Strategy: preserve parent body, insert reviewable patch blocks near relevant sections, and fall back to append-only when needed.\n",
        )

        candidate_json = candidate_dir / "candidate.json"
        if candidate_json.exists():
            candidate = load_json_file(candidate_json, require_dict=True, description="candidate.json")
            candidate["skill_name"] = str(report.get("skill_name") or candidate.get("skill_name") or parent_skill_dir.name)
            candidate["parent_skill_id"] = str(candidate.get("parent_skill_id") or parent_skill_dir.name)
            candidate["trigger_type"] = str(report.get("trigger_type") or candidate.get("trigger_type") or "")
            candidate["derived_from_report_id"] = str(report.get("report_id") or candidate.get("derived_from_report_id") or "")
            candidate["proposed_changes_summary"] = (
                "Copied parent skill, appended Candidate Patch Notes, and inserted section-targeted evolution patch blocks"
            )
            candidate["patch_tags"] = tags
            candidate["target_sections"] = used_sections
            candidate["fallback_sections"] = fallback_sections
            candidate["parent_skill_path"] = str(parent_skill_dir)
            candidate["materialized_from_parent"] = True
            candidate["materialized_file_count"] = count_files(skill_dst)
            write_json_file(candidate_json, candidate)

        logger.info("Materialized candidate at %s from parent %s", candidate_dir, parent_skill_dir)
        print(str(candidate_dir))
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while materializing candidate")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
