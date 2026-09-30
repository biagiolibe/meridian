"""Read-only project console snapshot and output tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import project_console as console  # noqa: E402


HEADER = (
    "| Status | ID | Title | Priority | Depends on | File |\n"
    "|--------|----|-------|----------|------------|------|\n"
)


class ProjectConsoleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        (self.project / "tasks").mkdir()
        (self.project / "PROJECT_WORKFLOW.md").write_text("# LEAN_DELIVERY\n", encoding="utf-8")
        (self.project / "tasks" / "001-first.md").write_text(
            "# Task 001\n\n## Objective\n\nFirst task.\n\n"
            "## Acceptance Criteria\n\n- [ ] First check.\n", encoding="utf-8",
        )
        (self.project / "tasks" / "002-second.md").write_text(
            "# Task 002\n\n## Objective\n\nSecond task.\n\n"
            "## Acceptance Criteria\n\n- [ ] Second check.\n", encoding="utf-8",
        )

    def write_queue(self, dependency: str = "001", done: bool = True) -> None:
        first_status = "`[x]`" if done else "`[ ]`"
        (self.project / "tasks" / "QUEUE.md").write_text(
            "# Queue\n\n### Phase 1\n\n" + HEADER
            + f"| {first_status} | 001 | First | P2 | — | [001](001-first.md) |\n"
            + f"| `[ ]` | 002 | Second | P2 | {dependency} | [002](002-second.md) |\n",
            encoding="utf-8",
        )

    def snapshot(self) -> console.Snapshot:
        with mock.patch.object(console, "_git", side_effect=lambda _project, *args: (
            "## main...origin/main\n" if args[0] == "status"
            else "worktree /tmp/task-002\nbranch refs/heads/task-002\n"
        )):
            return console.load_snapshot(self.project)

    def test_completed_dependency_is_ready_and_task_details_are_loaded(self) -> None:
        self.write_queue()
        snapshot = self.snapshot()
        self.assertEqual([task.task_id for task in snapshot.tasks], ["002"])
        self.assertEqual(snapshot.tasks[0].readiness, "READY")
        self.assertEqual(snapshot.tasks[0].objective, ("Second task.",))
        self.assertEqual(snapshot.tasks[0].criteria, ("- [ ] Second check.",))
        self.assertEqual(snapshot.tasks[0].worktree, "/tmp/task-002")
        self.assertEqual(snapshot.tasks[0].next_action, "If assigned: Proceed with 002")

    def test_open_and_missing_dependencies_are_not_ready(self) -> None:
        self.write_queue(done=False)
        snapshot = self.snapshot()
        self.assertEqual(snapshot.tasks[1].readiness, "BLOCKED: 001")
        self.write_queue(dependency="999")
        snapshot = self.snapshot()
        self.assertEqual(snapshot.tasks[0].readiness, "UNKNOWN: missing 999")

    def test_refresh_failure_retains_last_valid_snapshot(self) -> None:
        self.write_queue()
        state = console.ConsoleState(self.project)
        with mock.patch.object(console, "_git", side_effect=lambda _project, *args: (
            "## main\n" if args[0] == "status" else ""
        )):
            state.refresh()
        previous = state.snapshot
        previous_time = state.last_success
        (self.project / "tasks" / "QUEUE.md").unlink()
        state.refresh()
        self.assertIs(state.snapshot, previous)
        self.assertEqual(state.last_success, previous_time)
        self.assertIsNotNone(state.error)

    def test_duplicate_task_id_is_rejected(self) -> None:
        self.write_queue()
        (self.project / "tasks" / "QUEUE_ARCHIVE.md").write_text(
            HEADER + "| `[x]` | 001 | Duplicate | P2 | — | [001](001-first.md) |\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(console.ConsoleError, "Duplicate task ID"):
            self.snapshot()

    def test_one_shot_against_repository(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "project_console.py"),
             "--project", str(ROOT), "--once"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("MERIDIAN |", result.stdout)
        self.assertIn("Updated:", result.stdout)
        self.assertIn("Open:", result.stdout)
        self.assertIn("Agent activity: unavailable", result.stdout)

    def test_detail_pane_keeps_the_approved_content_hierarchy(self) -> None:
        self.write_queue()
        task = self.snapshot().tasks[0]
        palette = {name: 0 for name in (
            "base", "text", "title", "ready", "muted", "line", "action"
        )}
        lines = [value for value, _ in console._detail_lines(task, 40, palette)]
        self.assertEqual(lines[0], "Task details")
        self.assertLess(lines.index("Objective"), lines.index("Dependencies"))
        self.assertLess(lines.index("Dependencies"), lines.index("Next directive"))
        self.assertNotIn("Acceptance criteria", lines)
        self.assertNotIn("- [ ] Second check.", lines)

    def test_header_right_aligns_git_and_underlines_active_all_tab(self) -> None:
        self.write_queue()
        state = console.ConsoleState(self.project)
        state.snapshot = self.snapshot()
        state.last_success = datetime.now().astimezone()
        screen = mock.Mock()
        screen.getmaxyx.return_value = (35, 140)
        palette = {name: 0 for name in (
            "text", "blocked", "stale", "tab", "ready", "working",
            "unknown", "muted", "line", "tab_underline"
        )}
        console._draw_header(screen, state, palette, "All", 140)
        writes = [call.args for call in screen.addnstr.call_args_list]
        self.assertTrue(any(y == 0 and x > 70 and "refreshed" in value
                            for y, x, value, *_ in writes))
        self.assertTrue(any(y == 1 and "All 1" in value
                            for y, x, value, *_ in writes))
        self.assertTrue(any(y == 2 and "━" in value
                            for y, x, value, *_ in writes))


if __name__ == "__main__":
    unittest.main()
