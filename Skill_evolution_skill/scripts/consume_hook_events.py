#!/usr/bin/env python3
"""Consume hook events and drive the skill evolution v0.1 prototype.

Usage:
  python consume_hook_events.py <runtime_dir>

Expected runtime_dir layout:
  inbox/hook-events.jsonl
  transactions/
  reports/
  candidates/
  lineage/

Optional runtime_dir/config.json fields:
  {
    "skills_root": "/abs/or/relative/path/to/skills",
    "parent_skill_paths": {
      "table-analysis-pro": "/path/to/table-analysis-pro"
    }
  }

Event-level path fields take precedence over config:
  - skill_path
  - source_skill_path
  - parent_skill_path
"""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

from common import (
    ScriptError,
    ensure_directory,
    load_json_file,
    load_project_config,
    read_text_file,
    setup_logging,
    validate_against_schema,
    write_json_file,
    write_text_file,
)


logger = setup_logging("consume_hook_events")
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_CONFIG = load_project_config()
REQUIRED_RUNTIME_DIRS = PROJECT_CONFIG.get("runtime", {}).get(
    "required_dirs", ["inbox", "transactions", "reports", "candidates", "lineage"]
)


def ensure_dirs(runtime_dir: Path) -> None:
    for name in REQUIRED_RUNTIME_DIRS:
        ensure_directory(runtime_dir / name)


def load_runtime_config(runtime_dir: Path) -> dict:
    config_path = runtime_dir / "config.json"
    if not config_path.exists():
        return {}
    data = load_json_file(config_path, require_dict=True, description="runtime config")
    return data if isinstance(data, dict) else {}


def load_events(inbox_path: Path) -> list[dict]:
    if not inbox_path.exists():
        return []

    raw = read_text_file(inbox_path, description="hook event inbox")
    events: list[dict] = []
    invalid_lines = 0
    for line_no, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            logger.warning("Skipping invalid JSONL line %s in %s", line_no, inbox_path)
            continue
        if isinstance(data, dict):
            events.append(data)
        else:
            invalid_lines += 1
            logger.warning("Skipping non-object event on line %s in %s", line_no, inbox_path)

    if invalid_lines:
        logger.warning("Skipped %s invalid event line(s) from %s", invalid_lines, inbox_path)
    return events


def save_transaction(path: Path, transaction: dict) -> None:
    validate_against_schema(transaction, "evolution-transaction.schema.json", description="evolution transaction")
    write_json_file(path, transaction)


