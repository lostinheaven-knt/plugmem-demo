from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class PipelineP1Tests(unittest.TestCase):
    def run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        script_path = SCRIPTS_DIR / script_name
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def test_consume_hook_events_end_to_end_demo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            init_result = self.run_script("init_runtime_demo.py", str(runtime_dir))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            consume_result = self.run_script("consume_hook_events.py", str(runtime_dir))
            self.assertEqual(consume_result.returncode, 0, consume_result.stderr)
            self.assertIn("Processed 3 event(s)", consume_result.stdout)

            processed_path = runtime_dir / "inbox" / "hook-events.processed.jsonl"
            self.assertTrue(processed_path.exists())
            self.assertEqual(len(processed_path.read_text(encoding="utf-8").splitlines()), 3)

            txns = sorted((runtime_dir / "transactions").glob("*.json"))
            self.assertEqual(len(txns), 3)
            for txn_path in txns:
                txn = json.loads(txn_path.read_text(encoding="utf-8"))
                self.assertIn(txn["status"], {"review_required", "rejected", "finalized"})
                self.assertIn("transaction_id", txn)

            candidates = sorted((runtime_dir / "candidates").glob("*/candidate.json"))
            self.assertEqual(len(candidates), 3)
            seen_trigger_types = set()
            for candidate_path in candidates:
                candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                self.assertIn(candidate["candidate_type"], {"patch", "replacement", "composition"})
                self.assertIn(candidate["promotion_status"], {"draft", "experimental", "stable", "deprecated", "archived"})
                self.assertEqual(candidate["skill_name"], "table-analysis-pro")
                self.assertEqual(candidate["parent_skill_id"], "table-analysis-pro")
                self.assertIn(candidate["trigger_type"], {"skill_failure", "user_correction", "repeated_success_pattern"})
                self.assertTrue(candidate["derived_from_report_id"].startswith("report-"))
                seen_trigger_types.add(candidate["trigger_type"])

            self.assertEqual(seen_trigger_types, {"skill_failure", "user_correction", "repeated_success_pattern"})

    def test_schema_validation_rejects_bad_candidate_type_written_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            init_result = self.run_script("init_runtime_demo.py", str(runtime_dir))
            self.assertEqual(init_result.returncode, 0, init_result.stderr)

            report_path = runtime_dir / "examples" / "skill_failure.json"
            generated_report_path = runtime_dir / "bad.report.json"
            emit_result = self.run_script("emit_evolution_report.py", str(report_path), str(generated_report_path))
            self.assertEqual(emit_result.returncode, 0, emit_result.stderr)

            candidates_dir = runtime_dir / "candidates"
            bad_create = self.run_script("create_candidate_stub.py", str(candidates_dir), "table-analysis-pro", "patch")
            self.assertEqual(bad_create.returncode, 0, bad_create.stderr)
            candidate_dir = Path(bad_create.stdout.strip())

            candidate_json_path = candidate_dir / "candidate.json"
            candidate = json.loads(candidate_json_path.read_text(encoding="utf-8"))
            candidate["candidate_type"] = "banana"
            candidate_json_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")

            validate_result = self.run_script("promote_candidate.py", str(candidate_dir))
            self.assertNotEqual(validate_result.returncode, 0)
            self.assertIn("Schema validation failed", validate_result.stderr)


if __name__ == "__main__":
    unittest.main()
