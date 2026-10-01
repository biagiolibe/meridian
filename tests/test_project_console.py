"""Read-only project console snapshot and output tests."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
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
            "# Task 001\n\n> **ID**: `001`\n\n## Objective\n\nFirst task.\n\n"
            "## Acceptance Criteria\n\n- [ ] First check.\n", encoding="utf-8",
        )
        (self.project / "tasks" / "002-second.md").write_text(
            "# Task 002\n\n> **ID**: `002`\n\n## Objective\n\nSecond task.\n\n"
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
        self.assertLess(lines.index("Dependencies"), lines.index("Objective"))
        self.assertLess(lines.index("Objective"), lines.index("Acceptance criteria"))
        self.assertLess(lines.index("Dependencies"), lines.index("Next directive"))
        self.assertIn("- [ ] Second check.", lines)

    def test_detail_sections_accept_governed_headings_and_show_dependency_states(self) -> None:
        self.write_queue()
        task = self.snapshot().tasks[0]
        governed = "# Task\n\n## 🎯 Goal\n\nGoverned goal.\n\n## ✅ Acceptance criteria\n\n- [ ] Done.\n"
        self.assertEqual(console._section(governed, "Objective", "Goal"), ("Governed goal.",))
        self.assertEqual(console._section(governed, "Acceptance Criteria"), ("- [ ] Done.",))
        detailed = console.Task(
            task.task_id, task.title, task.status, task.phase, ("001",), task.path,
            task.objective, task.criteria, readiness=task.readiness,
            dependency_states=(("001", "Done"),),
        )
        palette = {name: 0 for name in ("base", "text", "title", "ready", "muted", "line", "action")}
        lines = [value for value, _ in console._detail_lines(detailed, 50, palette)]
        self.assertLess(lines.index("Dependencies"), lines.index("Objective"))
        self.assertIn("001 — Done", lines)

    def test_detail_view_clamps_scroll_across_resize_and_draws_hidden_indicators(self) -> None:
        palette = {name: 0 for name in ("base", "text", "title", "ready", "muted", "line", "action")}
        task = console.Task(
            "LONG", "A long task", "[ ]", (), ("001",), None,
            tuple(f"Objective line {number} needs enough text to wrap in narrow panes." for number in range(12)),
            (), readiness="READY", dependency_states=(("001", "Done"),),
        )
        lines, offset, body = console._detail_view(task, 32, 14, 4, 999, palette)
        self.assertEqual(offset, len(lines) - body)
        self.assertEqual(console._scroll_detail(task, 32, 14, 4, offset, 1, palette), offset)
        self.assertEqual(console._scroll_detail(task, 32, 14, 4, offset, -1, palette), offset - 1)
        _, resized, resized_body = console._detail_view(task, 72, 28, 4, offset, palette)
        self.assertLessEqual(resized, max(0, len(console._detail_view(task, 72, 28, 4, 0, palette)[0]) - resized_body))
        screen = FakeScreen(14, 40)
        console._draw_detail(screen, task, 2, 4, 32, 14, offset, palette)
        self.assertIn("more above", "\n".join(screen.row(y) for y in range(4, 12)))

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

    def test_tab_wraps_through_all_and_empty_tabs_remain_clickable(self) -> None:
        self.write_queue()
        snapshot = self.snapshot()
        self.assertEqual(console._cycle_filter(snapshot, "Ready", 1), "All")
        self.assertEqual(console._cycle_filter(snapshot, "Ready", -1), "All")
        self.assertEqual(console._cycle_filter(snapshot, "All", 1), "Ready")
        self.assertEqual(console._tab_at(snapshot, 2, 1), "All")
        self.assertEqual(console._tab_at(snapshot, 20, 1), "Working")

    def test_ready_directive_copy_hit_and_clipboard_result(self) -> None:
        self.write_queue()
        task = self.snapshot().tasks[0]
        self.assertEqual(task.launch_command, "Proceed with 002")
        palette = {name: 0 for name in (
            "base", "text", "title", "ready", "muted", "line", "action"
        )}
        screen = mock.Mock()
        screen.getmaxyx.return_value = (35, 140)
        rows = console._draw_detail(screen, task, 95, 4, 43, 35, 0, palette)
        self.assertTrue(rows)
        self.assertTrue(console._action_hit(100, min(rows), (95, 136, rows)))
        self.assertFalse(console._action_hit(94, min(rows), (95, 136, rows)))
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.subprocess, "run") as run:
            run.return_value.returncode = 0
            self.assertTrue(console._copy_to_clipboard(task.launch_command))
            run.assert_called_once_with(
                ("pbcopy",), input="Proceed with 002", text=True,
                capture_output=True, check=False, timeout=2,
            )
            run.return_value.returncode = 1
            self.assertFalse(console._copy_to_clipboard(task.launch_command))

    def test_new_tabs_are_appended_after_existing_ones(self) -> None:
        self.write_queue()
        snapshot = self.snapshot()
        self.assertEqual(
            tuple(console._filter_counts(snapshot)),
            ("Ready", "Working", "Blocked", "Unknown", "Review", "Mismatch"),
        )


class AgentLaunchTest(unittest.TestCase):
    SESSION_ID = "w0t1p2:12345678-1234-1234-1234-123456789abc"

    def task(self, **changes) -> console.Task:
        values = dict(
            task_id="001", title="First", status="TODO", phase=(), dependencies=(), path=None,
            objective=(), criteria=(), readiness="READY", lifecycle="todo",
        )
        values.update(changes)
        return console.Task(**values)

    def test_permitted_directive_matrix_refuses_writers_and_mismatches(self) -> None:
        self.assertEqual(self.task().launch_command, "Proceed with 001")
        self.assertEqual(self.task(workflow="lean-delivery", readiness="READY FOR REVIEW",
                                   lifecycle="ready_for_review").launch_command, "Review 001")
        self.assertEqual(self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                                   lifecycle="ready_for_review", review="REQUIRED").launch_command,
                         "Review 001")
        self.assertEqual(self.task(workflow="governed-sdd", readiness="IN PROGRESS",
                                   lifecycle="in_progress", changes_requested=True).launch_command,
                         "Address review 001")
        self.assertIsNone(self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                                    lifecycle="ready_for_review", review="NOT_REQUIRED").launch_command)
        self.assertIsNone(self.task(readiness="MISMATCH", active_writer=True).launch_command)
        self.assertIsNone(self.task(active_writer=True).launch_command)

    def test_next_action_explains_review_launches_and_refusals(self) -> None:
        required = self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                             lifecycle="ready_for_review", review="REQUIRED")
        self.assertEqual(required.next_action, "If assigned: Review 001")
        self.assertEqual(
            self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                      lifecycle="ready_for_review").next_action,
            "Review unavailable: review policy not declared",
        )
        self.assertEqual(
            self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                      lifecycle="ready_for_review", review="NOT REQUIRED").next_action,
            "Review unavailable: Review: NOT REQUIRED",
        )
        self.assertEqual(
            self.task(workflow="governed-sdd", readiness="READY FOR REVIEW",
                      lifecycle="ready_for_review", review="REQUIRED", active_writer=True).next_action,
            "Review unavailable: active writer",
        )
        self.assertEqual(
            self.task(readiness="MISMATCH", mismatch="state conflict").next_action,
            "Resolve the state disagreement: state conflict",
        )
        self.assertEqual(
            self.task(readiness="READY FOR REVIEW", lifecycle="ready_for_review",
                      record_problem="task record not found").next_action,
            "Resolve the task record: task record not found",
        )
        lean = self.task(workflow="lean-delivery", readiness="READY FOR REVIEW",
                         lifecycle="ready_for_review")
        self.assertEqual(lean.next_action, "If assigned: Review 001")

    def test_request_revalidates_id_and_preserves_an_argument_vector(self) -> None:
        with mock.patch.dict(console.os.environ, {"ITERM_SESSION_ID": self.SESSION_ID}, clear=False):
            request, error = console._launch_request(self.task(), Path("."), "codex")
        self.assertIsNone(error)
        self.assertIsNotNone(request)
        self.assertEqual(request.directive, "Proceed with 001")
        self.assertEqual(request.session_uuid, "12345678-1234-1234-1234-123456789abc")
        self.assertIn("exec codex 'Proceed with 001'", request.shell_command)
        with mock.patch.dict(console.os.environ, {"ITERM_SESSION_ID": self.SESSION_ID}, clear=False):
            hostile, error = console._launch_request(self.task(task_id="001; rm -rf /"), Path("."), "codex")
        self.assertIsNone(hostile)
        self.assertIn("task ID", error or "")

    def test_request_refuses_missing_or_malformed_console_session(self) -> None:
        for session_id in (None, "w0t1p2:not-a-uuid", "wrong:12345678-1234-1234-1234-123456789abc"):
            environment = {} if session_id is None else {"ITERM_SESSION_ID": session_id}
            with self.subTest(session_id=session_id), \
                 mock.patch.dict(console.os.environ, environment, clear=True):
                request, error = console._launch_request(self.task(), Path("."), "codex")
            self.assertIsNone(request)
            self.assertEqual(error, "iTerm2 console session is missing or invalid; [copy] remains available")

    def test_launch_failure_modes_leave_copy_as_fallback(self) -> None:
        request = console.LaunchRequest(
            "codex", "Proceed with 001", Path("/project"), "001",
            "12345678-1234-1234-1234-123456789abc",
        )
        with mock.patch.object(console.sys, "platform", "linux"):
            self.assertIn("macOS", console._start_launch(request)[1])
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.shutil, "which", return_value=None):
            self.assertIn("codex is not available", console._start_launch(request)[1])
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(console.subprocess, "run", side_effect=subprocess.TimeoutExpired("osascript", 10)):
            self.assertIn("timed out", console._start_launch(request)[1])

    def test_osascript_receives_quoted_command_and_reports_iterm_failure(self) -> None:
        request = console.LaunchRequest(
            "claude", "Proceed with 001; echo nope", Path("/project name"), "001",
            "12345678-1234-1234-1234-123456789abc",
        )
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(console.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stderr="Application isn't running", stdout="")
            success, message = console._start_launch(request)
        self.assertFalse(success)
        self.assertIn("iTerm2 is unavailable", message)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "osascript")
        self.assertIn("exec claude 'Proceed with 001; echo nope'", command[2])
        self.assertIn("split horizontally with default profile", command[2])
        self.assertIn('if unique id of aSession is "12345678-1234-1234-1234-123456789abc"', command[2])
        self.assertIn("repeat with aSession in sessions of aTab", command[2])
        self.assertIn("tell newSession to write text", command[2])
        self.assertNotIn("w0t1p2", command[2])
        self.assertNotIn("create tab", command[2])
        self.assertNotIn("create window", command[2])

    @unittest.skipUnless(
        sys.platform == "darwin" and shutil.which("osacompile")
        and Path("/Applications/iTerm.app").exists(),
        "requires macOS osacompile and iTerm2",
    )
    def test_split_payload_compiles_as_applescript(self) -> None:
        payload = console._apple_script(
            "exec claude 'a \"q\" \\ b'", "12345678-1234-1234-1234-123456789abc",
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ("osacompile", "-o", str(Path(directory) / "payload.scpt"), "-e", payload),
                capture_output=True, text=True, check=False, timeout=30,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unmatched_console_session_leaves_copy_as_fallback(self) -> None:
        request = console.LaunchRequest(
            "codex", "Proceed with 001", Path("/project"), "001",
            "12345678-1234-1234-1234-123456789abc",
        )
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.shutil, "which", return_value="/usr/bin/tool"), \
             mock.patch.object(console.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stderr="MERIDIAN_SESSION_NOT_FOUND", stdout="")
            success, message = console._start_launch(request)
        self.assertFalse(success)
        self.assertEqual(message, "iTerm2 console session was not found; [copy] remains available")

    def test_start_revalidates_task_and_session_ids(self) -> None:
        request = console.LaunchRequest("codex", "Proceed with 001", Path("/project"), "001; rm -rf /", "bad")
        with mock.patch.object(console.sys, "platform", "darwin"), \
             mock.patch.object(console.shutil, "which", return_value="/usr/bin/tool"):
            success, message = console._start_launch(request)
        self.assertFalse(success)
        self.assertIn("task ID", message)


class FakeScreen:
    """Records what curses would draw, as a character grid read back by row."""

    def __init__(self, height: int, width: int) -> None:
        self.height, self.width = height, width
        self.rows = [[" "] * width for _ in range(height)]

    def getmaxyx(self) -> tuple[int, int]:
        return self.height, self.width

    def addnstr(self, y: int, x: int, value: str, count: int, attr: int = 0) -> None:
        for offset, char in enumerate(value[:count]):
            self.rows[y][x + offset] = char

    def row(self, y: int) -> str:
        return "".join(self.rows[y])


class ConsoleListLayoutTest(unittest.TestCase):
    PALETTE = {name: 0 for name in (
        "base", "text", "title", "ready", "muted", "line", "action", "selected",
        "working", "blocked", "unknown",
    )}

    @staticmethod
    def task(task_id: str, title: str = "Title") -> console.Task:
        return console.Task(task_id, title, "[ ]", ("Phase 1",), (), None, (), (),
                            readiness="READY")

    def render(self, tasks, width: int, all_tasks=None):
        screen = FakeScreen(20, width)
        console._draw_list(screen, list(tasks), tasks[0].task_id, 0, width, 20,
                           self.PALETTE, all_tasks)
        return screen

    def test_columns_follow_the_longest_id_for_3_8_13_and_18_characters(self) -> None:
        for length in (3, 8, 13, 18):
            with self.subTest(length=length):
                task_id = "X" * (length - 1) + "1"
                tasks = [self.task("001"), self.task(task_id, "Visible title")]
                screen = self.render(tasks, 110)
                layout = console._list_layout(tasks, 110)
                self.assertEqual(layout.id_width, length)
                self.assertEqual(layout.title_x, 3 + length + 1)
                row = screen.row(7)
                self.assertEqual(row[3:3 + length], task_id)
                self.assertEqual(row[layout.title_x:layout.title_x + 15], "○ Visible title")
                self.assertEqual(row[layout.status_x:layout.status_x + 5], "Ready")
                self.assertEqual(screen.row(3)[layout.status_x:layout.status_x + 6], "Status")
                self.assertEqual(screen.row(3)[layout.age_x:layout.age_x + 7], "Updated")

    def test_two_level_groups_render_once_and_search_both_labels(self) -> None:
        queue = ("# Queue\n\n## Program Queue\n\n### Phase 1\n\n" + HEADER
                 + "| `[ ]` | 001 | First | P2 | — | — |\n"
                 + "| `[ ]` | 002 | Second | P2 | — | — |\n\n"
                 + "### Phase 2\n\n" + HEADER
                 + "| `[ ]` | 003 | Third | P2 | — | — |\n")
        rows = console.parse_queue(queue, "fixture", console.PROFILES["lean-delivery"])
        tasks = [
            console.Task(row.task_id, row.title, row.status, row.section,
                         (), None, (), (), readiness="READY")
            for row in rows
        ]
        screen = self.render(tasks, 100)
        drawn = [screen.row(y).strip() for y in range(5, 12)]
        self.assertEqual(drawn[0], "Program")
        self.assertEqual(drawn[1], "Phase 1")
        self.assertIn("001", drawn[2])
        self.assertIn("002", drawn[3])
        self.assertEqual(drawn[4], "Phase 2")
        self.assertIn("003", drawn[5])
        self.assertEqual(sum(line == "Program" for line in drawn), 1)
        snapshot = console.Snapshot(Path("/p"), Path("/p/q"), "main", "clean", 0,
                                    tuple(tasks), 0)
        self.assertEqual([task.task_id for task in console._visible_tasks(snapshot, "All", "program")],
                         ["001", "002", "003"])
        self.assertEqual([task.task_id for task in console._visible_tasks(snapshot, "All", "phase 2")],
                         ["003"])

    def test_lean_active_queue_wrapper_keeps_phase_only_rendering(self) -> None:
        queue = ("# Queue\n\n## 🏃 Active Queue\n\n### Phase 29 — Work\n\n"
                 + HEADER + "| `[ ]` | 001 | First | P2 | — | — |\n")
        row = console.parse_queue(queue, "fixture", console.PROFILES["lean-delivery"])[0]
        self.assertEqual(row.section, ("Phase 29 — Work",))
        task = console.Task(row.task_id, row.title, row.status, row.section,
                            (), None, (), (), readiness="READY")
        screen = self.render([task], 100)
        self.assertEqual(screen.row(5).strip(), "Phase 29 — Work")
        self.assertNotIn("Active Queue", " ".join(screen.row(y) for y in range(5, 8)))

    def test_queue_heading_levels_two_through_six_render(self) -> None:
        for level in range(2, 7):
            with self.subTest(level=level):
                label = f"Level {level} Queue — Work"
                queue = (f"# Queue\n\n{'#' * level} {label}\n\n" + HEADER
                         + "| `[ ]` | 001 | First | P2 | — | — |\n")
                row = console.parse_queue(queue, "fixture", console.PROFILES["lean-delivery"])[0]
                task = console.Task(row.task_id, row.title, row.status, row.section,
                                    (), None, (), (), readiness="READY")
                self.assertEqual(row.section, (label,))
                self.assertEqual(self.render([task], 100).row(5).strip(),
                                 f"Level {level} — Work")

    def test_three_character_ids_keep_their_position_with_actual_width(self) -> None:
        tasks = [self.task("075"), self.task("076")]
        layout = console._list_layout(tasks, 110)
        self.assertEqual((layout.id_x, layout.id_width, layout.title_x), (3, 3, 7))
        self.assertEqual(self.render(tasks, 110).row(6)[1], "›")

    def test_id_is_capped_clipped_and_never_overlaps_title_or_status(self) -> None:
        long_id = "M20-EVENT-002-CORR"
        tasks = [self.task(long_id, "Title")]
        self.assertTrue(console._list_layout(tasks, 50).id_width < len(long_id))
        for width in (50, 60, 74, 110):
            with self.subTest(width=width):
                layout = console._list_layout(tasks, width)
                self.assertLessEqual(layout.id_width, width // 3)
                self.assertGreaterEqual(layout.title_width, console.LIST_MIN_TITLE_WIDTH)
                self.assertLessEqual(layout.title_x + layout.title_width + 2, layout.status_x)
                row = self.render(tasks, width).row(6)
                shown = row[3:3 + layout.id_width]
                self.assertEqual(shown, console._clip(long_id, layout.id_width))
                self.assertEqual(shown.endswith("…"), layout.id_width < len(long_id))
                self.assertEqual(row[3 + layout.id_width], " ")
                self.assertTrue(row[layout.title_x:].startswith("○ "))

    def test_filtering_does_not_move_columns(self) -> None:
        everything = [self.task("001"), self.task("M20-EVENT-002")]
        full = console._list_layout(everything, 110)
        filtered = self.render(everything[:1], 110, everything)
        self.assertEqual(filtered.row(6)[3:6], "001")
        self.assertEqual(filtered.row(6)[full.title_x:full.title_x + 7], "○ Title")
        self.assertEqual(filtered.row(3)[full.status_x:full.status_x + 6], "Status")
        self.assertNotEqual(full, console._list_layout(everything[:1], 110))

    def test_full_id_is_in_detail_copy_directive_and_one_shot(self) -> None:
        task = self.task("M20-EVENT-002-CORR")
        lines = [value for value, _ in console._detail_lines(task, 60, self.PALETTE)]
        self.assertIn("Task M20-EVENT-002-CORR", lines)
        self.assertEqual(task.launch_command, "Proceed with M20-EVENT-002-CORR")
        state = console.ConsoleState(Path("."))
        state.snapshot = console.Snapshot(
            Path("."), Path("tasks/QUEUE.md"), "main", "clean", 0, (task,), 0,
        )
        state.last_success = datetime.now().astimezone()
        self.assertIn("M20-EVENT-002-CORR [READY] Title", console.one_shot(state))


class RepoCase(unittest.TestCase):
    """Throwaway Git repository with a primary checkout and task worktrees."""

    lock = "LEAN_DELIVERY"

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.project = self.root / "project"
        self.project.mkdir()
        self.git(self.project, "init", "-q", "-b", "main")
        self.write(self.project, "PROJECT_WORKFLOW.md", f"# {self.lock}\n")

    def git(self, cwd: Path, *args: str) -> str:
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "user.name=Test",
             "-c", "user.email=test@example.com", "-C", str(cwd), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def write(self, root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, cwd: Path, message: str = "change") -> None:
        self.git(cwd, "add", "-A")
        self.git(cwd, "commit", "-q", "-m", message)

    def worktree(self, branch: str) -> Path:
        path = self.root / f"wt-{branch}"
        self.git(self.project, "worktree", "add", "-q", "-b", branch, str(path))
        return path

    def load(self) -> dict[str, console.Task]:
        return {task.task_id: task for task in console.load_snapshot(self.project).tasks}

    def refs_and_status(self) -> tuple[str, str]:
        return (self.git(self.project, "for-each-ref"),
                self.git(self.project, "status", "--porcelain"))


class LeanEffectiveStateTest(RepoCase):
    def queue(self, statuses: dict[str, str], deps: dict[str, str] | None = None) -> str:
        rows = "".join(
            f"| `[{token}]` | {task_id} | Task {task_id} | P2 | {(deps or {}).get(task_id, '—')} "
            f"| [{task_id}]({task_id}-task.md) |\n"
            for task_id, token in statuses.items()
        )
        return ("# Queue\n\n### Phase 1\n\n" + HEADER + rows)

    def setup_project(self, statuses: dict[str, str], deps: dict[str, str] | None = None) -> None:
        self.write(self.project, "tasks/QUEUE.md", self.queue(statuses, deps))
        for task_id in statuses:
            self.write(
                self.project, f"tasks/{task_id}-task.md",
                f"# Task {task_id} — Title {task_id}\n\n> **ID**: `{task_id}`\n\n"
                "## Objective\n\nDo it.\n\n## Acceptance Criteria\n\n- [ ] Check.\n",
            )
        self.commit(self.project, "initial")

    def set_branch_status(self, wt: Path, task_id: str, token: str, handoff: str | None = None) -> None:
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8")
        queue = re.sub(rf"\| `\[.\]` \| {task_id} \|", f"| `[{token}]` | {task_id} |", queue)
        self.write(wt, "tasks/QUEUE.md", queue)
        if handoff:
            self.write(wt, f"tasks/handoffs/{task_id}.md",
                       f"# Completion Report — {task_id}\n\n- Status: `{handoff}`\n")
        self.commit(wt, f"{task_id} {token}")

    def test_task_without_branch_keeps_current_behavior(self) -> None:
        self.setup_project({"001": " "})
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.lifecycle, task.source), ("READY", "todo", "main"))
        self.assertEqual(task.launch_command, "Proceed with 001")
        self.assertFalse(task.active_writer)

    def test_reserved_branch_state_wins_without_any_write(self) -> None:
        self.setup_project({"001": " "})
        self.set_branch_status(self.worktree("task-001"), "001", "/")
        before = self.refs_and_status()
        task = self.load()["001"]
        self.assertEqual(self.refs_and_status(), before)
        self.assertEqual((task.readiness, task.lifecycle), ("IN PROGRESS", "in_progress"))
        self.assertEqual(task.source, "branch task-001")
        self.assertIsNone(task.launch_command)
        self.assertEqual(task.worktree, str(self.root / "wt-task-001"))
        self.assertIn("[ ]", (self.project / "tasks/QUEUE.md").read_text(encoding="utf-8"))

    def test_clean_prepared_worktree_is_registered_but_stays_todo(self) -> None:
        self.setup_project({"001": " "})
        self.worktree("task-001")
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.lifecycle, task.source), ("READY", "todo", "main"))
        self.assertFalse(task.active_writer)
        self.assertEqual(task.markers, ("registered worktree",))

    def test_uncommitted_in_progress_row_supersedes_committed_todo(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8").replace("| `[ ]` | 001 |", "| `[/]` | 001 |")
        self.write(wt, "tasks/QUEUE.md", queue)
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.lifecycle), ("IN PROGRESS", "in_progress"))
        self.assertEqual(task.source, "uncommitted task-001")
        self.assertTrue(task.active_writer)

    def test_working_tree_behind_committed_row_is_a_mismatch(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        self.set_branch_status(wt, "001", "/")
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8").replace("| `[/]` | 001 |", "| `[ ]` | 001 |")
        self.write(wt, "tasks/QUEUE.md", queue)
        task = self.load()["001"]
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("working tree TODO", task.mismatch or "")

    def test_unparseable_working_queue_falls_back_to_committed_state(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        self.set_branch_status(wt, "001", "/")
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8").replace("`[/]`", "`[?]`")
        self.write(wt, "tasks/QUEUE.md", queue)
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.source), ("IN PROGRESS", "branch task-001"))

    def test_missing_registered_worktree_directory_does_not_break_snapshot(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        moved = wt.with_name("missing-task-001")
        wt.rename(moved)
        self.addCleanup(lambda: moved.rename(wt) if moved.exists() else None)
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.source), ("READY", "main"))
        self.assertEqual(task.worktree, str(wt))

    def test_completed_branch_with_done_handoff_is_ready_for_review(self) -> None:
        self.setup_project({"001": " "})
        self.set_branch_status(self.worktree("task-001"), "001", "x", handoff="DONE")
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.lifecycle), ("READY FOR REVIEW", "ready_for_review"))
        self.assertEqual(console._state_label(task), ("Review", "ready"))
        self.assertEqual(task.launch_command, "Review 001")

    def test_completed_row_without_done_handoff_is_a_mismatch(self) -> None:
        self.setup_project({"001": " "})
        self.set_branch_status(self.worktree("task-001"), "001", "x", handoff="BLOCKED")
        task = self.load()["001"]
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("handoff BLOCKED", task.mismatch or "")

    def test_completed_branch_with_dirty_worktree_stays_in_progress(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        self.set_branch_status(wt, "001", "x", handoff="DONE")
        self.write(wt, "scratch.txt", "uncommitted")
        task = self.load()["001"]
        self.assertEqual((task.readiness, task.lifecycle), ("IN PROGRESS", "in_progress"))
        self.assertTrue(task.active_writer)

    def test_dirty_worktree_is_advisory_and_never_changes_state(self) -> None:
        self.setup_project({"001": " "})
        wt = self.worktree("task-001")
        self.set_branch_status(wt, "001", "/")
        clean = self.load()["001"]
        self.write(wt, "scratch.txt", "uncommitted")
        dirty = self.load()["001"]
        self.assertFalse(clean.active_writer)
        self.assertTrue(dirty.active_writer)
        self.assertEqual((clean.readiness, clean.lifecycle), (dirty.readiness, dirty.lifecycle))
        self.assertEqual(dirty.markers, ("active writer",))

    def test_branch_behind_primary_is_a_mismatch_without_directive(self) -> None:
        self.setup_project({"001": "/"})
        self.worktree("task-001")
        wt = self.root / "wt-task-001"
        self.set_branch_status(wt, "001", " ")
        task = self.load()["001"]
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("main IN_PROGRESS", task.mismatch or "")
        self.assertIn("task-001 TODO", task.mismatch or "")
        self.assertIsNone(task.launch_command)
        self.assertEqual(console._state_label(task)[0], "Mismatch")

    def test_dependencies_are_satisfied_by_integrated_state_only(self) -> None:
        self.setup_project({"001": " ", "002": " "}, deps={"002": "001"})
        self.set_branch_status(self.worktree("task-001"), "001", "x", handoff="DONE")
        tasks = self.load()
        self.assertEqual(tasks["001"].readiness, "READY FOR REVIEW")
        self.assertEqual(tasks["002"].readiness, "BLOCKED: 001")
        self.assertIsNone(tasks["002"].launch_command)

    def test_milestone_identity_resolves_the_task_branch(self) -> None:
        self.write(self.project, ".meridian/task-identity.json",
                   json.dumps({"version": 1, "mode": "milestone"}))
        self.setup_project({"M1-CORE-001": " "})
        self.set_branch_status(self.worktree("m1-core-001"), "M1-CORE-001", "/")
        task = self.load()["M1-CORE-001"]
        self.assertEqual(task.source, "branch m1-core-001")
        self.assertEqual(task.readiness, "IN PROGRESS")

    def test_one_shot_reports_source_markers_and_mismatch(self) -> None:
        self.setup_project({"001": " ", "002": "/"})
        wt = self.worktree("task-001")
        self.set_branch_status(wt, "001", "/")
        self.write(wt, "scratch.txt", "uncommitted")
        self.set_branch_status(self.worktree("task-002"), "002", " ")
        state = console.ConsoleState(self.project)
        state.refresh()
        output = console.one_shot(state)
        self.assertIn("State from: branch task-001", output)
        self.assertIn("Markers: active writer", output)
        self.assertIn("Mismatch: main IN_PROGRESS, task-002 TODO", output)


class GovernedEffectiveStateTest(RepoCase):
    lock = "GOVERNED_SDD"
    header = (
        "| Order | ID | Priority | Status | Review | Dependencies | Task file |\n"
        "|---:|---|---|---|---|---|---|\n"
    )

    def setup_project(self, rows: list[tuple[str, str, str, str]]) -> None:
        """Rows are (id, status, review, dependencies)."""
        body = "# Task Execution Queue\n\n" + self.header + "".join(
            f"| {index} | {task_id} | P1 | {status} | {review} | {deps} | "
            f"[{task_id}]({task_id}.md) |\n"
            for index, (task_id, status, review, deps) in enumerate(rows, 1)
        )
        self.write(self.project, "tasks/QUEUE.md", body)
        for task_id, status, review, _deps in rows:
            self.write_record(self.project, task_id, status)
        self.commit(self.project, "initial")

    def write_record(self, root: Path, task_id: str, status: str) -> None:
        self.write(root, f"tasks/{task_id}.md",
                   f"# Task {task_id} — Governed {task_id}\n\nPriority: P1\nStatus: {status}\n"
                   "Review: REQUIRED\n\n## Objective\n\nGoverned work.\n")

    def set_branch(self, wt: Path, task_id: str, status: str, record: str | None = None,
                   review: str | None = None) -> None:
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8")
        queue = re.sub(rf"(\| {task_id} \| P1 \| )\w+", rf"\g<1>{status}", queue)
        self.write(wt, "tasks/QUEUE.md", queue)
        self.write_record(wt, task_id, record or status)
        if review:
            self.write(wt, f"tasks/reviews/{task_id}.md", review)
        self.commit(wt, f"{task_id} {status}")

    def test_queue_statuses_map_to_normalized_phases_and_dependencies(self) -> None:
        self.setup_project([
            ("TASK-001", "ACCEPTED", "REQUIRED", "—"),
            ("TASK-002", "QUEUED", "REQUIRED", "TASK-001"),
            ("TASK-003", "IN_PROGRESS", "REQUIRED", "—"),
            ("TASK-004", "READY_FOR_REVIEW", "REQUIRED", "—"),
            ("TASK-005", "ANSWERED", "SPIKE", "—"),
            ("TASK-006", "QUEUED", "REQUIRED", "TASK-005"),
            ("TASK-007", "INCONCLUSIVE", "SPIKE", "—"),
            ("TASK-008", "QUEUED", "REQUIRED", "TASK-007"),
        ])
        tasks = self.load()
        self.assertEqual({tid: t.lifecycle for tid, t in tasks.items()}, {
            "TASK-002": "todo", "TASK-003": "in_progress", "TASK-004": "ready_for_review",
            "TASK-006": "todo", "TASK-008": "todo",
        })
        self.assertEqual(tasks["TASK-002"].readiness, "READY")
        self.assertEqual(tasks["TASK-006"].readiness, "READY")
        self.assertEqual(tasks["TASK-008"].readiness, "BLOCKED: TASK-007")
        self.assertEqual(tasks["TASK-004"].title, "Governed TASK-004")

    def test_dependency_on_unaccepted_task_is_blocked(self) -> None:
        self.setup_project([
            ("TASK-001", "READY_FOR_REVIEW", "REQUIRED", "—"),
            ("TASK-002", "QUEUED", "REQUIRED", "TASK-001"),
        ])
        self.assertEqual(self.load()["TASK-002"].readiness, "BLOCKED: TASK-001")

    def test_unrecognized_status_is_an_explicit_error(self) -> None:
        self.setup_project([("TASK-001", "CHANGES_REQUESTED", "REQUIRED", "—")])
        with self.assertRaisesRegex(console.ConsoleError, "Unknown task status"):
            console.load_snapshot(self.project)

    def test_ready_for_review_requires_record_queue_and_review_agreement(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "REQUIRED", "—")])
        wt = self.worktree("task-001")
        self.set_branch(wt, "TASK-001", "READY_FOR_REVIEW")
        task = self.load()["TASK-001"]
        self.assertEqual((task.readiness, task.lifecycle), ("READY FOR REVIEW", "ready_for_review"))
        self.assertEqual(task.source, "branch task-001")
        self.set_branch(wt, "TASK-001", "READY_FOR_REVIEW", record="IN_PROGRESS")
        task = self.load()["TASK-001"]
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("task record IN_PROGRESS", task.mismatch or "")
        self.assertIsNone(task.launch_command)

    def test_ready_for_review_without_required_review_is_a_mismatch(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "NOT_REQUIRED", "—")])
        self.set_branch(self.worktree("task-001"), "TASK-001", "READY_FOR_REVIEW")
        task = self.load()["TASK-001"]
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("Review NOT_REQUIRED", task.mismatch or "")

    def test_latest_changes_requested_attempt_marks_in_progress_task(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "REQUIRED", "—")])
        wt = self.worktree("task-001")
        review = (
            "# Review Record — TASK-001\n\n## Attempt 1 — CHANGES_REQUESTED\n\n- x\n\n"
            "## Attempt 2 — CHANGES_REQUESTED\n\n- y\n"
        )
        self.set_branch(wt, "TASK-001", "IN_PROGRESS", review=review)
        task = self.load()["TASK-001"]
        self.assertEqual((task.readiness, task.lifecycle), ("IN PROGRESS", "in_progress"))
        self.assertTrue(task.changes_requested)
        self.assertEqual(task.markers, ("changes requested",))
        approved = review + "\n## Attempt 3 — APPROVE\n\n- z\n"
        self.set_branch(wt, "TASK-001", "IN_PROGRESS", review=approved)
        self.assertFalse(self.load()["TASK-001"].changes_requested)

    def test_resubmission_after_changes_requested_is_ready_for_review(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "REQUIRED", "—")])
        review = "# Review Record — TASK-001\n\n## Attempt 1 — CHANGES_REQUESTED\n\n- x\n"
        self.set_branch(self.worktree("task-001"), "TASK-001", "READY_FOR_REVIEW", review=review)
        task = self.load()["TASK-001"]
        self.assertEqual(task.lifecycle, "ready_for_review")
        self.assertFalse(task.changes_requested)

    def test_branch_accepted_is_done_on_branch_and_does_not_unblock_dependents(self) -> None:
        self.setup_project([
            ("TASK-001", "QUEUED", "REQUIRED", "—"),
            ("TASK-002", "QUEUED", "REQUIRED", "TASK-001"),
        ])
        self.set_branch(self.worktree("task-001"), "TASK-001", "ACCEPTED")
        tasks = self.load()
        self.assertEqual(tasks["TASK-001"].readiness, "DONE ON BRANCH")
        self.assertEqual(tasks["TASK-002"].readiness, "BLOCKED: TASK-001")

    def test_dirty_worktree_shows_active_writer(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "REQUIRED", "—")])
        wt = self.worktree("task-001")
        self.set_branch(wt, "TASK-001", "IN_PROGRESS")
        self.write(wt, "scratch.txt", "uncommitted")
        task = self.load()["TASK-001"]
        self.assertTrue(task.active_writer)
        self.assertEqual(task.readiness, "IN PROGRESS")

    def test_uncommitted_in_progress_row_supersedes_committed_queued(self) -> None:
        self.setup_project([("TASK-001", "QUEUED", "REQUIRED", "—")])
        wt = self.worktree("task-001")
        queue = (wt / "tasks/QUEUE.md").read_text(encoding="utf-8").replace(
            "| TASK-001 | P1 | QUEUED", "| TASK-001 | P1 | IN_PROGRESS")
        self.write(wt, "tasks/QUEUE.md", queue)
        task = self.load()["TASK-001"]
        self.assertEqual((task.readiness, task.lifecycle), ("IN PROGRESS", "in_progress"))
        self.assertEqual(task.source, "uncommitted task-001")


class LinklessQueueTest(RepoCase):
    """A Governed SDD project shaped like Palimpsest: no file or review column."""

    lock = "GOVERNED_SDD"
    header = (
        "| Order | ID | Priority | Status | Dependencies | Estimate |\n"
        "|---:|---|---|---|---|---|\n"
    )

    def setUp(self) -> None:
        super().setUp()
        self.write(self.project, ".meridian/task-identity.json",
                   json.dumps({"version": 1, "mode": "milestone"}))
        self.write(self.project, "PROJECT_WORKFLOW.md", (
            f"# {self.lock}\n\n<!-- MERIDIAN:BEGIN capability=execution-assets v1 -->\n"
            "<!-- MERIDIAN:END -->\n\n"
            "The queue is `docs/TASK_QUEUE.md`. Task files live under "
            "`docs/tasks/<milestone>/<TASK-ID>.md`. Durable review records at "
            "`docs/tasks/reviews/<TASK-ID>.md`. Completion handoffs live at "
            "`tasks/handoffs/<TASK-ID>.md`.\n"
        ))

    def record(self, task_id: str, status: str = "QUEUED", milestone: str = "M37") -> str:
        return (f"docs/tasks/{milestone}/{task_id}.md",
                f"# {task_id} — Title of {task_id}\n\nStatus: {status}\n\n"
                f"## Objective\n\nObjective of {task_id}.\n")

    def setup_project(self, rows: list[tuple[str, str, str]], records: bool = True,
                      header: str | None = None) -> None:
        """Rows are (id, status, dependencies)."""
        body = "# Task Queue\n\n" + (header or self.header) + "".join(
            f"| {index} | {task_id} | P1 | {status} | {deps} | 2h |\n"
            for index, (task_id, status, deps) in enumerate(rows, 1)
        )
        self.write(self.project, "docs/TASK_QUEUE.md", body)
        for task_id, status, _deps in rows if records else ():
            path, text = self.record(task_id, status)
            self.write(self.project, path, text)
        self.commit(self.project, "initial")

    def test_palimpsest_shaped_project_lists_every_row_without_stale(self) -> None:
        rows = [
            ("M37-CAUSE-001", "ACCEPTED", "—"), ("M37-CAUSE-002", "QUEUED", "M37-CAUSE-001"),
            ("M37-CAUSE-003", "IN_PROGRESS", "—"), ("M37-CAUSE-004", "READY_FOR_REVIEW", "—"),
            ("M37-SPIKE-001", "ANSWERED", "—"), ("M37-CAUSE-005", "QUEUED", "M37-SPIKE-001"),
        ]
        self.setup_project(rows)
        for task_id, _status, _deps in rows:  # review and handoff records share the ID
            self.write(self.project, f"docs/tasks/reviews/{task_id}.md", "# Review\n")
            self.write(self.project, f"tasks/handoffs/{task_id}.md", "# Handoff\n")
        self.write(self.project, "docs/tasks/M36/notes/handoffs/M37-CAUSE-002.md", "# Stray\n")
        self.commit(self.project, "records")
        state = console.ConsoleState(self.project)
        state.refresh()
        self.assertIsNone(state.error)
        self.assertNotIn("STALE", console.one_shot(state))
        tasks = {task.task_id: task for task in state.snapshot.tasks}
        self.assertEqual(sorted(tasks), ["M37-CAUSE-002", "M37-CAUSE-003",
                                         "M37-CAUSE-004", "M37-CAUSE-005"])
        self.assertEqual(tasks["M37-CAUSE-002"].path,
                         self.project / "docs/tasks/M37/M37-CAUSE-002.md")
        self.assertEqual(tasks["M37-CAUSE-002"].title, "Title of M37-CAUSE-002")
        self.assertEqual(tasks["M37-CAUSE-002"].objective, ("Objective of M37-CAUSE-002.",))
        self.assertIsNone(tasks["M37-CAUSE-002"].record_problem)
        self.assertEqual(tasks["M37-CAUSE-002"].readiness, "READY")
        self.assertEqual(tasks["M37-CAUSE-002"].launch_command, "Proceed with M37-CAUSE-002")
        self.assertEqual(tasks["M37-CAUSE-005"].readiness, "READY")
        self.assertEqual(state.snapshot.done_count, 2)

    def test_milestone_headings_group_the_rendered_open_list(self) -> None:
        queue = "# Task Queue\n\n## Rules\n\nText only.\n\n## Priority\n\nText only.\n\n"
        counts = {}
        for number in range(1, 38):
            milestone = f"M{number:02}"
            task_id = f"{milestone}-CAUSE-001"
            status = "ACCEPTED" if number == 1 else "QUEUED"
            queue += (f"## {milestone} Queue — Milestone {number}\n\n" + self.header
                      + f"| {number} | {task_id} | P1 | {status} | — | 2h |\n\n")
            self.write(self.project, *self.record(task_id, status, milestone))
            counts[milestone] = 1
        queue += ("## F0 Queue — Presentation track\n\n" + self.header
                  + "| 38 | F0-PRES-001 | P1 | QUEUED | — | 2h |\n"
                  + "| 39 | F0-PRES-002 | P1 | QUEUED | — | 2h |\n")
        for task_id in ("F0-PRES-001", "F0-PRES-002"):
            self.write(self.project, *self.record(task_id, milestone="F0"))
        counts["F0"] = 2
        self.write(self.project, "docs/TASK_QUEUE.md", queue)
        self.commit(self.project, "milestone queue")

        snapshot = console.load_snapshot(self.project)
        self.assertEqual(snapshot.done_count, 1)
        self.assertEqual(len(snapshot.tasks), 38)
        grouped = {}
        for task in snapshot.tasks:
            grouped.setdefault(task.phase[0].split()[0], []).append(task.task_id)
        self.assertEqual({name: len(rows) for name, rows in grouped.items()},
                         {name: count for name, count in counts.items() if name != "M01"})

        screen = FakeScreen(100, 110)
        console._draw_list(screen, list(snapshot.tasks), snapshot.tasks[0].task_id,
                           0, 110, 100, ConsoleListLayoutTest.PALETTE)
        drawn = [screen.row(y).strip() for y in range(5, 85)]
        headings = [line for line in drawn if re.fullmatch(
            r"(?:M\d{2} — Milestone \d+|F0 — Presentation track)", line)]
        self.assertEqual(headings, [f"M{number:02} — Milestone {number}"
                                    for number in range(2, 38)]
                         + ["F0 — Presentation track"])
        self.assertFalse(any("Rules" in line or "Priority" in line or "M01" in line
                             for line in drawn))
        self.assertLess(drawn.index("M37 — Milestone 37"), drawn.index("F0 — Presentation track"))
        self.assertEqual([task.task_id for task in console._visible_tasks(
            snapshot, "All", "presentation track")], ["F0-PRES-001", "F0-PRES-002"])

    def test_queue_without_review_column_declares_no_review_policy(self) -> None:
        self.setup_project([("M37-CAUSE-004", "READY_FOR_REVIEW", "—")])
        task = self.load()["M37-CAUSE-004"]
        self.assertIsNone(task.review)
        self.assertEqual((task.readiness, task.lifecycle), ("READY FOR REVIEW", "ready_for_review"))
        self.assertIsNone(task.launch_command)
        self.assertIsNone(task.mismatch)

    def test_task_record_review_values_are_strict(self) -> None:
        for value, expected in (
            ("REQUIRED", "REQUIRED"), (" NOT REQUIRED ", "NOT REQUIRED"),
            ("", None), ("required", None), ("OPTIONAL", None),
        ):
            with self.subTest(value=value):
                self.assertEqual(console.record_review(f"Review: {value}\n"), expected)
        self.assertIsNone(console.record_review("Status: READY_FOR_REVIEW\n"))

    def test_branch_task_record_review_required_offers_review(self) -> None:
        self.setup_project([("M37-CAUSE-004", "QUEUED", "—")])
        wt = self.worktree("m37-cause-004")
        queue = (wt / "docs/TASK_QUEUE.md").read_text(encoding="utf-8").replace(
            "QUEUED", "READY_FOR_REVIEW")
        self.write(wt, "docs/TASK_QUEUE.md", queue)
        path, text = self.record("M37-CAUSE-004", "READY_FOR_REVIEW")
        self.write(wt, path, text + "Review: REQUIRED\n")
        self.commit(wt)
        task = self.load()["M37-CAUSE-004"]
        self.assertEqual((task.source, task.review, task.readiness),
                         ("branch m37-cause-004", "REQUIRED", "READY FOR REVIEW"))
        self.assertEqual(task.launch_command, "Review M37-CAUSE-004")
        self.assertEqual(task.next_action, "If assigned: Review M37-CAUSE-004")

    def test_branch_task_record_not_required_uses_queue_mismatch_rule(self) -> None:
        self.setup_project([("M37-CAUSE-004", "QUEUED", "—")])
        wt = self.worktree("m37-cause-004")
        queue = (wt / "docs/TASK_QUEUE.md").read_text(encoding="utf-8").replace(
            "QUEUED", "READY_FOR_REVIEW")
        self.write(wt, "docs/TASK_QUEUE.md", queue)
        path, text = self.record("M37-CAUSE-004", "READY_FOR_REVIEW")
        self.write(wt, path, text + "Review: NOT REQUIRED\n")
        self.commit(wt)
        task = self.load()["M37-CAUSE-004"]
        self.assertEqual(task.review, "NOT REQUIRED")
        self.assertEqual(task.readiness, "MISMATCH")
        self.assertIn("Review NOT REQUIRED", task.mismatch or "")

    def test_review_column_still_gates_review_state(self) -> None:
        header = ("| Order | ID | Priority | Status | Review | Dependencies |\n"
                  "|---:|---|---|---|---|---|\n")
        self.write(self.project, "docs/TASK_QUEUE.md", "# Q\n\n" + header
                   + "| 1 | M37-CAUSE-004 | P1 | READY_FOR_REVIEW | NOT_REQUIRED | — |\n")
        path, text = self.record("M37-CAUSE-004", "READY_FOR_REVIEW")
        self.write(self.project, path, text)
        self.commit(self.project)
        task = self.load()["M37-CAUSE-004"]
        self.assertEqual((task.review, task.readiness), ("NOT_REQUIRED", "MISMATCH"))

    def test_missing_record_is_a_per_task_problem(self) -> None:
        self.setup_project([("M37-CAUSE-001", "QUEUED", "—"), ("M37-CAUSE-002", "QUEUED", "—")],
                           records=False)
        path, text = self.record("M37-CAUSE-002")
        self.write(self.project, path, text)
        self.commit(self.project)
        tasks = self.load()
        missing = tasks["M37-CAUSE-001"]
        self.assertEqual(missing.record_problem, "task record not found")
        self.assertEqual((missing.title, missing.status, missing.objective, missing.updated_at),
                         ("M37-CAUSE-001", "QUEUED", (), None))
        self.assertIsNone(missing.path)
        self.assertIsNone(missing.launch_command)
        self.assertNotEqual(missing.readiness, "READY")
        self.assertEqual(tasks["M37-CAUSE-002"].readiness, "READY")
        palette = {name: 0 for name in (
            "base", "text", "title", "muted", "line", "action", "blocked", "unknown")}
        lines = [value for value, _ in console._detail_lines(missing, 60, palette)]
        self.assertIn("Task record not found", lines)
        self.assertIn("Unavailable", lines)
        self.assertNotIn("Proceed with", " ".join(lines))

    def test_duplicate_record_lists_the_paths_and_offers_no_directive(self) -> None:
        self.setup_project([("M37-CAUSE-001", "QUEUED", "—"), ("M37-CAUSE-002", "QUEUED", "—")])
        self.write(self.project, "tasks/M36/M37-CAUSE-001.md", "# Copy\n")
        self.commit(self.project)
        tasks = self.load()
        duplicate = tasks["M37-CAUSE-001"]
        self.assertEqual(
            duplicate.record_problem,
            "ambiguous task record: docs/tasks/M37/M37-CAUSE-001.md, tasks/M36/M37-CAUSE-001.md")
        self.assertIsNone(duplicate.launch_command)
        palette = {name: 0 for name in (
            "base", "text", "title", "muted", "line", "action", "blocked", "unknown")}
        lines = " ".join(value for value, _ in console._detail_lines(duplicate, 200, palette))
        self.assertIn("docs/tasks/M37/M37-CAUSE-001.md, tasks/M36/M37-CAUSE-001.md", lines)
        self.assertIn("Record: ambiguous", self.one_shot())
        self.assertEqual(tasks["M37-CAUSE-002"].readiness, "READY")

    def one_shot(self) -> str:
        state = console.ConsoleState(self.project)
        state.refresh()
        return console.one_shot(state)

    def test_present_but_invalid_link_keeps_its_rejection(self) -> None:
        header = ("| Order | ID | Priority | Status | Dependencies | Task file |\n"
                  "|---:|---|---|---|---|---|\n")
        self.write(self.project, *self.record("M37-CAUSE-001"))
        for cell, message in (("see notes", "no unambiguous file link"),
                              ("[x](../../outside.md)", "no unambiguous file link"),
                              ("[x](tasks/missing.md)", "unavailable within the project")):
            self.write(self.project, "docs/TASK_QUEUE.md", "# Q\n\n" + header
                       + f"| 1 | M37-CAUSE-001 | P1 | QUEUED | — | {cell} |\n")
            with self.assertRaisesRegex(console.ConsoleError, message, msg=cell):
                console.load_snapshot(self.project)

    def test_link_wins_over_the_search_when_present(self) -> None:
        header = ("| Order | ID | Priority | Status | Dependencies | Task file |\n"
                  "|---:|---|---|---|---|---|\n")
        self.write(self.project, "docs/TASK_QUEUE.md", "# Q\n\n" + header
                   + "| 1 | M37-CAUSE-001 | P1 | QUEUED | — | [t](tasks/M37/M37-CAUSE-001.md) |\n")
        self.write(self.project, "docs/tasks/M37/M37-CAUSE-001.md",
                   "# M37-CAUSE-001 — Linked\n\nStatus: QUEUED\n")
        self.commit(self.project)
        task = self.load()["M37-CAUSE-001"]
        self.assertEqual((task.title, task.record_problem), ("Linked", None))

    def test_record_is_read_from_the_task_branch_without_links(self) -> None:
        self.setup_project([("M37-CAUSE-001", "QUEUED", "—")])
        queue_path = self.project / "docs/TASK_QUEUE.md"
        queue_path.write_text(queue_path.read_text(encoding="utf-8").replace(
            "# Task Queue\n\n", "# Task Queue\n\n## M37 Queue — Main group\n\n"),
            encoding="utf-8")
        self.commit(self.project, "main group")
        wt = self.worktree("m37-cause-001")
        queue = (wt / "docs/TASK_QUEUE.md").read_text(encoding="utf-8").replace(
            "QUEUED", "IN_PROGRESS").replace("Main group", "Branch group")
        self.write(wt, "docs/TASK_QUEUE.md", queue)
        path, text = self.record("M37-CAUSE-001", "IN_PROGRESS")
        self.write(wt, path, text.replace("Objective of", "Branch objective of"))
        self.commit(wt)
        before = self.refs_and_status()
        task = self.load()["M37-CAUSE-001"]
        self.assertEqual(self.refs_and_status(), before)
        self.assertEqual((task.source, task.readiness), ("branch m37-cause-001", "IN PROGRESS"))
        self.assertIsNone(task.record_problem)
        self.assertEqual(task.objective, ("Branch objective of M37-CAUSE-001.",))
        self.assertEqual(task.path, self.project / path)
        self.assertIsNotNone(task.updated_at)
        self.assertEqual(task.phase, ("M37 Queue — Main group",))

    def test_branch_record_state_is_used_when_the_queue_has_no_links(self) -> None:
        self.setup_project([("M37-CAUSE-004", "QUEUED", "—")])
        wt = self.worktree("m37-cause-004")
        queue = (wt / "docs/TASK_QUEUE.md").read_text(encoding="utf-8").replace(
            "QUEUED", "READY_FOR_REVIEW")
        self.write(wt, "docs/TASK_QUEUE.md", queue)
        self.write(wt, *self.record("M37-CAUSE-004", "READY_FOR_REVIEW"))
        self.commit(wt)
        task = self.load()["M37-CAUSE-004"]
        self.assertEqual((task.source, task.readiness, task.mismatch),
                         ("branch m37-cause-004", "READY FOR REVIEW", None))

    def test_branch_that_moved_the_record_is_resolved_in_its_own_tree(self) -> None:
        self.setup_project([("M37-CAUSE-004", "QUEUED", "—")])
        wt = self.worktree("m37-cause-004")
        queue = (wt / "docs/TASK_QUEUE.md").read_text(encoding="utf-8").replace(
            "QUEUED", "READY_FOR_REVIEW")
        self.write(wt, "docs/TASK_QUEUE.md", queue)
        self.git(wt, "rm", "-q", "docs/tasks/M37/M37-CAUSE-004.md")
        self.write(wt, *self.record("M37-CAUSE-004", "READY_FOR_REVIEW", milestone="M38"))
        self.commit(wt)
        task = self.load()["M37-CAUSE-004"]
        self.assertEqual((task.source, task.readiness, task.mismatch),
                         ("branch m37-cause-004", "READY FOR REVIEW", None))
        self.assertEqual(task.path, self.project / "docs/tasks/M37/M37-CAUSE-004.md")

    def test_record_resolution_adds_no_per_task_subprocess_work(self) -> None:
        def calls(count: int, linked: bool) -> int:
            names = [f"M37-CAUSE-{n:03}" for n in range(count)]
            header = ("| Order | ID | Priority | Status | Dependencies | Task file |\n"
                      "|---:|---|---|---|---|---|\n") if linked else None
            self.setup_project([(name, "QUEUED", "—") for name in names], header=header)
            if linked:
                rows = "".join(
                    f"| {n} | {name} | P1 | QUEUED | — | [t](tasks/M37/{name}.md) |\n"
                    for n, name in enumerate(names, 1))
                self.write(self.project, "docs/TASK_QUEUE.md", "# Q\n\n" + header + rows)
                self.commit(self.project, "links")
            seen: list[list[str]] = []
            real = subprocess.run

            def counting(command, *args, **kwargs):
                seen.append(list(command))
                return real(command, *args, **kwargs)

            with mock.patch.object(subprocess, "run", side_effect=counting):
                console.load_snapshot(self.project, console.IdentityCache())
            return len(seen)

        for count in (2, 12):
            self.assertEqual(calls(count, linked=False), calls(count, linked=True), count)


class RefreshCostTest(RepoCase):
    """The cost of a refresh must not grow with the number of known tasks."""

    queue = LeanEffectiveStateTest.queue
    setup_project = LeanEffectiveStateTest.setup_project

    def setup_with_history(self, archived: int) -> None:
        self.setup_project({"001": " ", "002": " "})
        queue = (self.project / "tasks/QUEUE.md").read_text(encoding="utf-8")
        history = "".join(f"| `[x]` | {100 + n} | Done {n} | P2 | — | — |\n" for n in range(archived))
        self.write(self.project, "tasks/QUEUE.md", queue + history)
        self.commit(self.project, "history")

    def subprocess_calls(self, cache: console.IdentityCache | None) -> list[list[str]]:
        real = subprocess.run
        calls: list[list[str]] = []

        def counting(command, *args, **kwargs):
            calls.append(list(command))
            return real(command, *args, **kwargs)

        with mock.patch.object(subprocess, "run", side_effect=counting):
            console.load_snapshot(self.project, cache)
        return calls

    def test_subprocess_work_does_not_grow_with_known_tasks(self) -> None:
        self.setup_with_history(2)
        small = self.subprocess_calls(console.IdentityCache())
        self.setup_with_history(40)
        large = self.subprocess_calls(console.IdentityCache())
        self.assertEqual(len(small), len(large))
        checks = [call for call in large if "check-ref-format" in call]
        self.assertEqual(len(checks), 2, "one ref check per open task")

    def test_refresh_reads_worktree_queue_only_for_dirty_worktrees(self) -> None:
        statuses = {f"{number:03}": " " for number in range(1, 6)}
        self.setup_project(statuses)
        worktrees = {task_id: self.worktree(f"task-{task_id}") for task_id in statuses}
        self.write(worktrees["001"], "scratch.txt", "uncommitted")
        reads: list[Path] = []
        original = console._read_text

        def observing(path: Path) -> str:
            reads.append(path)
            return original(path)

        with mock.patch.object(console, "_read_text", side_effect=observing):
            console.load_snapshot(self.project, console.IdentityCache())
        self.assertIn(worktrees["001"] / "tasks/QUEUE.md", reads)
        for task_id, worktree in worktrees.items():
            if task_id != "001":
                self.assertNotIn(worktree / "tasks/QUEUE.md", reads)

    def test_warm_refresh_resolves_no_identity_and_spawns_no_ref_check(self) -> None:
        self.setup_with_history(5)
        cache = console.IdentityCache()
        self.subprocess_calls(cache)
        warm = self.subprocess_calls(cache)
        self.assertEqual([call for call in warm if "check-ref-format" in call], [])

    def test_identity_is_resolved_once_until_the_declaration_changes(self) -> None:
        self.setup_with_history(1)
        cache = console.IdentityCache()
        with mock.patch.object(console, "resolve_task_identity",
                               wraps=console.resolve_task_identity) as resolver:
            console.load_snapshot(self.project, cache)
            console.load_snapshot(self.project, cache)
            self.assertEqual(resolver.call_count, 2)
            self.write(self.project, ".meridian/task-identity.json",
                       json.dumps({"version": 1, "mode": "opaque"}))
            console.load_snapshot(self.project, cache)
            self.assertEqual(resolver.call_count, 4)
            console.load_snapshot(self.project, cache)
            self.assertEqual(resolver.call_count, 4)

    def test_failed_resolution_is_not_cached(self) -> None:
        cache = console.IdentityCache()
        self.setup_with_history(1)
        with self.assertRaises(console.MeridianError):
            cache.resolve(self.project, "999")
        self.write(self.project, "tasks/999-task.md", "# Task 999\n\n> **ID**: `999`\n")
        self.assertEqual(cache.resolve(self.project, "999").canonical_id, "999")


class BackgroundRefreshTest(unittest.TestCase):
    def wait_idle(self, state: console.ConsoleState) -> None:
        deadline = time.monotonic() + 5
        while state.refreshing and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(state.refreshing)

    def snapshot(self, marker: str) -> console.Snapshot:
        return console.Snapshot(
            project=Path("/p"), queue=Path("/p/q"), branch=marker, git_summary="clean",
            git_changes=0, tasks=(), done_count=0,
        )

    def test_refresh_is_non_blocking_single_flight_and_published_atomically(self) -> None:
        state = console.ConsoleState(Path("/p"))
        state.snapshot = self.snapshot("old")
        release = threading.Event()
        started = threading.Event()

        def slow(_project, _identities):
            started.set()
            release.wait(5)
            return self.snapshot("new")

        with mock.patch.object(console, "load_snapshot", side_effect=slow) as loader:
            began = time.monotonic()
            self.assertTrue(state.start_refresh())
            self.assertLess(time.monotonic() - began, 1)
            self.assertTrue(started.wait(5))
            self.assertFalse(state.start_refresh(), "refreshes must not overlap")
            state.apply_pending()
            self.assertEqual(state.snapshot.branch, "old")
            release.set()
            self.wait_idle(state)
            self.assertEqual(state.snapshot.branch, "old", "published only when applied")
            state.apply_pending()
            self.assertEqual(state.snapshot.branch, "new")
            self.assertIsNone(state.error)
            self.assertEqual(loader.call_count, 1)

    def test_failed_background_refresh_keeps_last_snapshot_and_marks_it_stale(self) -> None:
        state = console.ConsoleState(Path("/p"))
        state.snapshot = self.snapshot("old")
        with mock.patch.object(console, "load_snapshot",
                               side_effect=console.ConsoleError("boom")):
            self.assertTrue(state.start_refresh())
            self.wait_idle(state)
        state.apply_pending()
        self.assertEqual(state.snapshot.branch, "old")
        self.assertEqual(state.error, "boom")
        with mock.patch.object(console, "load_snapshot", side_effect=RuntimeError("bug")):
            self.assertTrue(state.start_refresh())
            self.wait_idle(state)
        state.apply_pending()
        self.assertEqual(state.snapshot.branch, "old")
        self.assertIn("bug", state.error)
        with mock.patch.object(console, "load_snapshot", return_value=self.snapshot("fresh")):
            self.assertTrue(state.start_refresh())
            self.wait_idle(state)
        state.apply_pending()
        self.assertEqual((state.snapshot.branch, state.error), ("fresh", None))


class WorkflowModeLockTest(RepoCase):
    def test_missing_unknown_and_double_locks_are_explicit_errors(self) -> None:
        (self.project / "PROJECT_WORKFLOW.md").unlink()
        with self.assertRaisesRegex(console.ConsoleError, "PROJECT_WORKFLOW.md is missing") as raised:
            console.load_snapshot(self.project)
        self.assertNotIn("--mode", str(raised.exception))
        self.write(self.project, "PROJECT_WORKFLOW.md", "# nothing\n")
        with self.assertRaisesRegex(console.ConsoleError, "no recognized mode lock"):
            console.load_snapshot(self.project)
        self.write(self.project, "PROJECT_WORKFLOW.md", "LEAN_DELIVERY GOVERNED_SDD\n")
        with self.assertRaisesRegex(console.ConsoleError, "both mode locks"):
            console.load_snapshot(self.project)


if __name__ == "__main__":
    unittest.main()
