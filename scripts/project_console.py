#!/usr/bin/env python3
"""Local terminal dashboard for a Meridian project."""

from __future__ import annotations

import argparse
import curses
import os
import re
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
from meridian import resolve_project_locations


STATUS = {"`[ ]`": "TODO", "`[/]`": "IN_PROGRESS", "`[x]`": "DONE"}
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)")


class ConsoleError(Exception):
    """Project state could not be read without ambiguity."""


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    status: str
    phase: str
    dependencies: tuple[str, ...]
    path: Path
    objective: tuple[str, ...]
    criteria: tuple[str, ...]
    worktree: str | None = None
    readiness: str = ""
    updated_at: int | None = None

    @property
    def launch_command(self) -> str | None:
        return f"Proceed with {self.task_id}" if self.readiness == "READY" else None

    @property
    def next_action(self) -> str:
        if self.readiness == "READY":
            return f"If assigned: {self.launch_command}"
        if self.readiness == "IN PROGRESS":
            return "Continue the assigned task in its worktree"
        if self.readiness.startswith("BLOCKED"):
            return "Wait for the listed dependencies to complete"
        return "Resolve the missing dependency record"


@dataclass(frozen=True)
class Snapshot:
    project: Path
    queue: Path
    branch: str
    git_summary: str
    git_changes: int
    tasks: tuple[Task, ...]
    done_count: int


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ConsoleError(f"Cannot read {path}: {error}") from error


def _queue_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    phase = ""
    for line_number, line in enumerate(_read_text(path).splitlines(), 1):
        if line.startswith("### "):
            phase = line[4:].strip()
        if not line.startswith("|"):
            headers = []
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if "Status" in cells and "ID" in cells:
            headers = cells
            continue
        if not headers or len(cells) != len(headers) or set("".join(cells)) <= {"-", ":"}:
            continue
        row = dict(zip(headers, cells))
        if row.get("Status") not in STATUS:
            raise ConsoleError(f"Unknown task status in {path}:{line_number}: {row.get('Status')}")
        task_id = row["ID"].strip("`")
        if not ID_PATTERN.fullmatch(task_id):
            raise ConsoleError(f"Invalid task ID in {path}:{line_number}")
        row["ID"] = task_id
        row["Phase"] = phase
        rows.append(row)
    return rows


def _task_path(project: Path, queue: Path, row: dict[str, str]) -> Path:
    cell = row.get("File", row.get("Task File", ""))
    match = LINK_PATTERN.fullmatch(cell)
    if not match:
        raise ConsoleError(f"Task {row['ID']} has no unambiguous file link")
    path = (queue.parent / match.group(1)).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise ConsoleError(f"Task {row['ID']} file is unavailable within the project: {path}")
    return path


def _section(text: str, name: str) -> tuple[str, ...]:
    inside = False
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = name.casefold() in line.casefold()
        elif inside and line.strip():
            lines.append(line.strip())
    return tuple(lines)


