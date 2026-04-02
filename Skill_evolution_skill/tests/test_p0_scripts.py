from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class ScriptSmokeTests(unittest.TestCase):
    def run_script(self, script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        script_path = SCRIPTS_DIR / script_name
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def test_emit_evolution_report_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            event_path = tmp_path / "event.json"
            out_path = tmp_path / "report.json"
            event_path.write_text(
                json.dumps({
                    "event_type": "skill_failure",
                    "skill_name": "demo-skill",
                    "error_summary": "missing comparison",
                }),
                encoding="utf-8",
            )

            result = self.run_script("emit_evolution_report.py", str(event_path), str(out_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out_path.exists())
            report = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(report["trigger_type"], "skill_failure")
            self.assertEqual(report["skill_name"], "demo-skill")

    def test_create_candidate_stub_rejects_invalid_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("create_candidate_stub.py", tmp, "demo-skill", "banana")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("candidate_type must be one of", result.stderr)

    def test_attribute_candidate_user_correction_returns_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            report_path.write_text(
                json.dumps({
                    "trigger_type": "user_correction",
                    "user_feedback": "you should compare current period vs previous period",
                }),
                encoding="utf-8",
            )

            result = self.run_script("attribute_candidate.py", str(report_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["recommended_action"], "patch")

    def test_validate_candidate_flags_stub_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("create_candidate_stub.py", tmp, "demo-skill", "patch")
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate_dir = Path(result.stdout.strip())

            validation = self.run_script("validate_candidate.py", str(candidate_dir))
            self.assertEqual(validation.returncode, 2, validation.stderr)
            payload = json.loads(validation.stdout)
            self.assertFalse(payload["passed"])
            self.assertIn("skill_name_stub_or_missing", payload["failed_checks"])

    def test_create_candidate_stub_records_skill_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("create_candidate_stub.py", tmp, "demo-skill", "patch")
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate_dir = Path(result.stdout.strip())
            candidate = json.loads((candidate_dir / "candidate.json").read_text(encoding="utf-8"))
            self.assertEqual(candidate["skill_name"], "demo-skill")
            self.assertEqual(candidate["parent_skill_id"], "demo-skill")
            self.assertEqual(candidate["trigger_type"], "")


if __name__ == "__main__":
    unittest.main()
