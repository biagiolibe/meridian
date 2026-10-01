"""Tests for the local-only release preparation command."""

from __future__ import annotations

import json
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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

    def test_prepare_word_matches_legacy_prepare_form(self) -> None:
        legacy = io.StringIO()
        named = io.StringIO()
        with redirect_stdout(legacy):
            self.assertEqual(self.invoke("--bump", "patch", "--dry-run"), 0)
        with redirect_stdout(named):
            self.assertEqual(self.invoke("prepare", "--bump", "patch", "--dry-run"), 0)
        self.assertEqual(named.getvalue(), legacy.getvalue())

    def test_dry_run_prints_only_new_changelog_section(self) -> None:
        self.write_changelog("### Added\n\n- New command." + "\n\n## [0.9.9]\n\n" + "Old release.\n" * 500)
        self.git("add", "CHANGELOG.md")
        self.git("commit", "-qm", "long changelog")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(self.invoke("--bump", "patch", "--dry-run"), 0)
        text = output.getvalue()
        self.assertTrue(text.startswith("Derived release kind: CLI-only release\nVersion: 1.0.1\nWould write:"))
        self.assertIn("Derived release kind: CLI-only release", text)
        self.assertIn("Version: 1.0.1", text)
        self.assertIn("Would write: VERSION, .claude-plugin/plugin.json, releases/1.0.1.json, CHANGELOG.md", text)
        self.assertIn("## [1.0.1]", text)
        self.assertNotIn("## [0.9.9]", text)
        self.assertLess(len(text), 500)

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

    def test_prepare_directs_an_already_prepared_release_to_publish(self) -> None:
        self.git("tag", "v1.0.0")
        (self.root / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        (self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.1"}\n', encoding="utf-8")
        (self.root / "releases/1.0.1.json").write_text(json.dumps({
            "version": "1.0.1", "gitTag": "v1.0.1", "baselineChanged": False, "migrations": [],
        }), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Prepare release in migration task")
        with mock.patch("sys.stderr") as stderr:
            self.assertEqual(self.invoke("--bump", "patch"), 1)
        self.assertIn("publish --confirm v1.0.1", "".join(str(call) for call in stderr.write.call_args_list))

    def test_commit_contains_only_release_files(self) -> None:
        with mock.patch.object(release, "validate", return_value=(0, [])):
            self.assertEqual(self.invoke("--version", "1.0.1"), 0)
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout.strip(), "Release 1.0.1")
        files = self.git("show", "--format=", "--name-only", "HEAD").stdout.splitlines()
        self.assertEqual(files, [".claude-plugin/plugin.json", "CHANGELOG.md", "VERSION", "releases/1.0.1.json"])


class ReleasePublishTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        self.remote = Path(self.temporary.name) / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(self.remote)], check=True)
        for directory in (".claude-plugin", "releases", "scripts", "bin"):
            (self.root / directory).mkdir()
        (self.root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.0"}\n', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
        (self.root / "releases/1.0.0.json").write_text(json.dumps({
            "version": "1.0.0", "gitTag": "v1.0.0", "baselineChanged": False, "migrations": [],
        }), encoding="utf-8")
        (self.root / "scripts/check_repository.py").write_text("", encoding="utf-8")
        (self.root / "scripts/prepare_release.py").write_text("", encoding="utf-8")
        (self.root / "bin/meridian").write_text("#!/bin/sh\necho UP_TO_DATE\n", encoding="utf-8")
        (self.root / "bin/meridian").chmod(0o755)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Meridian Test")
        self.git("config", "user.email", "meridian@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-qu", "origin", "main")
        self.prepare_release()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True)

    def prepare_release(self) -> None:
        (self.root / "VERSION").write_text("1.0.1\n", encoding="utf-8")
        (self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.1"}\n', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.1]\n", encoding="utf-8")
        (self.root / "releases/1.0.1.json").write_text(json.dumps({
            "version": "1.0.1", "gitTag": "v1.0.1", "baselineChanged": False, "migrations": [],
        }), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Release 1.0.1")

    def invoke(self, *args: str) -> int:
        return release.main(["publish", *args, "--root", str(self.root)])

    def test_confirmation_is_required_and_exact(self) -> None:
        for confirm in ([], ["--confirm", "v1.0.2"]):
            with self.subTest(confirm=confirm), mock.patch.object(release, "validate") as validate:
                self.assertEqual(self.invoke(*confirm), 1)
                validate.assert_not_called()
                self.assertEqual(self.git("ls-remote", "--tags", "origin").stdout, "")

    def test_preconditions_refuse_without_push(self) -> None:
        cases = [
            ("branch", lambda: self.git("checkout", "-qb", "feature"), "current branch"),
            ("dirty", lambda: (self.root / "dirty").write_text("x", encoding="utf-8"), "working tree"),
            ("versions", lambda: ((self.root / ".claude-plugin/plugin.json").write_text('{"version": "1.0.2"}\n', encoding="utf-8"), self.git("add", "."), self.git("commit", "-qm", "wrong version")), "must agree"),
            ("ledger-tag", lambda: ((self.root / "releases/1.0.1.json").write_text(json.dumps({"version": "1.0.1", "gitTag": "v1.0.2", "baselineChanged": False, "migrations": []}), encoding="utf-8"), self.git("add", "."), self.git("commit", "-qm", "wrong tag")), "gitTag"),
            ("cli-migrations", lambda: ((self.root / "releases/1.0.1.json").write_text(json.dumps({"version": "1.0.1", "gitTag": "v1.0.1", "baselineChanged": False, "migrations": ["001-test"]}), encoding="utf-8"), self.git("add", "."), self.git("commit", "-qm", "wrong migrations")), "CLI-only"),
            ("local-tag", lambda: self.git("tag", "v1.0.1"), "local tag"),
            ("remote-tag", lambda: (self.git("tag", "v1.0.1"), self.git("push", "origin", "v1.0.1"), self.git("tag", "-d", "v1.0.1")), "origin tag"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name), mock.patch("sys.stderr") as stderr:
                mutate()
                self.assertEqual(self.invoke("--confirm", "v1.0.1"), 1)
                self.assertIn(expected, "".join(str(call) for call in stderr.write.call_args_list))
            self.tearDown()
            self.setUp()

    def test_template_changing_release_and_multi_commit_publish(self) -> None:
        (self.root / "migrations").mkdir()
        (self.root / "migrations/001-test.json").write_text('{"id": "001-test", "to": "1.0.1"}', encoding="utf-8")
        (self.root / "releases/1.0.1.json").write_text(json.dumps({
            "version": "1.0.1", "gitTag": "v1.0.1", "baselineChanged": True, "migrations": ["001-test"],
        }), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Add release migration")
        self.git("commit", "--allow-empty", "-qm", "Document release migration")
        output = io.StringIO()
        with mock.patch.object(release, "validate", return_value=(0, [])), redirect_stdout(output):
            self.assertEqual(self.invoke("--confirm", "v1.0.1", "--no-wait"), 0)
        text = output.getvalue()
        self.assertIn("Template-changing release", text)
        self.assertIn("Migrations: 001-test", text)
        self.assertIn("Add release migration", text)
        self.assertIn("Document release migration", text)

    def test_template_changing_ledger_migration_must_exist_and_target_version(self) -> None:
        (self.root / "migrations").mkdir()
        (self.root / "migrations/001-test.json").write_text('{"id": "001-test", "to": "1.0.2"}', encoding="utf-8")
        (self.root / "releases/1.0.1.json").write_text(json.dumps({
            "version": "1.0.1", "gitTag": "v1.0.1", "baselineChanged": True, "migrations": ["001-test"],
        }), encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Wrong migration target")
        with mock.patch("sys.stderr") as stderr:
            self.assertEqual(self.invoke("--confirm", "v1.0.1"), 1)
        self.assertIn("must exist and target 1.0.1", "".join(str(call) for call in stderr.write.call_args_list))

    def test_origin_must_be_parent_of_release_commit(self) -> None:
        self.git("checkout", "-qb", "other", "origin/main")
        self.git("commit", "--allow-empty", "-qm", "ahead")
        self.git("push", "-q", "origin", "HEAD:main")
        self.git("checkout", "-q", "main")
        self.git("fetch", "-q", "origin")
        self.assertEqual(self.invoke("--confirm", "v1.0.1"), 1)

    def test_push_order_and_no_forbidden_git_flags(self) -> None:
        commands: list[list[str]] = []
        original_run_command = release.run_command
        original_run_git = release.run_git

        def record_command(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            return original_run_command(root, command)

        def record_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
            commands.append(["git", *args])
            return original_run_git(root, *args)

        with mock.patch.object(release, "validate", return_value=(0, [])), mock.patch.object(release, "run_command", side_effect=record_command), mock.patch.object(release, "run_git", side_effect=record_git):
            self.assertEqual(self.invoke("--confirm", "v1.0.1", "--no-wait"), 0)
        pushes = [command for command in commands if command[:2] == ["git", "push"]]
        self.assertEqual(pushes, [["git", "push", "origin", "main"], ["git", "push", "origin", "v1.0.1"]])
        self.assertFalse(any(flag in command for command in commands for flag in ("--force", "--force-with-lease", "--delete")))

    def test_rejected_main_push_stops_before_tag(self) -> None:
        original = release.run_command

        def reject_main(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
            if command == ["git", "push", "origin", "main"]:
                return subprocess.CompletedProcess(command, 1, "", "rejected")
            return original(root, command)

        with mock.patch.object(release, "validate", return_value=(0, [])), mock.patch.object(release, "run_command", side_effect=reject_main):
            self.assertEqual(self.invoke("--confirm", "v1.0.1", "--no-wait"), 1)
        self.assertEqual(self.git("tag", "--list", "v1.0.1").stdout, "")

    def test_validation_failure_stops_before_push(self) -> None:
        with mock.patch.object(release, "validate", return_value=(9, ["validation", "failed"])):
            self.assertEqual(self.invoke("--confirm", "v1.0.1", "--no-wait"), 1)
        self.assertEqual(self.git("ls-remote", "--heads", "origin", "main").stdout.count("refs/heads/main"), 1)
        self.assertEqual(self.git("tag", "--list", "v1.0.1").stdout, "")

    def test_no_wait_and_missing_gh_paths(self) -> None:
        with mock.patch.object(release, "validate", return_value=(0, [])):
            self.assertEqual(self.invoke("--confirm", "v1.0.1", "--no-wait"), 0)
        self.tearDown()
        self.setUp()
        with mock.patch.object(release, "validate", return_value=(0, [])), mock.patch.object(release.shutil, "which", return_value=None):
            self.assertEqual(self.invoke("--confirm", "v1.0.1"), 0)

    def test_workflow_failure_does_not_move_tag(self) -> None:
        original = release.run_command

        def gh(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
            if command[:3] == ["gh", "run", "list"]:
                return subprocess.CompletedProcess(command, 0, '[{"databaseId": "4", "url": "https://example.invalid/run/4"}]', "")
            if command[:3] == ["gh", "run", "watch"]:
                return subprocess.CompletedProcess(command, 1, "", "failed")
            return original(root, command)

        with mock.patch.object(release, "validate", return_value=(0, [])), mock.patch.object(release.shutil, "which", return_value="gh"), mock.patch.object(release, "run_command", side_effect=gh):
            self.assertEqual(self.invoke("--confirm", "v1.0.1"), 1)
        self.assertEqual(self.git("rev-parse", "v1.0.1").stdout.strip(), self.git("rev-parse", "HEAD").stdout.strip())


if __name__ == "__main__":
    unittest.main()