def _git(project: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ("git", "-C", str(project), *args),
            capture_output=True, text=True, check=False, timeout=5,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConsoleError(f"Git {' '.join(args)} failed: {error}") from error
    if result.returncode:
        raise ConsoleError(f"Git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _worktrees(project: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    path = ""
    for line in _git(project, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line[9:]
        elif line.startswith("branch refs/heads/") and path:
            records[line.removeprefix("branch refs/heads/")] = path
    return records


def _committed_update(project: Path, path: Path) -> int | None:
    """Return the last committed change to a task record, when Git knows it."""
    relative = path.relative_to(project).as_posix()
    try:
        value = _git(project, "log", "-1", "--format=%ct", "--", relative).strip()
        return int(value) if value else None
    except (ConsoleError, ValueError):
        return None


def load_snapshot(project: Path) -> Snapshot:
    project = project.expanduser().resolve()
    workflow = project / "PROJECT_WORKFLOW.md"
    if not workflow.is_file():
        raise ConsoleError(f"No PROJECT_WORKFLOW.md in {project}")
    if "LEAN_DELIVERY" not in _read_text(workflow):
        raise ConsoleError("This console currently supports LEAN_DELIVERY queues")
    try:
        locations = resolve_project_locations(project)
    except Exception as error:
        raise ConsoleError(f"Cannot resolve canonical queue: {error}") from error
    queue = project / locations.queue
    archive = queue.with_name("QUEUE_ARCHIVE.md")
    active_rows = _queue_rows(queue)
    archived_rows = _queue_rows(archive) if archive.is_file() else []
    by_id: dict[str, str] = {}
    for row in (*active_rows, *archived_rows):
        task_id = row["ID"]
        if task_id in by_id:
            raise ConsoleError(f"Duplicate task ID across queues: {task_id}")
        by_id[task_id] = STATUS[row["Status"]]
    status_lines = _git(project, "status", "--porcelain=v1", "--branch").splitlines()
    if not status_lines:
        raise ConsoleError("Git status returned no branch line")
    branch_line = status_lines[0].removeprefix("## ")
    branch = branch_line.split("...", 1)[0].split(" [", 1)[0]
    worktrees = _worktrees(project)
    tasks: list[Task] = []
    for row in active_rows:
        status = STATUS[row["Status"]]
        if status == "DONE":
            continue
        raw_dependencies = row.get("Depends on", row.get("Dependencies", ""))
        dependencies = tuple(
            item.strip().strip("`") for item in raw_dependencies.split(",")
            if item.strip() not in ("", "—", "-")
        )
        if any(not ID_PATTERN.fullmatch(item) for item in dependencies):
            raise ConsoleError(f"Task {row['ID']} has an invalid dependency")
        missing = [item for item in dependencies if item not in by_id]
        waiting = [item for item in dependencies if by_id.get(item) not in (None, "DONE")]
        if missing:
            readiness = "UNKNOWN: missing " + ", ".join(missing)
        elif waiting:
            readiness = "BLOCKED: " + ", ".join(waiting)
        elif status == "IN_PROGRESS":
            readiness = "IN PROGRESS"
        else:
            readiness = "READY"
        path = _task_path(project, queue, row)
        task_text = _read_text(path)
        branch_name = f"task-{int(row['ID']):03d}" if row["ID"].isdigit() else row["ID"].lower()
        tasks.append(Task(
            task_id=row["ID"], title=row.get("Title", ""), status=status,
            phase=row["Phase"], dependencies=dependencies, path=path,
            objective=_section(task_text, "Objective"),
            criteria=_section(task_text, "Acceptance Criteria"),
            worktree=worktrees.get(branch_name), readiness=readiness,
            updated_at=_committed_update(project, path),
        ))
    return Snapshot(
        project=project, queue=queue, branch=branch_line,
        git_summary="clean" if len(status_lines) == 1 else f"{len(status_lines) - 1} changed paths",
        git_changes=len(status_lines) - 1, tasks=tuple(tasks),
        done_count=sum(status == "DONE" for status in by_id.values()),
    )


class ConsoleState:
    def __init__(self, project: Path):
        self.project = project
        self.snapshot: Snapshot | None = None
        self.last_success: datetime | None = None
        self.error: str | None = None

    def refresh(self) -> None:
        try:
            candidate = load_snapshot(self.project)
        except ConsoleError as error:
            self.error = str(error)
            return
        self.snapshot = candidate
        self.last_success = datetime.now().astimezone()
        self.error = None


def one_shot(state: ConsoleState) -> str:
    if state.error:
        return f"STALE: {state.error}"
    snapshot = state.snapshot
    if snapshot is None:
        return "No project snapshot available"
    stamp = state.last_success.strftime("%Y-%m-%d %H:%M:%S %Z") if state.last_success else "unknown"
    lines = [
        f"MERIDIAN | {snapshot.project} | {snapshot.branch} | {snapshot.git_summary}",
        f"Updated: {stamp} | Open: {len(snapshot.tasks)} | Done: {snapshot.done_count}",
    ]
    for task in snapshot.tasks:
        objective = " ".join(task.objective)
        lines.append(f"{task.task_id} [{task.readiness}] {task.title}")
        if objective:
            lines.append(f"  {objective}")
        lines.append(f"  Dependencies: {', '.join(task.dependencies) or 'none'}")
        lines.append(f"  Next action: {task.next_action}")
        if task.worktree:
            lines.append(f"  Worktree: {task.worktree}")
    lines.append("Agent activity: unavailable (no verified local source)")
    return "\n".join(lines)


def _put(screen, y: int, x: int, value: str, width: int, attr: int = 0) -> None:
    height, screen_width = screen.getmaxyx()
    if y < 0 or y >= height or x >= screen_width or width <= 0:
        return
    try:
        screen.addnstr(y, x, value, min(width, screen_width - x - 1), attr)
    except curses.error:
        pass


def _fill(screen, y: int, x: int, width: int, attr: int) -> None:
    _put(screen, y, x, " " * max(0, width), width, attr)


def _palette(screen) -> dict[str, int]:
    """Use the terminal background while preserving console foreground colors."""
    if not curses.has_colors():
        screen.bkgd(" ", curses.A_NORMAL)
        return {
            "base": curses.A_NORMAL, "text": curses.A_BOLD,
            "muted": curses.A_DIM, "line": curses.A_DIM,
            "ready": curses.A_BOLD, "working": curses.A_BOLD,
            "blocked": curses.A_BOLD, "unknown": curses.A_BOLD,
            "stale": curses.A_REVERSE | curses.A_BOLD,
            "selected": curses.A_REVERSE | curses.A_BOLD,
            "tab": curses.A_REVERSE | curses.A_BOLD,
            "tab_underline": curses.A_BOLD,
            "title": curses.A_BOLD,
            "action": curses.A_BOLD,
        }
    curses.start_color()
    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = 233 if curses.COLORS >= 256 else curses.COLOR_BLACK
    if curses.COLORS >= 256:
        colors = (
            (253, background), (253, background), (245, background),
            (240, background), (80, background), (141, background),
            (221, background), (203, background), (231, 52), (16, 75),
            (253, 238), (181, background), (150, background),
            (117, background),
        )
    else:
        colors = (
            (curses.COLOR_WHITE, background),
            (curses.COLOR_WHITE, background),
            (curses.COLOR_WHITE, background),
            (curses.COLOR_WHITE, background),
            (curses.COLOR_CYAN, background),
            (curses.COLOR_MAGENTA, background),
            (curses.COLOR_YELLOW, background),
            (curses.COLOR_RED, background),
            (curses.COLOR_WHITE, curses.COLOR_RED),
            (curses.COLOR_BLACK, curses.COLOR_CYAN),
            (curses.COLOR_WHITE, curses.COLOR_BLUE),
            (curses.COLOR_MAGENTA, background),
            (curses.COLOR_GREEN, background),
            (curses.COLOR_CYAN, background),
        )
    names = ("base", "text", "muted", "line", "ready", "working",
             "blocked", "unknown", "stale", "selected", "tab", "title", "action",
             "tab_underline")
    palette = {}
    for index, (name, (foreground, background)) in enumerate(zip(names, colors), 1):
        curses.init_pair(index, foreground, background)
        palette[name] = curses.color_pair(index)
    palette["text"] |= curses.A_BOLD
    palette["title"] |= curses.A_BOLD
    screen.bkgd(" ", palette["base"])
    return palette


def _wrapped(lines: tuple[str, ...] | list[str], width: int) -> list[str]:
    output: list[str] = []
    for line in lines:
        output.extend(textwrap.wrap(line, max(10, width), replace_whitespace=False) or [""])
    return output


def _state_label(task: Task) -> tuple[str, str]:
    if task.readiness == "READY":
        return "Ready", "ready"
    if task.readiness == "IN PROGRESS":
        return "Working", "working"
    if task.readiness.startswith("BLOCKED"):
        return "Blocked", "blocked"
    return "Unknown", "unknown"


def _filter_counts(snapshot: Snapshot | None) -> dict[str, int]:
    counts = {name: 0 for name in ("Ready", "Working", "Blocked", "Unknown")}
    for task in snapshot.tasks if snapshot else ():
        counts[_state_label(task)[0]] += 1
    return counts


def _cycle_filter(snapshot: Snapshot | None, current: str, direction: int) -> str:
    filters = ("All", "Ready", "Working", "Blocked", "Unknown")
    counts = _filter_counts(snapshot)
    start = filters.index(current)
    for step in range(1, len(filters) + 1):
        candidate = filters[(start + direction * step) % len(filters)]
        if candidate == "All" or counts[candidate]:
            return candidate
    return "All"


def _tab_at(snapshot: Snapshot | None, x: int, y: int) -> str | None:
    if y != 1:
        return None
    counts = _filter_counts(snapshot)
    tabs = (("All", sum(counts.values())), *counts.items())
    left = 1
    for name, count in tabs:
        right = left + len(f" {name} {count} ")
        if left <= x < right:
            return name
        left = right + 1
    return None


def _copy_to_clipboard(value: str) -> bool:
    if sys.platform == "darwin":
        commands = (("pbcopy",),)
    elif sys.platform == "win32":
        commands = (("clip",),)
    else:
        commands = (("wl-copy",), ("xclip", "-selection", "clipboard"))
    for command in commands:
        try:
            result = subprocess.run(command, input=value, text=True,
                                    capture_output=True, check=False, timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return True
    return False


def _action_hit(x: int, y: int,
                bounds: tuple[int, int, set[int]] | None) -> bool:
    return bool(bounds and bounds[0] <= x <= bounds[1] and y in bounds[2])


def _age(timestamp: int | None) -> str:
    if timestamp is None:
        return "—"
    seconds = max(0, int(time.time()) - timestamp)
    if seconds < 60:
        return "now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def _clip(value: str, width: int) -> str:
    return value if len(value) <= width else value[:max(0, width - 1)] + "…"


def _detail_lines(task: Task, width: int, palette: dict[str, int],
                  compact: bool = False) -> list[tuple[str, int]]:
    lines: list[tuple[str, int]] = []

    def add(value: str, style: str = "base") -> None:
        for part in _wrapped([value], width):
            lines.append((part, palette[style]))

    label, color = _state_label(task)
    add("Task details", "text")
    add("")
    if not compact:
        add("")
    add(task.title, "title")
    add(f"○ {label}", color)
    add("")
    add("Objective", "muted")
    for value in task.objective or ("Unavailable",):
        add(value)
    if not compact:
        add("")
    add("Dependencies", "muted")
    add(", ".join(task.dependencies) or "none")
    if not compact:
        add("")
    add("─" * min(20, width), "line")
    if not compact:
        add("")
    add("Next directive", "muted")
    command = task.launch_command
    add(f"{command}  [copy]" if command else task.next_action, "action")
    return lines


def _visible_tasks(snapshot: Snapshot | None, status_filter: str, search: str) -> list[Task]:
    tasks = snapshot.tasks if snapshot else ()
    return [
        task for task in tasks
        if (status_filter == "All" or _state_label(task)[0] == status_filter)
        and search.casefold() in f"{task.task_id} {task.title}".casefold()
    ]


def _draw_header(screen, state: ConsoleState, palette: dict[str, int],
                 status_filter: str, width: int) -> None:
    snapshot = state.snapshot
    project_name = snapshot.project.name if snapshot else state.project.name
    branch = snapshot.branch.split("...", 1)[0] if snapshot else "unavailable"
    summary = snapshot.git_summary if snapshot else "unknown"
    left = f"Project command center  {project_name}  {branch}"
    _put(screen, 0, 1, left, width - 2, palette["text"])
    ahead = re.search(r"\[ahead (\d+)", snapshot.branch) if snapshot else None
    local = f"↑ {ahead.group(1)} local · " if ahead else ""
    age = _age(int(state.last_success.timestamp())) if state.last_success else "never"
    right = f"{local}{summary} · refreshed {age}"
    right_x = width - len(right) - 2
    if right_x > len(left) + 2:
        _put(screen, 0, right_x, right, len(right), palette["blocked"])
    if state.error:
        _put(screen, 1, max(1, width - 9), "STALE", 7, palette["stale"])
    counts = _filter_counts(snapshot)
    tabs = (("All", sum(counts.values())), *((name, count) for name, count in counts.items()))
    x = 1
    for name, count in tabs:
        label = f" {name} {count} "
        attr = palette["tab"] if name == status_filter else palette[
            {"All": "text", "Ready": "ready", "Working": "working",
             "Blocked": "blocked", "Unknown": "unknown"}[name]
        ]
        _put(screen, 1, x, label, len(label), attr)
        x += len(label) + 1
    if snapshot and x + 9 < width:
        _put(screen, 1, x + 1, f"Done {snapshot.done_count}", width - x - 2, palette["muted"])
    hint = "tab/shift+tab filter"
    if width - len(hint) - 2 > x + 9:
        _put(screen, 1, width - len(hint) - 2, hint, len(hint), palette["muted"])
    _put(screen, 2, 0, "─" * max(0, width - 1), width - 1, palette["line"])
    selected_x = 1
    for name, count in tabs:
        label_width = len(f" {name} {count} ")
        if name == status_filter:
            _put(screen, 2, selected_x + 1, "━" * max(1, label_width - 2),
                 label_width - 2, palette["tab_underline"])
            break
        selected_x += label_width + 1


def _draw_list(screen, tasks: list[Task], selected_id: str | None,
               offset: int, left_width: int, height: int,
               palette: dict[str, int]) -> int:
    status_width = 11
    age_width = 9
    # The title starts at column 9 and leaves two columns before status.
    title_width = max(8, left_width - status_width - age_width - 13)
    _put(screen, 3, 2, "Tasks", title_width, palette["muted"])
    _put(screen, 3, left_width - status_width - age_width - 2, "Status", status_width, palette["muted"])
    _put(screen, 3, left_width - age_width - 1, "Updated", age_width, palette["muted"])
    entries: list[tuple[str, Task | None]] = []
    phase = None
    for task in tasks:
        if task.phase != phase:
            phase = task.phase
            entries.append((phase, None))
        entries.append(("", task))
    body_top = 5
    body_lines = max(1, height - body_top - 2)
    selected_line = next((i for i, (_, task) in enumerate(entries)
                          if task and task.task_id == selected_id), 0)
    if selected_line < offset:
        offset = selected_line
    if selected_line >= offset + body_lines:
        offset = selected_line - body_lines + 1
    offset = min(offset, max(0, len(entries) - body_lines))
    for line_number, (heading, task) in enumerate(entries[offset:offset + body_lines], body_top):
        if task is None:
            _put(screen, line_number, 1, heading, left_width - 3, palette["muted"])
            continue
        selected = task.task_id == selected_id
        row_attr = palette["selected"] if selected else palette["base"]
        _fill(screen, line_number, 0, left_width - 1, row_attr)
        _put(screen, line_number, 1, "›" if selected else " ", 1, row_attr)
        _put(screen, line_number, 3, task.task_id, 5, row_attr if selected else palette["muted"])
        _put(screen, line_number, 9, _clip(f"○ {task.title}", title_width),
             title_width, row_attr)
        label, color = _state_label(task)
        _put(screen, line_number, left_width - status_width - age_width - 2,
             label, status_width, row_attr if selected else palette[color])
        _put(screen, line_number, left_width - age_width - 1,
             _age(task.updated_at), age_width, row_attr if selected else palette["muted"])
    if not tasks:
        _put(screen, body_top + 1, 2, "No matching open tasks", left_width - 4, palette["muted"])
    return offset


def _draw_detail(screen, task: Task | None, x: int, top: int, width: int,
                 height: int, offset: int, palette: dict[str, int]) -> set[int]:
    if task is None:
        _put(screen, top, x, "No task selected", width, palette["muted"])
        return set()
    lines = _detail_lines(task, width - 2, palette, compact=height < 30)
    body_lines = max(1, height - top - 2)
    offset = min(offset, max(0, len(lines) - body_lines))
    for y, (value, attr) in enumerate(lines[offset:offset + body_lines], top):
        _put(screen, y, x, value, width - 1, attr)
    if not task.launch_command:
        return set()
    action_start = next(i for i, (value, _) in enumerate(lines)
                        if value == "Next directive") + 1
    return {
        top + i - offset for i in range(action_start, len(lines))
        if offset <= i < offset + body_lines
    }


def run_terminal(screen, state: ConsoleState, interval: float) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    palette = _palette(screen)
    try:
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED)
    except curses.error:
        pass
    screen.timeout(100)
    selected_id: str | None = None
    offset = 0
    detail_offset = 0
    search = ""
    searching = False
    help_visible = False
    detail_open = False
    status_filter = "All"
    last_poll = 0.0
    notice = ""
    notice_until = 0.0
    while True:
        now = time.monotonic()
        if now - last_poll >= interval:
            state.refresh()
            last_poll = now
        snapshot = state.snapshot
        visible = _visible_tasks(snapshot, status_filter, search)
        if selected_id not in {task.task_id for task in visible}:
            selected_id = visible[0].task_id if visible else None
            detail_offset = 0
        selected_task = next((task for task in visible if task.task_id == selected_id), None)
        height, width = screen.getmaxyx()
        screen.erase()
        action_bounds: tuple[int, int, set[int]] | None = None
        if height < 12 or width < 50:
            _put(screen, 0, 0, "Terminal too small (minimum 50x12). Press q to quit.", width,
                 palette["text"])
        else:
            _draw_header(screen, state, palette, status_filter, width)
            wide = width >= 110
            if help_visible:
                help_lines = (
                    "Navigation", "↑/↓ or j/k  Select task", "Tab/Shift+Tab  Filter by status",
                    "Enter  Open full task details", "Esc  Return to task list",
                    "/  Search task ID or title", "[ / ]  Scroll task details",
                    "c or click [copy]  Copy a ready task directive",
                    "Tab  Cycle All and nonempty states; click any tab",
                    "r  Refresh now", "q  Quit", "",
                    "Project state is read-only; copy writes to the clipboard.",
                    "Updated is the last committed change to the task file.",
                    "Agent activity is unavailable without a verified source.",
                    "It does not control agents or fetch from the network.",
                )
                for y, line in enumerate(help_lines, 4):
                    _put(screen, y, 2, line, width - 4, palette["text"] if y == 4 else palette["base"])
            elif detail_open:
                action_rows = _draw_detail(screen, selected_task, 2, 4, width - 4,
                                           height, detail_offset, palette)
                action_bounds = (2, width - 4, action_rows)
            else:
                left_width = int(width * .68) if wide else width
                offset = _draw_list(screen, visible, selected_id, offset, left_width,
                                    height, palette)
                if wide:
                    divider = left_width - 1
                    for y in range(3, height - 2):
                        _put(screen, y, divider, "│", 1, palette["line"])
                    detail_x = left_width + 1
                    action_rows = _draw_detail(screen, selected_task, detail_x, 4,
                                               width - left_width - 2, height,
                                               detail_offset, palette)
                    action_bounds = (detail_x, width - 3, action_rows)
            if notice and time.monotonic() < notice_until:
                footer = notice
            elif state.error:
                footer = f"STALE: {state.error}"
            elif searching:
                footer = f"Search: {search}"
            elif detail_open or help_visible:
                footer = "Esc back   [/] scroll   r refresh   q quit"
            else:
                footer = "? help   ↑/↓ move   tab filter   enter details   c copy   / search   r refresh   q quit"
            _put(screen, height - 2, 0, "─" * max(0, width - 1),
                 width - 1, palette["line"])
            _put(screen, height - 1, 1, footer, width - 2,
                 palette["stale"] if state.error else palette["muted"])
        screen.refresh()
        key = screen.getch()
        if key == -1:
            continue
        if key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, button_state = curses.getmouse()
            except curses.error:
                continue
            if not button_state & (curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED):
                continue
            tab = _tab_at(snapshot, mouse_x, mouse_y)
            if tab and not help_visible and not detail_open:
                status_filter = tab
                offset = detail_offset = 0
            elif selected_task and _action_hit(mouse_x, mouse_y, action_bounds):
                command = selected_task.launch_command
                if command:
                    notice = (f"Copied: {command}" if _copy_to_clipboard(command)
                              else "Clipboard unavailable")
                    notice_until = time.monotonic() + 2
            continue
        if searching:
            if key in (10, 13, 27):
                searching = False
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search = search[:-1]
                detail_offset = offset = 0
            elif 32 <= key <= 126:
                search += chr(key)
                detail_offset = offset = 0
            continue
        if key == 27:
            detail_open = help_visible = False
            continue
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("j"), curses.KEY_DOWN) and not detail_open and not help_visible:
            if visible:
                index = next((i for i, task in enumerate(visible)
                              if task.task_id == selected_id), 0)
                selected_id = visible[min(index + 1, len(visible) - 1)].task_id
            detail_offset = 0
        elif key in (ord("k"), curses.KEY_UP) and not detail_open and not help_visible:
            if visible:
                index = next((i for i, task in enumerate(visible)
                              if task.task_id == selected_id), 0)
                selected_id = visible[max(0, index - 1)].task_id
            detail_offset = 0
        elif key == ord("["):
            detail_offset = max(0, detail_offset - 1)
        elif key == ord("]") or key == curses.KEY_NPAGE:
            detail_offset += 1
        elif key == curses.KEY_PPAGE:
            detail_offset = max(0, detail_offset - 1)
        elif key in (9, curses.KEY_BTAB) and not detail_open and not help_visible:
            direction = -1 if key == curses.KEY_BTAB else 1
            status_filter = _cycle_filter(snapshot, status_filter, direction)
            offset = detail_offset = 0
        elif key in (10, 13) and selected_task and not help_visible:
            detail_open = True
            detail_offset = 0
        elif key == ord("/"):
            searching = True
            search = ""
        elif key == ord("r"):
            state.refresh()
            last_poll = time.monotonic()
        elif key == ord("c") and selected_task and not help_visible:
            command = selected_task.launch_command
            notice = (f"Copied: {command}" if command and _copy_to_clipboard(command)
                      else "Clipboard unavailable" if command
                      else "No launch command for this task")
            notice_until = time.monotonic() + 2
        elif key == ord("?"):
            help_visible = not help_visible


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--interval", type=float, default=2.0,
                        help="seconds between local refreshes (default: 2)")
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    args = parser.parse_args(argv)
    if not 0.2 <= args.interval <= 60:
        parser.error("--interval must be between 0.2 and 60 seconds")
    state = ConsoleState(args.project)
    state.refresh()
    if args.once:
        print(one_shot(state))
        return 1 if state.error else 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("interactive mode requires a terminal; use --once")
    curses.wrapper(run_terminal, state, args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
