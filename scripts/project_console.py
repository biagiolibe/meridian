#!/usr/bin/env python3
"""Read-only terminal dashboard for a local Meridian project."""

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

    @property
    def next_action(self) -> str:
        if self.readiness == "READY":
            return f"If assigned: Proceed with {self.task_id}"
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
    screen.addnstr(y, x, value, min(width, screen_width - x - 1), attr)


def _wrapped(lines: tuple[str, ...] | list[str], width: int) -> list[str]:
    output: list[str] = []
    for line in lines:
        output.extend(textwrap.wrap(line, max(10, width), replace_whitespace=False) or [""])
    return output


def run_terminal(screen, state: ConsoleState, interval: float) -> None:
    curses.curs_set(0)
    screen.timeout(100)
    selected = 0
    offset = 0
    detail_offset = 0
    search = ""
    searching = False
    help_visible = False
    last_poll = 0.0
    while True:
        now = time.monotonic()
        if now - last_poll >= interval:
            state.refresh()
            last_poll = now
        snapshot = state.snapshot
        tasks = list(snapshot.tasks) if snapshot else []
        visible = [task for task in tasks if search.casefold() in f"{task.task_id} {task.title}".casefold()]
        selected = min(selected, max(0, len(visible) - 1))
        height, width = screen.getmaxyx()
        screen.erase()
        if height < 10 or width < 65:
            _put(screen, 0, 0, "Terminal too small (minimum 65x10). Press q to quit.", width)
        else:
            heading = f"MERIDIAN | {snapshot.branch if snapshot else 'unavailable'} | {snapshot.git_summary if snapshot else 'unknown'}"
            _put(screen, 0, 0, heading, width, curses.A_BOLD)
            stamp = state.last_success.strftime("%H:%M:%S") if state.last_success else "never"
            status = f"Updated {stamp} | {len(tasks)} open | {snapshot.done_count if snapshot else 0} done"
            if state.error:
                status += f" | STALE: {state.error}"
            _put(screen, 1, 0, status, width, curses.A_REVERSE if state.error else 0)
            left = min(48, max(27, width // 2))
            _put(screen, 2, 0, "TASKS", left, curses.A_BOLD)
            _put(screen, 2, left + 1, "DETAIL", width - left - 2, curses.A_BOLD)
            body_height = height - 5
            if selected < offset:
                offset = selected
            if selected >= offset + body_height:
                offset = selected - body_height + 1
            for y, task in enumerate(visible[offset:offset + body_height], 3):
                label = f"{task.task_id} {task.readiness:<11} {task.title}"
                _put(screen, y, 0, label, left, curses.A_REVERSE if offset + y - 3 == selected else 0)
            if visible:
                task = visible[selected]
                detail = [task.phase, f"{task.task_id} - {task.title}",
                          f"State: {task.status}; {task.readiness}",
                          f"Dependencies: {', '.join(task.dependencies) or 'none'}",
                          f"Next action: {task.next_action}",
                          f"Worktree: {task.worktree or 'none'}", "", "Objective:"]
                detail.extend(task.objective or ("Unavailable",))
                detail.extend(("", "Acceptance criteria:"))
                detail.extend(task.criteria or ("Unavailable",))
                rendered = _wrapped(detail, width - left - 3)
                for y, line in enumerate(rendered[detail_offset:detail_offset + body_height], 3):
                    _put(screen, y, left + 1, line, width - left - 2)
            else:
                _put(screen, 3, 0, "No matching open tasks", left)
            _put(screen, height - 2, 0, "Agent activity: unavailable (no verified local source)", width)
            footer = "Search: " + search if searching else "/ search  j/k move  [/] detail  r refresh  ? help  q quit"
            if help_visible:
                footer = "Read-only local view. No fetch, agent control, or writes. Press ? to close help."
            _put(screen, height - 1, 0, footer, width, curses.A_REVERSE)
        screen.refresh()
        key = screen.getch()
        if key == -1:
            continue
        if searching:
            if key in (10, 13, 27):
                searching = False
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search = search[:-1]
                selected = detail_offset = 0
            elif 32 <= key <= 126:
                search += chr(key)
                selected = detail_offset = 0
            continue
        if key in (ord("q"), ord("Q")):
            return
        if key in (ord("j"), curses.KEY_DOWN):
            selected = min(selected + 1, max(0, len(visible) - 1))
            detail_offset = 0
        elif key in (ord("k"), curses.KEY_UP):
            selected = max(0, selected - 1)
            detail_offset = 0
        elif key == ord("["):
            detail_offset = max(0, detail_offset - 1)
        elif key == ord("]"):
            detail_offset += 1
        elif key == ord("/"):
            searching = True
            search = ""
        elif key == ord("r"):
            state.refresh()
            last_poll = time.monotonic()
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
