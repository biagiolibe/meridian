"""End-to-end Git evidence for the task-worktree delivery contract."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import json
import os
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import meridian  # noqa: E402


class TaskWorktreeIsolationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.primary = self.root / "project"
        self.primary.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Meridian Test")
        self.git("config", "user.email", "meridian@example.invalid")
        (self.primary / "QUEUE.md").write_text(
            "Task 051: TODO\n"
            + "\n".join(f"shared context {index}" for index in range(10))
            + "\nTask 052: TODO\n",
            encoding="utf-8",
        )
        self.git("add", "QUEUE.md")
        self.git("commit", "-m", "initial")
        self.base = self.git("rev-parse", "main").stdout.strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(
        self, *arguments: str, cwd: Path | None = None, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.primary,
            text=True,
            capture_output=True,
            check=check,
        )

    def create_task(self, task_id: str) -> Path:
        worktree = self.root / f"project-{task_id}"
        self.git("worktree", "add", "-b", task_id, str(worktree), "main")
        return worktree

    def commit_task(self, worktree: Path, task_id: str, queue_change: tuple[str, str]) -> str:
        queue = worktree / "QUEUE.md"
        queue.write_text(
            queue.read_text(encoding="utf-8").replace(*queue_change), encoding="utf-8"
        )
        (worktree / f"{task_id}.txt").write_text(f"isolated {task_id}\n", encoding="utf-8")
        self.git("add", "QUEUE.md", f"{task_id}.txt", cwd=worktree)
        self.git("commit", "-m", f"complete {task_id}", cwd=worktree)
        return self.git("rev-parse", "HEAD", cwd=worktree).stdout.strip()

    def integrate(self, branch: str) -> str:
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        merged = self.git("merge", "--no-ff", "--no-commit", branch, check=False)
        self.assertEqual(merged.returncode, 0, merged.stdout + merged.stderr)
        self.git("commit", "-m", f"integrate {branch}")
        return self.git("rev-parse", "HEAD").stdout.strip()

    def validation_decision(
        self,
        task_commit: str,
        *,
        validated_task_commit: str | None = None,
        current_main: str | None = None,
        full_required: bool = False,
        assessment_complete: bool = True,
        task_paths: tuple[str, ...] = ("feature.txt",),
        main_paths: tuple[str, ...] = (),
        task_dependencies: tuple[str, ...] = (),
        main_dependencies: tuple[str, ...] = (),
        task_surfaces: tuple[str, ...] = (),
        main_surfaces: tuple[str, ...] = (),
    ) -> meridian.IntegrationValidationDecision:
        return meridian.decide_integration_validation(
            evidence_complete=True,
            validated_task_commit=validated_task_commit or task_commit,
            current_task_commit=task_commit,
            validated_base_commit=self.base,
            current_main_commit=current_main or self.git("rev-parse", "main").stdout.strip(),
            validated_base_is_task_ancestor=True,
            full_validation_required=full_required,
            interaction_assessment_complete=assessment_complete,
            task_paths=task_paths,
            main_advanced_paths=main_paths,
            task_dependencies=task_dependencies,
            main_advanced_dependencies=main_dependencies,
            task_behavioral_surfaces=task_surfaces,
            main_advanced_behavioral_surfaces=main_surfaces,
        )

    def run_candidate_gate(
        self,
        branch: str,
        decision: meridian.IntegrationValidationDecision,
        *,
        smoke_command: tuple[str, ...] | None = None,
    ) -> tuple[bool, list[str]]:
        invoked: list[str] = []
        merged = self.git("merge", "--no-ff", "--no-commit", branch, check=False)
        if merged.returncode != 0:
            self.git("merge", "--abort")
            return False, invoked
        diff_check = self.git("diff", "--check", check=False)
        invoked.append("git diff --check")
        passed = diff_check.returncode == 0
        if passed and smoke_command is not None:
            invoked.append("smoke")
            passed = subprocess.run(smoke_command, cwd=self.primary, check=False).returncode == 0
        if passed and decision.outcome == meridian.IntegrationValidationOutcome.FULL:
            invoked.append("complete baseline")
        if not passed:
            self.git("merge", "--abort")
        return passed, invoked

    def test_two_tasks_remain_isolated_and_integrate_serially(self) -> None:
        first = self.create_task("task-051")
        second = self.create_task("task-052")
        first_commit = self.commit_task(first, "task-051", ("Task 051: TODO", "Task 051: DONE"))
        second_commit = self.commit_task(second, "task-052", ("Task 052: TODO", "Task 052: DONE"))

        first_before = (first / "QUEUE.md").read_text(encoding="utf-8")
        second_before = (second / "QUEUE.md").read_text(encoding="utf-8")
        self.git("switch", "-c", "coordination")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=first).stdout.strip(), first_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=second).stdout.strip(), second_commit)
        self.assertEqual((first / "QUEUE.md").read_text(encoding="utf-8"), first_before)
        self.assertEqual((second / "QUEUE.md").read_text(encoding="utf-8"), second_before)
        self.git("switch", "main")

        first_merge = self.integrate("task-051")
        self.assertNotEqual(
            self.git("merge-base", "--is-ancestor", first_merge, "task-052", check=False).returncode,
            0,
            "the second task deliberately starts from the old main",
        )
        second_merge = self.integrate("task-052")

        queue = (self.primary / "QUEUE.md").read_text(encoding="utf-8")
        self.assertIn("Task 051: DONE", queue)
        self.assertIn("Task 052: DONE", queue)
        self.assertTrue((self.primary / "task-051.txt").is_file())
        self.assertTrue((self.primary / "task-052.txt").is_file())
        for task_commit in (first_commit, second_commit):
            self.assertEqual(
                self.git("merge-base", "--is-ancestor", task_commit, second_merge).returncode,
                0,
            )
        self.assertEqual(len(self.git("rev-list", "--parents", "-n", "1", second_merge).stdout.split()), 3)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=first).stdout.strip(), first_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=second).stdout.strip(), second_commit)

    def test_conflicting_integration_aborts_and_preserves_task_state(self) -> None:
        first = self.create_task("task-051")
        second = self.create_task("task-052")
        first_commit = self.commit_task(first, "task-051", ("shared context 5", "first task value"))
        second_commit = self.commit_task(second, "task-052", ("shared context 5", "second task value"))
        self.integrate("task-051")

        conflicted = self.git("merge", "--no-ff", "--no-commit", "task-052", check=False)
        self.assertNotEqual(conflicted.returncode, 0)
        self.git("merge", "--abort")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual(self.git("rev-parse", "task-051").stdout.strip(), first_commit)
        self.assertEqual(self.git("rev-parse", "task-052").stdout.strip(), second_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=second).stdout.strip(), second_commit)
        self.assertIn("second task value", (second / "QUEUE.md").read_text(encoding="utf-8"))

    def test_unchanged_base_reuses_evidence_without_complete_baseline(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        decision = self.validation_decision(task_commit)

        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.REUSE)
        passed, invoked = self.run_candidate_gate("task-055", decision)
        self.assertTrue(passed)
        self.assertEqual(invoked, ["git diff --check"])

    def test_advanced_main_independent_change_uses_bounded_gate(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        (self.primary / "independent.txt").write_text("main change\n", encoding="utf-8")
        self.git("add", "independent.txt")
        self.git("commit", "-m", "advance main independently")
        decision = self.validation_decision(task_commit, main_paths=("independent.txt",))

        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.BOUNDED)
        passed, invoked = self.run_candidate_gate("task-055", decision)
        self.assertTrue(passed)
        self.assertNotIn("complete baseline", invoked)

    def test_advanced_main_interacting_surface_requires_full_validation(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        (self.primary / "dependency.lock").write_text("main dependency\n", encoding="utf-8")
        self.git("add", "dependency.lock")
        self.git("commit", "-m", "advance shared dependency")
        decision = self.validation_decision(
            task_commit,
            main_paths=("dependency.lock",),
            task_dependencies=("runtime",),
            main_dependencies=("runtime",),
        )

        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.FULL)
        passed, invoked = self.run_candidate_gate("task-055", decision)
        self.assertTrue(passed)
        self.assertIn("complete baseline", invoked)

    def test_stale_task_commit_is_blocked_before_merge(self) -> None:
        task = self.create_task("task-055")
        validated_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        (task / "later.txt").write_text("changed after validation\n", encoding="utf-8")
        self.git("add", "later.txt", cwd=task)
        self.git("commit", "-m", "change after validation", cwd=task)
        current_commit = self.git("rev-parse", "HEAD", cwd=task).stdout.strip()

        decision = self.validation_decision(
            current_commit, validated_task_commit=validated_commit
        )
        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.BLOCKED)


class BoundedWorktreeLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.primary = self.root / "project"
        self.primary.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Meridian Test")
        self.git("config", "user.email", "meridian@example.invalid")
        tasks = self.primary / "tasks"
        tasks.mkdir()
        (tasks / "056-lifecycle.md").write_text(
            "# Task 056\n\n> **ID**: `056`\n", encoding="utf-8"
        )
        (tasks / "QUEUE.md").write_text(
            "| Status | ID | Title |\n|---|---|---|\n| `[ ]` | 056 | Lifecycle |\n",
            encoding="utf-8",
        )
        (self.primary / "QUEUE.md").write_text(
            "Task 051: TODO\nshared context\nTask 052: TODO\n", encoding="utf-8"
        )
        (self.primary / "PROJECT_PLAN.md").write_text(
            "- `[ ]` 056 — Lifecycle\n", encoding="utf-8"
        )
        (self.primary / "README.md").write_text("base\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.worktree_root = self.root / "worktrees"
        self.worktree_root.mkdir()
        self.previous_cwd = Path.cwd()
        os.chdir(self.primary)

    def tearDown(self) -> None:
        os.chdir(self.previous_cwd)
        self.temporary.cleanup()

    def git(self, *arguments: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd or self.primary,
            text=True,
            capture_output=True,
            check=check,
        )

    def prepare(self) -> dict[str, object]:
        return meridian.prepare_task_worktree("056", self.worktree_root, self.primary)

    def create_task(self, task_id: str) -> Path:
        worktree = self.root / f"project-{task_id}"
        self.git("worktree", "add", "-b", task_id, str(worktree), "main")
        return worktree

    def commit_task(self, worktree: Path, task_id: str, queue_change: tuple[str, str]) -> str:
        queue = worktree / "QUEUE.md"
        queue.write_text(queue.read_text(encoding="utf-8").replace(*queue_change), encoding="utf-8")
        (worktree / f"{task_id}.txt").write_text(f"isolated {task_id}\n", encoding="utf-8")
        self.git("add", "QUEUE.md", f"{task_id}.txt", cwd=worktree)
        self.git("commit", "-m", f"complete {task_id}", cwd=worktree)
        return self.git("rev-parse", "HEAD", cwd=worktree).stdout.strip()

    def validation_decision(
        self,
        task_commit: str,
        *,
        validated_task_commit: str | None = None,
        current_main: str | None = None,
        full_required: bool = False,
        assessment_complete: bool = True,
        task_paths: tuple[str, ...] = ("feature.txt",),
        main_paths: tuple[str, ...] = (),
        task_dependencies: tuple[str, ...] = (),
        main_dependencies: tuple[str, ...] = (),
        task_surfaces: tuple[str, ...] = (),
        main_surfaces: tuple[str, ...] = (),
    ) -> meridian.IntegrationValidationDecision:
        return meridian.decide_integration_validation(
            evidence_complete=True,
            validated_task_commit=validated_task_commit or task_commit,
            current_task_commit=task_commit,
            validated_base_commit=self.base,
            current_main_commit=current_main or self.git("rev-parse", "main").stdout.strip(),
            validated_base_is_task_ancestor=True,
            full_validation_required=full_required,
            interaction_assessment_complete=assessment_complete,
            task_paths=task_paths,
            main_advanced_paths=main_paths,
            task_dependencies=task_dependencies,
            main_advanced_dependencies=main_dependencies,
            task_behavioral_surfaces=task_surfaces,
            main_advanced_behavioral_surfaces=main_surfaces,
        )

    def run_candidate_gate(
        self,
        branch: str,
        decision: meridian.IntegrationValidationDecision,
        *,
        smoke_command: tuple[str, ...] | None = None,
    ) -> tuple[bool, list[str]]:
        invoked: list[str] = []
        merged = self.git("merge", "--no-ff", "--no-commit", branch, check=False)
        if merged.returncode != 0:
            self.git("merge", "--abort")
            return False, invoked
        invoked.append("git diff --check")
        passed = self.git("diff", "--check", check=False).returncode == 0
        if passed and smoke_command is not None:
            invoked.append("smoke")
            passed = subprocess.run(smoke_command, cwd=self.primary, check=False).returncode == 0
        if passed and decision.outcome == meridian.IntegrationValidationOutcome.FULL:
            invoked.append("complete baseline")
        if not passed:
            self.git("merge", "--abort")
        return passed, invoked

    def test_prepare_is_idempotent_and_check_rejects_wrong_worker(self) -> None:
        prepared = self.prepare()
        self.assertTrue(prepared["created"])
        repeated = self.prepare()
        self.assertFalse(repeated["created"])
        self.assertEqual(prepared["worktree"], repeated["worktree"])

        wrong, ready = meridian.inspect_task_worktree("056", self.worktree_root, self.primary)
        self.assertFalse(ready)
        self.assertIn("wrong-worktree", wrong["errors"])

        os.chdir(Path(str(prepared["worktree"])))
        correct, ready = meridian.inspect_task_worktree("056", self.worktree_root, self.primary)
        self.assertTrue(ready, correct)
        self.assertEqual(correct["branch"], "task-056")
        self.assertTrue(correct["clean"])

    def test_stage_finalize_and_verified_cleanup(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        task_commit = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(
            json.dumps({
                "accepted": True,
                "validation_passed": True,
                "validated_task_commit": task_commit,
                "validated_base_commit": self.base,
                "full_validation_required": False,
                "interaction_assessment_complete": True,
                "task_paths": ["feature.txt"],
                "task_dependencies": [],
                "task_behavioral_surfaces": ["feature behavior"],
                "main_advanced_dependencies": [],
                "main_advanced_behavioral_surfaces": [],
            }),
            encoding="utf-8",
        )
        staged = meridian.stage_task_integration(
            "056", self.worktree_root, evidence_path, self.primary
        )
        self.assertEqual(staged["decision"], "REUSE")
        self.assertEqual(
            meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary),
            staged,
        )
        validation_path = self.root / "candidate-validation.json"
        validation_path.write_text(
            json.dumps({
                "candidate_tree": staged["candidate_tree"],
                "passed": True,
                "scope": "bounded",
                "commands": ["git diff --check"],
            }),
            encoding="utf-8",
        )
        finalized = meridian.finalize_task_integration("056", validation_path, self.primary)
        self.assertEqual(finalized["decision"], "REUSE")
        self.assertTrue((self.primary / "feature.txt").is_file())
        cleaned = meridian.cleanup_task_worktree("056", self.worktree_root, self.primary)
        self.assertEqual(cleaned["status"], "cleaned")
        self.assertFalse(task_worktree.exists())
        self.assertNotEqual(self.git("show-ref", "--verify", "refs/heads/task-056", check=False).returncode, 0)
        repeated = meridian.cleanup_task_worktree("056", self.worktree_root, self.primary)
        self.assertTrue(repeated["already_cleaned"])

    def test_evidence_command_records_git_facts_without_running_validation(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        previous = Path.cwd()
        try:
            os.chdir(task_worktree)
            recorded = meridian.record_task_evidence(
                "056", self.worktree_root, ["python3 -m unittest"], [0],
                accepted=True,
                task_dependencies=[], task_behavioral_surfaces=[],
                main_advanced_dependencies=[], main_advanced_behavioral_surfaces=[],
                full_validation_required=False, supplied_project=self.primary,
            )
        finally:
            os.chdir(previous)
        evidence = json.loads(Path(str(recorded["evidence"])).read_text(encoding="utf-8"))
        self.assertEqual(evidence["validated_task_commit"], self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip())
        self.assertEqual(evidence["validated_base_commit"], self.base)
        self.assertEqual(evidence["task_paths"], ["feature.txt"])
        self.assertEqual(evidence["validation_commands"], ["python3 -m unittest"])
        self.assertEqual(evidence["validation_exit_codes"], [0])

    def test_stage_recomputes_main_path_overlap_to_require_full_validation(self) -> None:
        (self.primary / "feature.txt").write_text("first\nmiddle\nlast\n", encoding="utf-8")
        self.git("add", "feature.txt")
        self.git("commit", "-m", "add feature base")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("task\nmiddle\nlast\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        task_commit = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        (self.primary / "feature.txt").write_text("first\nmiddle\nmain\n", encoding="utf-8")
        self.git("add", "feature.txt")
        self.git("commit", "-m", "advance main")
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True, "validation_passed": True,
            "validated_task_commit": task_commit, "validated_base_commit": self.base,
            "full_validation_required": False, "interaction_assessment_complete": True,
            "task_paths": [], "task_dependencies": [], "task_behavioral_surfaces": [],
            "main_advanced_dependencies": [], "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")
        staged = meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        self.assertEqual(staged["decision"], "FULL")
        self.assertEqual(staged["main_advanced_paths"], ["feature.txt"])
        meridian.abort_task_integration("056", self.primary)

    def test_stage_keeps_independent_main_advance_bounded(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("task\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        task_commit = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        (self.primary / "independent.txt").write_text("main\n", encoding="utf-8")
        self.git("add", "independent.txt")
        self.git("commit", "-m", "advance main independently")
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True, "validation_passed": True,
            "validated_task_commit": task_commit, "validated_base_commit": self.base,
            "full_validation_required": False, "interaction_assessment_complete": True,
            "task_paths": ["feature.txt"], "task_dependencies": [], "task_behavioral_surfaces": [],
            "main_advanced_dependencies": [], "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")
        staged = meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        self.assertEqual(staged["decision"], "BOUNDED")
        meridian.abort_task_integration("056", self.primary)

    def test_stage_completes_rows_after_main_registration_advance(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        task_commit = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        queue = self.primary / "tasks/QUEUE.md"
        queue.write_text(
            queue.read_text(encoding="utf-8") + "".join(
                f"| `[ ]` | {index:03d} | Registered |\n" for index in range(10)
            ),
            encoding="utf-8",
        )
        plan = self.primary / "PROJECT_PLAN.md"
        plan.write_text(
            plan.read_text(encoding="utf-8") + "- `[ ]` 999 — Registered\n",
            encoding="utf-8",
        )
        self.git("add", "tasks/QUEUE.md", "PROJECT_PLAN.md")
        self.git("commit", "-m", "register tasks on main")
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True, "validation_passed": True,
            "validated_task_commit": task_commit, "validated_base_commit": self.base,
            "full_validation_required": False, "interaction_assessment_complete": True,
            "task_paths": ["feature.txt"], "task_dependencies": [],
            "task_behavioral_surfaces": [], "main_advanced_dependencies": [],
            "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")

        staged = meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        self.assertEqual(staged["decision"], "BOUNDED")
        self.assertIn("| `[x]` | 056 | Lifecycle |", queue.read_text(encoding="utf-8"))
        self.assertIn("- `[x]` 056 — Lifecycle", plan.read_text(encoding="utf-8"))
        meridian.abort_task_integration("056", self.primary)

    def test_stage_accepts_exact_task_record_archive_after_validation(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        validated_task = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()

        queue = task_worktree / "tasks/QUEUE.md"
        queue.write_text(queue.read_text(encoding="utf-8").replace("`[ ]`", "`[x]`"), encoding="utf-8")
        plan = task_worktree / "PROJECT_PLAN.md"
        plan.write_text("- `[x]` 056 — Lifecycle\n", encoding="utf-8")
        handoff = task_worktree / "tasks/handoffs/056.md"
        handoff.parent.mkdir()
        handoff.write_text("validated\n", encoding="utf-8")
        archive = task_worktree / "tasks/done"
        archive.mkdir()
        self.git("mv", "tasks/056-lifecycle.md", "tasks/done/056-lifecycle.md", cwd=task_worktree)
        self.git("add", "tasks/QUEUE.md", "PROJECT_PLAN.md", "tasks/handoffs/056.md", cwd=task_worktree)
        self.git("commit", "-m", "close task", cwd=task_worktree)

        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True,
            "validation_passed": True,
            "validated_task_commit": validated_task,
            "validated_base_commit": self.base,
            "full_validation_required": False,
            "interaction_assessment_complete": True,
            "task_paths": ["feature.txt"],
            "task_dependencies": [],
            "task_behavioral_surfaces": [],
            "main_advanced_dependencies": [],
            "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")

        staged = meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        self.assertEqual(staged["decision"], "REUSE")
        meridian.abort_task_integration("056", self.primary)

    def test_lifecycle_change_parser_rejects_inexact_task_record_changes(self) -> None:
        identity = meridian.resolve_task_identity(self.primary, "056", "existing")
        active = "tasks/056-lifecycle.md"
        archive = "tasks/done/056-lifecycle.md"
        invalid_diffs = {
            "deletion": f"D\0{active}\0",
            "separate archive addition": f"A\0{archive}\0",
            "changed-content rename": f"R099\0{active}\0{archive}\0",
            "wrong archive destination": f"R100\0{active}\0tasks/done/other.md\0",
            "different task path": "A\0tasks/done/057-other.md\0",
        }
        for label, diff in invalid_diffs.items():
            with self.subTest(label=label), mock.patch.object(
                meridian,
                "_run_git",
                side_effect=(
                    subprocess.CompletedProcess([], 0, diff, ""),
                    subprocess.CompletedProcess([], 1, "", ""),
                ),
            ):
                unchanged, offending = meridian._lifecycle_changes_after_validation(
                    self.primary, identity, "validated", "current"
                )
                self.assertFalse(unchanged)
                self.assertTrue(offending)

    def test_completion_rows_reject_unknown_shape_without_editing_queue(self) -> None:
        identity = meridian.resolve_task_identity(self.primary, "056", "existing")
        queue = self.primary / "tasks/QUEUE.md"
        original_queue = queue.read_text(encoding="utf-8")
        (self.primary / "PROJECT_PLAN.md").write_text("Task 056: TODO\n", encoding="utf-8")

        with self.assertRaisesRegex(meridian.MeridianError, r"unrecognized completion row"):
            meridian._apply_task_completion_rows(self.primary, identity)

        self.assertEqual(queue.read_text(encoding="utf-8"), original_queue)

    def test_stage_blocks_invalid_archive_before_creating_lifecycle_state(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        validated_task = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        archive = task_worktree / "tasks/done"
        archive.mkdir()
        self.git("mv", "tasks/056-lifecycle.md", "tasks/done/other.md", cwd=task_worktree)
        self.git("commit", "-am", "archive to wrong destination", cwd=task_worktree)
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True, "validation_passed": True,
            "validated_task_commit": validated_task, "validated_base_commit": self.base,
            "full_validation_required": False, "interaction_assessment_complete": True,
            "task_paths": ["feature.txt"], "task_dependencies": [],
            "task_behavioral_surfaces": [], "main_advanced_dependencies": [],
            "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")
        identity = meridian.resolve_task_identity(self.primary, "056", "existing")
        state_path, lease_path, integration_path = meridian._lifecycle_paths(self.primary, identity)
        references = self.git("show-ref").stdout
        worktree_state = state_path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(meridian.MeridianError, r"paths changed after validation: .*other.md"):
            meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertEqual(self.git("show-ref").stdout, references)
        self.assertEqual(state_path.read_text(encoding="utf-8"), worktree_state)
        self.assertFalse(lease_path.exists())
        self.assertFalse(integration_path.exists())
        self.assertFalse((self.primary / ".git/MERGE_HEAD").exists())

    def test_abort_requires_owned_state_and_preserves_task(self) -> None:
        prepared = self.prepare()
        task_worktree = Path(str(prepared["worktree"]))
        (task_worktree / "feature.txt").write_text("implemented\n", encoding="utf-8")
        self.git("add", "feature.txt", cwd=task_worktree)
        self.git("commit", "-m", "implement task", cwd=task_worktree)
        task_commit = self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip()
        evidence_path = self.root / "integration-evidence.json"
        evidence_path.write_text(json.dumps({
            "accepted": True,
            "validation_passed": True,
            "validated_task_commit": task_commit,
            "validated_base_commit": self.base,
            "full_validation_required": False,
            "interaction_assessment_complete": True,
            "task_paths": ["feature.txt"],
            "task_dependencies": [],
            "task_behavioral_surfaces": [],
            "main_advanced_dependencies": [],
            "main_advanced_behavioral_surfaces": [],
        }), encoding="utf-8")
        meridian.stage_task_integration("056", self.worktree_root, evidence_path, self.primary)
        aborted = meridian.abort_task_integration("056", self.primary)
        self.assertEqual(aborted["status"], "aborted")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=task_worktree).stdout.strip(), task_commit)

    def test_abort_recovers_an_owned_lease_before_merge_state_exists(self) -> None:
        self.prepare()
        identity = meridian.resolve_task_identity(self.primary, "056", "existing")
        _task_state, lease_path, integration_path = meridian._lifecycle_paths(self.primary, identity)
        meridian._write_json_atomic(
            lease_path,
            {"version": 1, "task_id": "056", "branch": "task-056", "project": str(self.primary)},
            exclusive=True,
        )
        self.assertFalse(integration_path.exists())
        recovered = meridian.abort_task_integration("056", self.primary)
        self.assertEqual(recovered["status"], "aborted")
        self.assertFalse(lease_path.exists())
        self.assertEqual(self.git("rev-parse", "HEAD").stdout.strip(), self.base)

    def test_abort_recovers_when_the_queue_link_is_stale(self) -> None:
        self.prepare()
        identity = meridian.resolve_task_identity(self.primary, "056", "existing")
        _task_state, lease_path, _integration_path = meridian._lifecycle_paths(self.primary, identity)
        meridian._write_json_atomic(
            lease_path,
            {"version": 1, "task_id": "056", "branch": "task-056", "project": str(self.primary)},
            exclusive=True,
        )
        queue = self.primary / "tasks/QUEUE.md"
        queue.write_text(
            queue.read_text(encoding="utf-8").replace(
                "| 056 |", "| [056](missing/056-lifecycle.md) |"
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(meridian.MeridianError, "queue link for task 056"):
            meridian.resolve_task_identity(self.primary, "056", "existing")
        recovered = meridian.abort_task_integration("056", self.primary)
        self.assertEqual(recovered["status"], "aborted")
        self.assertFalse(lease_path.exists())

    def test_missing_validation_evidence_is_blocked(self) -> None:
        decision = meridian.decide_integration_validation(
            evidence_complete=False,
            validated_task_commit="",
            current_task_commit="task",
            validated_base_commit=self.base,
            current_main_commit=self.base,
            validated_base_is_task_ancestor=True,
            full_validation_required=False,
        )
        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.BLOCKED)

    def test_governance_only_commit_after_validation_keeps_evidence_current(self) -> None:
        decision = meridian.decide_integration_validation(
            evidence_complete=True,
            validated_task_commit="validated",
            current_task_commit="accepted",
            validated_base_commit=self.base,
            current_main_commit=self.base,
            validated_base_is_task_ancestor=True,
            validated_task_is_current_ancestor=True,
            relevant_tree_unchanged_after_validation=True,
            full_validation_required=False,
        )
        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.REUSE)

    def test_missing_smoke_configuration_does_not_expand_gate(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        decision = self.validation_decision(task_commit)

        passed, invoked = self.run_candidate_gate("task-055", decision, smoke_command=None)
        self.assertTrue(passed)
        self.assertEqual(invoked, ["git diff --check"])

    def test_smoke_failure_aborts_clean_merge_and_retains_task(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        decision = self.validation_decision(task_commit)

        passed, invoked = self.run_candidate_gate("task-055", decision, smoke_command=("false",))
        self.assertFalse(passed)
        self.assertEqual(invoked, ["git diff --check", "smoke"])
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual(self.git("rev-parse", "task-055").stdout.strip(), task_commit)
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=task).stdout.strip(), task_commit)

    def test_task_can_require_full_combined_tree_validation(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        decision = self.validation_decision(task_commit, full_required=True)

        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.FULL)
        passed, invoked = self.run_candidate_gate("task-055", decision)
        self.assertTrue(passed)
        self.assertIn("complete baseline", invoked)

    def test_unknown_advanced_main_interaction_is_blocked(self) -> None:
        task = self.create_task("task-055")
        task_commit = self.commit_task(task, "task-055", ("Task 051: TODO", "Task 051: DONE"))
        (self.primary / "advance.txt").write_text("main change\n", encoding="utf-8")
        self.git("add", "advance.txt")
        self.git("commit", "-m", "advance main")

        decision = self.validation_decision(task_commit, assessment_complete=False)
        self.assertEqual(decision.outcome, meridian.IntegrationValidationOutcome.BLOCKED)


if __name__ == "__main__":
    unittest.main()
