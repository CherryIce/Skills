"""Behavioral checks for the project-local learning artifacts and summary."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import summarize_factory_lessons as learning


ROOT = Path(__file__).resolve().parent.parent


def record(run_id, project_ref, severity="P1", confidence="confirmed", evidence=None):
    return {
        "schema_version": 1,
        "status": "completed",
        "run": {
            "run_id": run_id,
            "project_ref": project_ref,
            "scope": "mvp",
            "product_verdict": "needs_revision",
        },
        "lessons": [{
            "pattern_key": "flutter.overlay.dismiss-reopen",
            "severity": severity,
            "symptom": "Reopen fails",
            "phase": "runtime",
            "cause_confidence": confidence,
            "cause": "Disposed context",
            "evidence": ["test-output.txt"] if evidence is None else evidence,
            "proposed_change": "Add a transition test",
            "regression_check": "Before fails and after passes",
        }],
    }


class LearningTests(unittest.TestCase):
    def test_two_projects_flag_review_but_same_project_does_not(self):
        one = record("run-1", "project-a")
        same_project = record("run-2", "project-a")
        other_project = record("run-3", "project-b")
        self.assertEqual(learning.summarize([one, same_project])[0][-1], "more_evidence_needed")
        self.assertEqual(learning.summarize([one, other_project])[0][-1], "review_candidate")

    def test_single_confirmed_p0_is_urgent_not_auto_adopted(self):
        self.assertEqual(learning.summarize([record("run-1", "project-a", "P0")])[0][-1], "urgent_review")
        unverified = record("run-2", "project-b", "P0", "hypothesis", [])
        self.assertEqual(learning.summarize([unverified])[0][-1], "more_evidence_needed")

    def test_incomplete_scaffold_is_rejected_by_aggregator(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "retrospective.json"
            path.write_text(json.dumps({"schema_version": 1, "status": "not_evaluated"}))
            with self.assertRaisesRegex(ValueError, "not completed"):
                learning.load_record(path)

    def test_cli_reads_only_supplied_completed_records(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, project in enumerate(("project-a", "project-b"), 1):
                path = Path(directory) / f"run-{index}.json"
                path.write_text(json.dumps(record(f"run-{index}", project)))
                paths.append(path)
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/summarize_factory_lessons.py"),
                 *(str(path) for path in paths)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("review_candidate", completed.stdout)
            self.assertNotIn("project-a", completed.stdout)

    def test_bootstrap_creates_valid_project_local_scaffold(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "app"
            project.mkdir()
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/bootstrap_factory_run.py"),
                 "--project", str(project), "--config", str(ROOT / "assets/templates/intake.json")],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            path = project / "docs/factory/RETROSPECTIVE.json"
            scaffold = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(scaffold["status"], "not_evaluated")
            self.assertEqual(scaffold["lessons"], [])
            self.assertTrue((project / "docs/release/FUNCTIONAL_REVIEW.md").exists())
            brief = (project / "docs/product/PRODUCT_BRIEF.md").read_text(encoding="utf-8")
            self.assertIn("默认跟随系统；匹配支持的系统语言，无法匹配时回退英文", brief)
            self.assertIn("默认跟随系统 light/dark", brief)
            self.assertIn("替换 iOS/Android 的 Flutter 默认图标", brief)
            self.assertIn("iOS/Android 原生启动页", brief)
            self.assertIn("首次安装可跳过", brief)
            self.assertIn("默认不强制既有用户重新进入引导", brief)
            self.assertIn("ITSAppUsesNonExemptEncryption=false", brief)
            self.assertIn("滚动视口使用可用空间", brief)
            self.assertIn("默认使用 iOS/Cupertino 风格弹框", brief)


if __name__ == "__main__":
    unittest.main()
