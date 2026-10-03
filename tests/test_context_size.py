"""Regression tests for `meridian context size`."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "meridian.py"


class ContextSizeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        (self.project / "docs/workflows").mkdir(parents=True)
        (self.project / "tasks").mkdir()
        (self.project / "PROJECT_WORKFLOW.md").write_text("LEAN_DELIVERY\n", encoding="utf-8")
        (self.project / "LANGUAGE_POLICY.md").write_text("English\n", encoding="utf-8")
        (self.project / "AGENTS.md").write_text("Read `PROJECT_WORKFLOW.md` and `LANGUAGE_POLICY.md`.\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(CLI), "context", "size", *arguments, "--project", str(self.project)], text=True, capture_output=True, check=False)

    def governed(self) -> None:
        (self.project / "PROJECT_WORKFLOW.md").write_text("GOVERNED_SDD\n", encoding="utf-8")
        (self.project / "AGENTS.md").write_text(
            "\n".join((
                "Status, project question, or tech-design alignment — use `docs/workflows/STATUS.md`.",
                "- `Proceed with <TASK-ID>` — read `docs/workflows/IMPLEMENTATION.md`.",
                "- `Review <TASK-ID>` — read `docs/workflows/REVIEW.md`.",
                "- `Address review <TASK-ID>` — read `docs/workflows/REMEDIATION.md`.",
                "- `Run lifecycle <TASK-ID>` or `Accept <TASK-ID>` — read `docs/workflows/LIFECYCLE.md`.",
            )), encoding="utf-8"
        )
        for name in ("STATUS.md", "IMPLEMENTATION.md", "REVIEW.md", "REMEDIATION.md", "LIFECYCLE.md"):
            (self.project / "docs/workflows" / name).write_text(f"# {name}\n", encoding="utf-8")

    def test_lean_roles_report_estimated_ranges(self) -> None:
        for role in ("implementation", "review"):
            result = self.run_cli("--role", role, "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "lean-delivery")
            self.assertIn("not tokenizer-accurate", report["estimate"])
            self.assertGreater(report["total"]["bytes"], 0)

    def test_governed_roles_and_missing_citation(self) -> None:
        self.governed()
        (self.project / "docs/workflows/IMPLEMENTATION.md").write_text("Read `docs/MISSING.md`.\n", encoding="utf-8")
        for role in ("status", "design", "implementation", "review", "remediation", "lifecycle"):
            result = self.run_cli("--role", role, "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["mode"], "governed-sdd")
        report = json.loads(self.run_cli("--role", "implementation", "--format", "json").stdout)
        self.assertIn("docs/MISSING.md", [item["path"] for item in report["files"] if item["status"] == "missing"])

    def test_task_authority_milestone_threshold_and_no_writes(self) -> None:
        self.governed()
        (self.project / ".meridian").mkdir()
        (self.project / ".meridian/task-identity.json").write_text('{"version": 1, "mode": "milestone"}\n', encoding="utf-8")
        (self.project / "docs/ARCHITECTURE_DECISIONS.md").write_text("## ADR-0001 — Test\n\nBody.\n", encoding="utf-8")
        task = self.project / "tasks/M1-CORE-001.md"
        task.write_text("# Task\n\n## Authority\n\n- ADR-0001\n", encoding="utf-8")
        before = {path.relative_to(self.project): path.stat().st_mtime_ns for path in self.project.rglob("*") if path.is_file()}
        result = self.run_cli("--role", "implementation", "--task", "M1-CORE-001", "--threshold-bytes", "1", "--format", "text")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("authority-excerpt", result.stdout)
        self.assertIn("Threshold exceeded", result.stdout)
        after = {path.relative_to(self.project): path.stat().st_mtime_ns for path in self.project.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

