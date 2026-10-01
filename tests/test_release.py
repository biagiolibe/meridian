"""Tests for the local-only release preparation command."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import release  # noqa: E402


class ReleasePrepareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in (".claude-plugin", "releases", "migrations", "scripts", "tests"):
            (self.root / directory).mkdir()
        (self.root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.0"}\n', encoding="utf-8")
        (self.root / "releases/1.0.0.json").write_text(json.dumps({
            "version": "1.0.0", "releaseDate": "2026-01-01", "gitTag": "v1.0.0",
            "protocolVersion": 2, "workflowBaselineVersion": "1.0.0",
            "baselineChanged": False, "migrations": [],
        }), encoding="utf-8")
        self.write_changelog("### Added\n\n- New command.")
        (self.root / "scripts/meridian.py").write_text("PROTOCOL_VERSION = 2\n", encoding="utf-8")
        (self.root / "scripts/check_repository.py").write_text("", encoding="utf-8")
        (self.root / "scripts/prepare_release.py").write_text("", encoding="utf-8")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Meridian Test")
        self.git("config", "user.email", "meridian@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True)

    def write_changelog(self, body: str) -> None:
        (self.root / "CHANGELOG.md").write_text(
            f"# Changelog\n\n## [Unreleased]\n\n{body}\n\n## [1.0.0]\n\nOld release.\n", encoding="utf-8"
        )

    def invoke(self, *args: str) -> int:
        return release.main([*args, "--root", str(self.root)])

    def test_preflight_failures_write_nothing(self) -> None:
        cases = [
            ("branch", lambda: self.git("checkout", "-qb", "feature"), "current branch"),
            ("dirty", lambda: (self.root / "extra").write_text("x", encoding="utf-8"), "working tree"),
            ("mismatch", lambda: ((self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.1"}\n', encoding="utf-8"), self.git("add", ".claude-plugin/plugin.json"), self.git("commit", "-qm", "mismatch")), "must agree"),
            ("tag", lambda: self.git("tag", "v1.0.1"), "tag v1.0.1"),
            ("empty", lambda: (self.write_changelog(""), self.git("add", "CHANGELOG.md"), self.git("commit", "-qm", "empty")), "empty body"),
        ]
        for _name, mutate, message in cases:
            with self.subTest(_name), mock.patch("sys.stderr") as stderr:
                mutate()
                before = self.git("status", "--porcelain").stdout
                self.assertEqual(self.invoke("--version", "1.0.1"), 1)
                self.assertIn(message, "".join(str(call) for call in stderr.write.call_args_list))
                self.assertEqual(self.git("status", "--porcelain").stdout, before)
            self.tearDown()
            self.setUp()

    def test_cli_only_dry_run_writes_nothing(self) -> None:
        before = self.git("status", "--porcelain").stdout
        self.assertEqual(self.invoke("--bump", "patch", "--dry-run"), 0)
        self.assertEqual(self.git("status", "--porcelain").stdout, before)

    def test_template_change_needs_upgrade_notes(self) -> None:
        (self.root / "migrations/001-test.json").write_text('{"id":"001-test","to":"1.0.1"}', encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "migration")
        self.assertEqual(self.invoke("--version", "1.0.1"), 1)

    def test_template_change_and_protocol_gate(self) -> None:
        (self.root / "migrations/001-test.json").write_text('{"id":"001-test","to":"1.0.1"}', encoding="utf-8")
        self.write_changelog("### Upgrade notes\n\n- Apply the migration.")
        (self.root / "scripts/meridian.py").write_text("PROTOCOL_VERSION = 3\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "migration")
        self.assertEqual(self.invoke("--version", "1.0.1"), 1)
        with mock.patch.object(release, "validate", return_value=(0, [])):
            self.assertEqual(self.invoke("--version", "1.0.1", "--protocol-reviewed"), 0)
        record = json.loads((self.root / "releases/1.0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(record["migrations"], ["001-test"])
        self.assertTrue(record["baselineChanged"])

    def test_validation_failure_rolls_back(self) -> None:
        with mock.patch.object(release, "validate", return_value=(7, ["test", "failure"])):
            self.assertEqual(self.invoke("--version", "1.0.1"), 7)
        self.assertFalse((self.root / "releases/1.0.1.json").exists())
        self.assertEqual((self.root / "VERSION").read_text(encoding="utf-8"), "1.0.0\n")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_commit_contains_only_release_files(self) -> None:
        with mock.patch.object(release, "validate", return_value=(0, [])):
            self.assertEqual(self.invoke("--version", "1.0.1"), 0)
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout.strip(), "Release 1.0.1")
        files = self.git("show", "--format=", "--name-only", "HEAD").stdout.splitlines()
        self.assertEqual(files, [".claude-plugin/plugin.json", "CHANGELOG.md", "VERSION", "releases/1.0.1.json"])


if __name__ == "__main__":
    unittest.main()