def run_py(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    script_path = SCRIPT_DIR / script
    if not script_path.exists():
        raise ScriptError(f"Required script not found: {script_path}")
    result = subprocess.run([sys.executable, str(script_path), *args], capture_output=True, text=True)
    logger.info("Ran %s exit=%s", script, result.returncode)
    return result


def parse_json_stdout(result: subprocess.CompletedProcess[str], description: str) -> dict:
    output = (result.stdout or "").strip()
    if not output:
        raise ScriptError(f"{description} returned empty stdout")
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ScriptError(f"{description} returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ScriptError(f"{description} returned non-object JSON")
    return data


def normalize_skill_name(event: dict) -> str:
    if event.get("skill_name"):
        return str(event["skill_name"])

    participating = event.get("participating_skills")
    if isinstance(participating, list) and participating:
        if len(participating) == 1:
            return str(participating[0])
        return "__".join(str(x) for x in participating)

    return "unknown-skill"


def _candidate_paths_from_event(event: dict) -> list[Path]:
    paths: list[Path] = []
    for key in ["skill_path", "source_skill_path", "parent_skill_path"]:
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            paths.append(Path(value))
    return paths


def resolve_parent_skill_dir(runtime_dir: Path, event: dict, skill_name: str, config: dict) -> tuple[Path | None, list[str]]:
    raw_candidates: list[Path] = []
    raw_candidates.extend(_candidate_paths_from_event(event))

    parent_skill_paths = config.get("parent_skill_paths")
    if isinstance(parent_skill_paths, dict):
        value = parent_skill_paths.get(skill_name)
        if isinstance(value, str) and value.strip():
            raw_candidates.append(Path(value))

    skills_root = config.get("skills_root")
    if isinstance(skills_root, str) and skills_root.strip():
        raw_candidates.append(Path(skills_root) / skill_name)

    raw_candidates.extend([
        runtime_dir.parent / skill_name,
        runtime_dir.parent / "skills" / skill_name,
    ])

    tried: list[str] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        resolved = raw if raw.is_absolute() else (runtime_dir / raw).resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        tried.append(key)
        if resolved.exists() and resolved.is_dir() and (resolved / "SKILL.md").exists():
            return resolved, tried

    return None, tried


def build_transaction(event: dict, transaction_id: str, skill_name: str) -> dict:
    trace_ids = event.get("trace_ids")
    if not isinstance(trace_ids, list) or not trace_ids:
        trace_ids = [event.get("trace_id", "")]

    return {
        "transaction_id": transaction_id,
        "created_at": event.get("ts", ""),
        "trigger_type": event.get("event_type", "unknown"),
        "host_framework": event.get("host_framework", "openclaw-like"),
        "source_skill_id": skill_name,
        "related_trace_ids": trace_ids,
        "status": "detected",
        "decision_summary": "",
        "recommended_action": "",
    }


def append_processed_events(processed_path: Path, processed: list[dict]) -> None:
    if not processed:
        return
    existing = read_text_file(processed_path, description="processed inbox") if processed_path.exists() else ""
    lines = existing + "".join(json.dumps(ev, ensure_ascii=False) + "\n" for ev in processed)
    write_text_file(processed_path, lines)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: consume_hook_events.py <runtime_dir>", file=sys.stderr)
        return 1

    runtime_dir = Path(sys.argv[1]).resolve()

    try:
        ensure_dirs(runtime_dir)
        config = load_runtime_config(runtime_dir)

        inbox_path = runtime_dir / "inbox" / "hook-events.jsonl"
        events = load_events(inbox_path)
        if not events:
            print("No events to process")
            return 0

        processed: list[dict] = []
        for event in events:
            transaction_id = event.get("transaction_id", f"txn-{uuid.uuid4().hex[:12]}")
            event["transaction_id"] = transaction_id
            skill_name = normalize_skill_name(event)
            txn_path = runtime_dir / "transactions" / f"{transaction_id}.json"

            transaction = build_transaction(event, transaction_id, skill_name)
            save_transaction(txn_path, transaction)

            event_path = runtime_dir / "reports" / f"{transaction_id}.event.json"
            write_json_file(event_path, event)

            report_path = runtime_dir / "reports" / f"{transaction_id}.report.json"
            r = run_py("emit_evolution_report.py", str(event_path), str(report_path))
            if r.returncode != 0:
                transaction["status"] = "rejected"
                transaction["decision_summary"] = f"Failed to normalize event: {(r.stderr or r.stdout).strip()}"
                save_transaction(txn_path, transaction)
                processed.append(event)
                continue

            transaction["status"] = "normalized"
            save_transaction(txn_path, transaction)

            a = run_py("attribute_candidate.py", str(report_path))
            if a.returncode != 0:
                transaction["status"] = "rejected"
                transaction["decision_summary"] = f"Failed to attribute event: {(a.stderr or a.stdout).strip()}"
                save_transaction(txn_path, transaction)
                processed.append(event)
                continue

            attribution = parse_json_stdout(a, "attribute_candidate.py")
            transaction["status"] = "attributed"
            transaction["recommended_action"] = attribution.get("recommended_action", "")
            transaction["decision_summary"] = attribution.get("reason", "")
            save_transaction(txn_path, transaction)

            action = attribution.get("recommended_action")
            if action in {"patch", "replacement", "composition"}:
                c = run_py("create_candidate_stub.py", str(runtime_dir / "candidates"), skill_name, action)
                candidate_dir_raw = (c.stdout or "").strip()
                candidate_dir = Path(candidate_dir_raw).resolve() if candidate_dir_raw else None
                if c.returncode != 0 or candidate_dir is None or not candidate_dir.exists():
                    transaction["status"] = "rejected"
                    transaction["decision_summary"] = f"Failed to create candidate stub: {(c.stderr or c.stdout).strip()}"
                    save_transaction(txn_path, transaction)
                    processed.append(event)
                    continue

                transaction["status"] = "candidate_generated"
                save_transaction(txn_path, transaction)

                parent_skill_dir, tried_paths = resolve_parent_skill_dir(runtime_dir, event, skill_name, config)
                if parent_skill_dir is not None:
                    m = run_py("materialize_candidate_from_skill.py", str(parent_skill_dir), str(report_path), str(candidate_dir))
                    if m.returncode != 0:
                        transaction["decision_summary"] = (
                            transaction["decision_summary"]
                            + f" | Materialization failed for {parent_skill_dir}: {(m.stderr or m.stdout).strip()}"
                        ).strip(" |")
                        save_transaction(txn_path, transaction)
                else:
                    transaction["decision_summary"] = (
                        transaction["decision_summary"]
                        + f" | Parent skill not found; checked: {', '.join(tried_paths)}"
                    ).strip(" |")
                    save_transaction(txn_path, transaction)

                candidate_json_path = candidate_dir / "candidate.json"
                if candidate_json_path.exists():
                    candidate = load_json_file(candidate_json_path, require_dict=True, description="candidate.json")
                    candidate["skill_resolution_checked_paths"] = tried_paths
                    if parent_skill_dir is not None:
                        candidate["parent_skill_path"] = str(parent_skill_dir)
                    write_json_file(candidate_json_path, candidate)

                v = run_py("validate_candidate.py", str(candidate_dir))
                transaction["status"] = "validated"
                save_transaction(txn_path, transaction)

                p = run_py("promote_candidate.py", str(candidate_dir))
                if p.returncode != 0:
                    transaction["status"] = "rejected"
                    transaction["decision_summary"] = f"Promotion decision failed: {(p.stderr or p.stdout).strip()}"
                    save_transaction(txn_path, transaction)
                    processed.append(event)
                    continue

                run_py("generate_promotion_review.py", str(candidate_dir))
                run_py("write_lineage_record.py", str(runtime_dir / "lineage"), skill_name, str(candidate_dir / "candidate.json"))
                candidate = load_json_file(candidate_dir / "candidate.json", require_dict=True, description="candidate.json")

                recommendation = candidate.get("promotion_recommendation")
                if recommendation == "review_required":
                    transaction["status"] = "review_required"
                elif recommendation == "promotable":
                    transaction["status"] = "finalized"
                else:
                    transaction["status"] = "rejected"

                transaction["decision_summary"] = candidate.get("promotion_reason", transaction["decision_summary"])
                save_transaction(txn_path, transaction)
            else:
                transaction["status"] = "rejected"
                save_transaction(txn_path, transaction)

            processed.append(event)

        processed_path = runtime_dir / "inbox" / "hook-events.processed.jsonl"
        append_processed_events(processed_path, processed)
        write_text_file(inbox_path, "")
        logger.info("Processed %s event(s)", len(processed))
        print(f"Processed {len(processed)} event(s)")
        return 0
    except ScriptError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # pragma: no cover - defensive guardrail
        logger.exception("Unexpected failure while consuming hook events")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
