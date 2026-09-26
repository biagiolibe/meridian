"""End-to-end Git evidence for the task-worktree delivery contract."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
