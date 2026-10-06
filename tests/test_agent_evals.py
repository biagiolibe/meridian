"""Grader and safety-guard tests for the agent evaluation harness; no agent is ever started."""

from __future__ import annotations

import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_agent_evals  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "agent_evals"
SCENARIO = ROOT / "evals" / "scenarios" / "main-ahead-integrates"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class GraderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.expect = load(SCENARIO / "expect.json")

    def grade(self, name: str) -> tuple[bool, list[str]]:
        return run_agent_evals.grade(load(FIXTURES / f"main-ahead-integrates-{name}.json"), self.expect)

    def test_recorded_successful_integration_passes(self) -> None:
        self.assertEqual(self.grade("pass"), (True, []))

    def test_main_behind_origin_stop_fails_and_names_the_stop(self) -> None:
        passed, reasons = self.grade("main-behind-origin")
        self.assertFalse(passed)
        self.assertIn('journal holds forbidden {"stop_code": "MAIN_BEHIND_ORIGIN"}', reasons)
        self.assertIn('journal lacks {"command": "integrate finalize", "result": "ok"}', reasons)

    def test_finalize_without_the_push_fails(self) -> None:
        passed, reasons = self.grade("not-pushed")
        self.assertFalse(passed)
        self.assertEqual(reasons, ["origin main lacks GREETING.md", "origin main differs from local main"])

    def test_a_tag_on_origin_fails(self) -> None:
        snapshot = load(FIXTURES / "main-ahead-integrates-pass.json")
        snapshot["origin_refs"]["refs/tags/v1"] = "0" * 40
        passed, reasons = run_agent_evals.grade(snapshot, self.expect)
        self.assertFalse(passed)
        self.assertEqual(reasons, ["origin holds tags ['refs/tags/v1']"])

    def test_dirty_primary_checkout_fails(self) -> None:
        snapshot = load(FIXTURES / "main-ahead-integrates-pass.json")
        snapshot["primary_status"] = " M tasks/QUEUE.md\n"
        self.assertFalse(run_agent_evals.grade(snapshot, self.expect)[0])

    def test_journal_patterns_match_partially_and_never_on_agent_text(self) -> None:
        snapshot = load(FIXTURES / "main-ahead-integrates-pass.json")
        snapshot["agent_text"] = "BLOCKED MAIN_BEHIND_ORIGIN"
        self.assertTrue(run_agent_evals.grade(snapshot, self.expect)[0])

    def test_expect_validation_rejects_ignored_keys(self) -> None:
        run_agent_evals.validate_expect(self.expect)
        for change in ({"kind": "other"}, {"surprise": 1}):
            with self.subTest(change=change), self.assertRaises(run_agent_evals.EvalError):
                run_agent_evals.validate_expect({**copy.deepcopy(self.expect), **change})
        broken = copy.deepcopy(self.expect)
        broken["git"]["unknown_assertion"] = True
        with self.assertRaises(run_agent_evals.EvalError):
            run_agent_evals.validate_expect(broken)

    def test_the_first_scenario_is_a_progress_scenario_with_its_files(self) -> None:
        self.assertEqual(self.expect["kind"], "progress")
        for name in ("setup.sh", "prompt.txt", "expect.json"):
            self.assertTrue((SCENARIO / name).is_file(), name)
        scenarios = run_agent_evals.load_scenarios(["main-ahead-integrates"])
        self.assertEqual(scenarios[0].prompt, "Proceed with 901")


class SafetyGuardTest(unittest.TestCase):
    def test_only_absolute_local_paths_are_local(self) -> None:
        for url in ("/tmp/x/origin.git", "/private/var/folders/a b/origin.git"):
            self.assertTrue(run_agent_evals.is_local_path(url), url)
        for url in (
            "https://github.com/o/r.git", "git@github.com:o/r.git", "ssh://host/r.git",
            "file:///tmp/x.git", "relative/origin.git", "../origin.git", "host:/srv/r.git", "",
        ):
            self.assertFalse(run_agent_evals.is_local_path(url), url)

    def test_origin_guard_refuses_remote_and_outside_origins(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            fixture = root / "fixture"
            subprocess.run(["git", "init", "-q", str(fixture)], check=True)
            guard = lambda: run_agent_evals.check_fixture_origin(fixture, root)  # noqa: E731
            with self.assertRaises(run_agent_evals.EvalError):
                guard()  # no origin at all
            subprocess.run(["git", "remote", "add", "origin", "https://example.invalid/r.git"], cwd=fixture, check=True)
            with self.assertRaises(run_agent_evals.EvalError):
                guard()
            subprocess.run(["git", "remote", "set-url", "origin", str(Path(directory).parent / "elsewhere.git")], cwd=fixture, check=True)
            with self.assertRaises(run_agent_evals.EvalError):
                guard()
            inside = root / "origin.git"
            subprocess.run(["git", "remote", "set-url", "origin", str(inside)], cwd=fixture, check=True)
            self.assertEqual(guard(), inside)


class HostAvailabilityTest(unittest.TestCase):
    def test_a_missing_host_cli_is_unavailable_and_never_a_pass(self) -> None:
        with mock.patch.object(run_agent_evals.shutil, "which", return_value=None):
            with self.assertRaises(run_agent_evals.HostUnavailable) as caught:
                run_agent_evals.check_host("claude")
            self.assertIn("claude CLI is not on PATH", str(caught.exception))
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                status = run_agent_evals.main(["--host", "codex"])
            self.assertEqual(status, run_agent_evals.EXIT_UNAVAILABLE)
            self.assertIn("UNAVAILABLE: the codex CLI is not on PATH", stderr.getvalue())

    def test_missing_credentials_are_unavailable(self) -> None:
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="")
        with mock.patch.object(run_agent_evals.shutil, "which", return_value="/bin/codex"), mock.patch.object(
            run_agent_evals.subprocess, "run", return_value=failed
        ):
            with self.assertRaises(run_agent_evals.HostUnavailable):
                run_agent_evals.check_host("codex")
        signed_out = subprocess.CompletedProcess([], 0, stdout='{"loggedIn": false}', stderr="")
        with mock.patch.object(run_agent_evals.shutil, "which", return_value="/bin/claude"), mock.patch.object(
            run_agent_evals.subprocess, "run", return_value=signed_out
        ):
            with self.assertRaises(run_agent_evals.HostUnavailable):
                run_agent_evals.check_host("claude")

    def test_invocations_use_headless_modes_and_confine_codex_writes(self) -> None:
        root, fixture = Path("/tmp/root"), Path("/tmp/root/fixture")
        claude = run_agent_evals.host_command("claude", "go", fixture, root, "5")
        self.assertEqual(claude[:3], ["claude", "-p", "go"])
        self.assertIn("project,local", claude)
        codex = run_agent_evals.host_command("codex", "go", fixture, root, "5")
        self.assertEqual(codex[:2], ["codex", "exec"])
        self.assertIn("--ignore-user-config", codex)
        self.assertIn("workspace-write", codex)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", codex)


if __name__ == "__main__":
    unittest.main()
