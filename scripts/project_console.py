#!/usr/bin/env python3
"""Local terminal dashboard for a Meridian project."""

from __future__ import annotations

import argparse
import curses
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
from meridian import (
    TASK_IDENTITY_PATH, MeridianError, ResolvedTaskIdentity, detect_mode,
    resolve_project_locations, resolve_task_identity,
)
from console_workflow import (
    ID_PATTERN, PROFILES, BranchFacts, ConsoleError, QueueRow, Profile, effective_state,
    handoff_status, has_link, heading_title, is_task_record_path, latest_review_verdict,
    link_target, parse_queue, record_matches, record_status,
)


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    status: str
    phase: tuple[str, ...]
    dependencies: tuple[str, ...]
    path: Path | None
    objective: tuple[str, ...]
    criteria: tuple[str, ...]
    worktree: str | None = None
    readiness: str = ""
    updated_at: int | None = None
    lifecycle: str = "todo"
    source: str = "main"
    mismatch: str | None = None
    changes_requested: bool = False
    active_writer: bool = False
    registered_worktree: bool = False
    record_problem: str | None = None
    review: str | None = None
    dependency_states: tuple[tuple[str, str], ...] = ()
    workflow: str = "lean-delivery"

    @property
    def launch_command(self) -> str | None:
        if self.record_problem or self.readiness == "MISMATCH" or self.active_writer:
            return None
        if self.lifecycle == "todo" and self.readiness == "READY":
            return f"Proceed with {self.task_id}"
        if self.lifecycle == "ready_for_review":
            if self.workflow == "lean-delivery":
                return f"Review {self.task_id}"
            if self.workflow == "governed-sdd" and self.review == "REQUIRED":
                return f"Review {self.task_id}"
        if (self.workflow == "governed-sdd" and self.lifecycle == "in_progress"
                and self.changes_requested):
            return f"Address review {self.task_id}"
        return None

    @property
    def markers(self) -> tuple[str, ...]:
        return (
            *(("changes requested",) if self.changes_requested else ()),
            *(("active writer",) if self.active_writer else ()),
            *(("registered worktree",) if self.registered_worktree else ()),
        )

    @property
    def next_action(self) -> str:
        if self.record_problem and self.readiness != "MISMATCH":
            return f"Resolve the task record: {self.record_problem}"
        if self.readiness == "READY":
            return f"If assigned: {self.launch_command}"
        if self.readiness == "MISMATCH":
            return f"Resolve the state disagreement: {self.mismatch}"
        if self.readiness == "READY FOR REVIEW":
            return "Awaiting review of the task branch"
        if self.readiness == "DONE ON BRANCH":
            return "Awaiting integration of the task branch"
        if self.readiness == "IN PROGRESS":
            return "Continue the assigned task in its worktree"
        if self.readiness.startswith("BLOCKED"):
            return "Wait for the listed dependencies to complete"
        return "Resolve the missing dependency record"


@dataclass(frozen=True)
class LaunchRequest:
    """A confirmed, safe-to-quote invocation for a new iTerm2 tab."""

    agent: str
    directive: str
    directory: Path

    @property
    def shell_command(self) -> str:
        return "cd " + shlex.quote(str(self.directory)) + " && exec " + shlex.join(
            (self.agent, self.directive)
        )


def _launch_request(task: Task, project: Path, agent: str) -> tuple[LaunchRequest | None, str | None]:
    """Revalidate a selected task before a confirmation can offer a launch."""
    if agent not in ("claude", "codex"):
        return None, "Choose Claude Code or Codex"
    if not ID_PATTERN.fullmatch(task.task_id):
        return None, "Refusing launch: task ID no longer matches the workflow rules"
    directive = task.launch_command
    if not directive:
        return None, "This task is not eligible to launch; use [copy] if a directive is shown"
    directory, error = _primary_checkout(project)
    if error:
        return None, error
    return LaunchRequest(agent, directive, directory), None


def _apple_script(command: str) -> str:
    """Return the sole iTerm2 automation payload, with AppleScript quoting."""
    quoted = command.replace("\\", "\\\\").replace('"', '\\"')
    return "\n".join((
        'tell application "iTerm2"',
        "activate",
        "if (count of windows) is 0 then",
        "create window with default profile",
        "else",
        "tell current window to create tab with default profile",
        "end if",
        "tell current session of current tab of current window",
        f'write text "{quoted}"',
        "end tell",
        "end tell",
    ))


def _start_launch(request: LaunchRequest) -> tuple[bool, str]:
    """Open a new iTerm2 tab. This is called only after UI confirmation."""
    if sys.platform != "darwin":
        return False, "Agent launch requires macOS and iTerm2; [copy] remains available"
    if shutil.which(request.agent) is None:
        return False, f"{request.agent} is not available on PATH; [copy] remains available"
    if shutil.which("osascript") is None:
        return False, "macOS osascript is unavailable; [copy] remains available"
    try:
        result = subprocess.run(
            ("osascript", "-e", _apple_script(request.shell_command)),
            capture_output=True, text=True, check=False, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "iTerm2 launch timed out; [copy] remains available"
    except OSError as error:
        return False, f"iTerm2 launch failed: {error}; [copy] remains available"
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        return False, (f"iTerm2 is unavailable or rejected launch: {detail}; [copy] remains available"
                       if detail else "iTerm2 launch failed; [copy] remains available")
    return True, f"Started {request.agent} in a new iTerm2 tab"


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


class RecordResolver:
    """Find task records for queue rows that carry no file link.

    The task roots are walked at most once per snapshot, and only when a row
    needs the search, so resolution adds no per-task subprocess work.
    """

    def __init__(self, project: Path, locations) -> None:
        self.project = project
        self.roots = tuple(root.as_posix() for root in locations.task_roots)
        self.excluded = (locations.handoff_root.as_posix(), locations.review_root.as_posix())
        self._paths: list[str] | None = None

    def _scan(self) -> list[str]:
        if self._paths is None:
            found: set[str] = set()
            for root in self.roots:
                for directory, names, files in os.walk(self.project / root):
                    relative = Path(directory).relative_to(self.project).as_posix()
                    names[:] = [
                        name for name in names
                        if is_task_record_path(f"{relative}/{name}/x", self.excluded)
                    ]
                    found.update(
                        f"{relative}/{name}" for name in files
                        if name.endswith(".md") and not os.path.islink(os.path.join(directory, name))
                    )
            self._paths = sorted(found)
        return self._paths

    def find(self, task_id: str) -> tuple[Path | None, str | None]:
        """Return the record path, or the per-task problem that prevents one."""
        matches = record_matches(task_id, self._scan(), self.excluded)
        if not matches:
            return None, "task record not found"
        if len(matches) > 1:
            return None, "ambiguous task record: " + ", ".join(matches)
        path = (self.project / matches[0]).resolve()
        if not path.is_relative_to(self.project) or not path.is_file():
            return None, f"task record is unavailable within the project: {matches[0]}"
        return path, None

    def find_on_ref(self, ref: str, task_id: str) -> str | None:
        """Apply the same rules to a task branch tree; None unless exactly one match."""
        listing = _git_optional(self.project, "ls-tree", "-r", "--name-only", ref, "--", *self.roots)
        matches = record_matches(task_id, (listing or "").splitlines(), self.excluded)
        return matches[0] if len(matches) == 1 else None


def _task_path(project: Path, queue: Path, row: QueueRow,
               resolver: RecordResolver) -> tuple[Path | None, str | None]:
    """Resolve a task record: the queue link when present, else a search of the task roots."""
    if not has_link(row.link):
        return resolver.find(row.task_id)
    target = link_target(queue.relative_to(project).as_posix(), row.link)
    if target is None:
        raise ConsoleError(f"Task {row.task_id} has no unambiguous file link")
    path = (project / target).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise ConsoleError(f"Task {row.task_id} file is unavailable within the project: {path}")
    return path, None


def _section(text: str, *names: str) -> tuple[str, ...]:
    """Return the first named level-two section, tolerating decorative emoji."""
    inside = False
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            heading = re.sub(r"^[^\w]+", "", line[3:]).strip().casefold()
            inside = heading in {name.casefold() for name in names}
        elif inside and line.strip():
            lines.append(line.strip())
    return tuple(lines)


def _git_result(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ("git", "-C", str(project), *args),
            capture_output=True, text=True, check=False, timeout=5,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ConsoleError(f"Git {' '.join(args)} failed: {error}") from error


def _git(project: Path, *args: str) -> str:
    result = _git_result(project, *args)
    if result.returncode:
        raise ConsoleError(f"Git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _git_optional(project: Path, *args: str) -> str | None:
    """Return Git output, or None when the object or ref does not exist."""
    result = _git_result(project, *args)
    return None if result.returncode else result.stdout


def _primary_checkout(project: Path) -> tuple[Path | None, str | None]:
    """Resolve Git's first registered worktree, which is the primary checkout."""
    result = _git_result(project, "worktree", "list", "--porcelain")
    if result.returncode:
        return None, "Cannot resolve the primary checkout"
    primary = next((line.removeprefix("worktree ") for line in result.stdout.splitlines()
                    if line.startswith("worktree ")), None)
    directory = Path(primary).resolve() if primary else None
    if directory is None or not directory.is_dir():
        return None, "Primary checkout is unavailable"
    return directory, None


def _worktrees(project: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    path = ""
    for line in _git(project, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line[9:]
        elif line.startswith("branch refs/heads/") and path:
            records[line.removeprefix("branch refs/heads/")] = path
    return records


def _committed_update(project: Path, relative: str, ref: str = "HEAD") -> int | None:
    """Return the last committed change to a task record, when Git knows it."""
    try:
        value = _git(project, "log", "-1", "--format=%ct", ref, "--", relative).strip()
        return int(value) if value else None
    except (ConsoleError, ValueError):
        return None


def _select_profile(project: Path) -> Profile:
    try:
        mode = detect_mode(project)
    except MeridianError as error:
        raise ConsoleError(str(error).partition("; pass --mode")[0]) from error
    return PROFILES[mode]


def _relative(project: Path, path: Path) -> str:
    try:
        return path.relative_to(project).as_posix()
    except ValueError as error:
        raise ConsoleError(f"Task record is outside the project: {path}") from error


class IdentityCache:
    """Resolve each task identity once per console process.

    Entries are valid only for the bytes of the identity declaration they were
    resolved under; any change to that file discards them. Failures are never
    cached, so a corrected project recovers on the next refresh.
    """

    def __init__(self) -> None:
        self._declaration: bytes | None = None
        self._loaded = False
        self._items: dict[str, ResolvedTaskIdentity] = {}

    def resolve(self, project: Path, task_id: str) -> ResolvedTaskIdentity:
        try:
            declaration = (project / TASK_IDENTITY_PATH).read_bytes()
        except OSError:
            declaration = None
        if not self._loaded or declaration != self._declaration:
            self._items.clear()
            self._declaration, self._loaded = declaration, True
        identity = self._items.get(task_id)
        if identity is None:
            identity = self._items[task_id] = resolve_task_identity(project, task_id, "existing")
        return identity


def _branch_facts(project: Path, profile: Profile, task_id: str, queue: str,
                  worktrees: dict[str, str], identities: IdentityCache | None = None,
                  resolver: RecordResolver | None = None, main_record: str | None = None
                  ) -> tuple[BranchFacts | None, str | None, str | None, str | None]:
    """Read one task branch without touching its worktree.

    Returns the branch facts, the branch task record text and path, and the
    registered worktree path (known even when the branch ref is unreadable).
    """
    try:
        identity = (identities or IdentityCache()).resolve(project, task_id)
    except MeridianError as error:
        raise ConsoleError(f"Cannot resolve task identity for {task_id}: {error}") from error
    branch = identity.branch_name
    worktree = worktrees.get(branch)
    if _git_optional(project, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}") is None:
        return None, None, None, worktree
    ref = f"refs/heads/{branch}"

    def show(relative: str) -> str | None:
        return _git_optional(project, "show", f"{ref}:{relative}")

    queue_text = show(queue)
    row = next((item for item in parse_queue(queue_text, f"{branch}:{queue}", profile)
                if item.task_id == task_id), None) if queue_text is not None else None
    if row is None:
        record_path = None
    elif has_link(row.link):
        record_path = link_target(queue, row.link)
    else:
        record_path = main_record
    record = show(record_path) if record_path else None
    if record is None and resolver and row and not has_link(row.link):
        # The branch moved the record: resolve it in the branch tree by the same rules.
        record_path = resolver.find_on_ref(ref, task_id)
        record = show(record_path) if record_path else None
    review = (show(_relative(project, identity.review_path))
              if profile.name == "governed-sdd" else None)
    base = "refs/heads/main" if _git_optional(
        project, "rev-parse", "--verify", "--quiet", "refs/heads/main") is not None else "HEAD"
    ahead = (_git_optional(project, "rev-list", "--count", f"{base}..{ref}") or "0").strip() != "0"
    dirty = bool(worktree and (_git_optional(worktree, "status", "--porcelain") or "").strip())
    working_row = None
    if dirty and worktree:
        try:
            working_text = _read_text(Path(worktree) / queue)
            working_row = next(
                (item for item in parse_queue(working_text, f"{worktree}:{queue}", profile)
                 if item.task_id == task_id),
                None,
            )
        except ConsoleError:
            # An unreadable or invalid uncommitted queue cannot supersede the
            # committed branch state.
            pass
    facts = BranchFacts(
        branch=branch, row=row, record=record_status(record),
        handoff=handoff_status(show(_relative(project, identity.handoff_path))),
        review_verdict=latest_review_verdict(review), ahead=ahead,
        worktree=worktree, dirty=dirty, working_row=working_row,
    )
    return facts, record, record_path, worktree


def load_snapshot(project: Path, identities: IdentityCache | None = None) -> Snapshot:
    project = project.expanduser().resolve()
    profile = _select_profile(project)
    try:
        locations = resolve_project_locations(project)
    except Exception as error:
        raise ConsoleError(f"Cannot resolve canonical queue: {error}") from error
    queue = project / locations.queue
    archive = queue.with_name("QUEUE_ARCHIVE.md")
    active_rows = parse_queue(_read_text(queue), str(queue), profile)
    archived_rows = parse_queue(_read_text(archive), str(archive), profile) if archive.is_file() else []
    by_id: dict[str, str] = {}
    for row in (*active_rows, *archived_rows):
        if row.task_id in by_id:
            raise ConsoleError(f"Duplicate task ID across queues: {row.task_id}")
        by_id[row.task_id] = row.status
    status_lines = _git(project, "status", "--porcelain=v1", "--branch").splitlines()
    if not status_lines:
        raise ConsoleError("Git status returned no branch line")
    branch_line = status_lines[0].removeprefix("## ")
    branch = branch_line.split("...", 1)[0].split(" [", 1)[0]
    worktrees = _worktrees(project)
    queue_relative = _relative(project, queue)
    resolver = RecordResolver(project, locations)
    tasks: list[Task] = []
    for row in active_rows:
        if profile.phases[row.status] == "done":
            continue
        dependencies = tuple(
            item.strip().strip("`") for item in row.dependencies.split(",")
            if item.strip() not in ("", "—", "-")
        )
        if any(not ID_PATTERN.fullmatch(item) for item in dependencies):
            raise ConsoleError(f"Task {row.task_id} has an invalid dependency")
        path, main_problem = _task_path(project, queue, row, resolver)
        primary_text = _read_text(path) if path else None
        if main_problem:
            # Task identity needs exactly one record, so a task without one has no branch state.
            facts, branch_text, branch_path, worktree = None, None, None, None
        else:
            facts, branch_text, branch_path, worktree = _branch_facts(
                project, profile, row.task_id, queue_relative, worktrees, identities, resolver,
                _relative(project, path) if path and not has_link(row.link) else None)
        effective = effective_state(profile, row, record_status(primary_text), facts)
        from_branch = facts is not None and branch_text is not None and effective.source != "main"
        task_text = branch_text if from_branch else primary_text
        problem = None if task_text is not None else (main_problem or "task record not found")
        # Dependencies are satisfied by integrated state only: a task accepted on its
        # branch does not unblock dependents until it reaches the primary queue.
        missing = [item for item in dependencies if item not in by_id]
        waiting = [item for item in dependencies
                   if item in by_id and by_id[item] not in profile.satisfying]
        if effective.mismatch:
            readiness = "MISMATCH"
        elif problem:
            readiness = "UNKNOWN: " + problem.split(":", 1)[0]
        elif missing:
            readiness = "UNKNOWN: missing " + ", ".join(missing)
        elif waiting:
            readiness = "BLOCKED: " + ", ".join(waiting)
        else:
            readiness = {
                "todo": "READY", "in_progress": "IN PROGRESS",
                "ready_for_review": "READY FOR REVIEW", "done": "DONE ON BRANCH",
            }[effective.lifecycle]
        updated_path = branch_path if from_branch else (_relative(project, path) if path else None)
        updated_ref = ("refs/heads/" + facts.branch) if from_branch else "HEAD"
        title = row.title or heading_title(task_text or "") or row.task_id
        tasks.append(Task(
            task_id=row.task_id, title=title, status=effective.status,
            phase=row.section, dependencies=dependencies, path=path,
            objective=_section(task_text or "", "Objective", "Goal"),
            criteria=_section(task_text or "", "Acceptance Criteria"),
            worktree=worktree, readiness=readiness,
            updated_at=_committed_update(project, updated_path, updated_ref) if updated_path else None,
            lifecycle=effective.lifecycle, source=effective.source,
            mismatch=effective.mismatch, changes_requested=effective.changes_requested,
            active_writer=effective.active_writer,
            registered_worktree=bool(
                facts and facts.worktree and not facts.dirty and facts.row
                and facts.row.status == row.status
            ),
            record_problem=problem, review=row.review,
            workflow=profile.name,
            dependency_states=tuple(
                (item, {
                    "done": "Done", "in_progress": "Working",
                    "ready_for_review": "Review", "todo": "Open",
                }[profile.phases[by_id[item]]])
                for item in dependencies if item in by_id
            ),
        ))
    return Snapshot(
        project=project, queue=queue, branch=branch_line,
        git_summary="clean" if len(status_lines) == 1 else f"{len(status_lines) - 1} changed paths",
        git_changes=len(status_lines) - 1, tasks=tuple(tasks),
        done_count=sum(profile.phases[status] == "done" for status in by_id.values()),
    )


class ConsoleState:
    """Snapshot, staleness and refresh state shown by the console.

    `refresh` loads synchronously. `start_refresh` loads on one background
    thread and hands the result over through `apply_pending`, so the display
    only ever changes on the caller's thread and never shows a mixed state.
    """

    def __init__(self, project: Path):
        self.project = project
        self.snapshot: Snapshot | None = None
        self.last_success: datetime | None = None
        self.error: str | None = None
        self.identities = IdentityCache()
        self._lock = threading.Lock()
        self._worker: threading.Thread | None = None
        self._pending: tuple[Snapshot | None, str | None] | None = None

    def _load(self) -> tuple[Snapshot | None, str | None]:
        try:
            return load_snapshot(self.project, self.identities), None
        except ConsoleError as error:
            return None, str(error)

    def _apply(self, candidate: Snapshot | None, error: str | None) -> None:
        if candidate is None:
            self.error = error
            return
        self.snapshot = candidate
        self.last_success = datetime.now().astimezone()
        self.error = None

    def refresh(self) -> None:
        self._apply(*self._load())

    @property
    def refreshing(self) -> bool:
        with self._lock:
            return self._worker is not None

    def start_refresh(self) -> bool:
        """Start a background refresh unless one is already running."""
        with self._lock:
            if self._worker is not None:
                return False
            self._worker = threading.Thread(target=self._run, daemon=True)
            worker = self._worker
        worker.start()
        return True

    def _run(self) -> None:
        try:
            result = self._load()
        except Exception as error:  # a worker must never die silently
            result = (None, f"Refresh failed: {error}")
        with self._lock:
            self._pending = result
            self._worker = None

    def apply_pending(self) -> None:
        with self._lock:
            pending, self._pending = self._pending, None
        if pending is not None:
            self._apply(*pending)


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
        if task.source != "main":
            lines.append(f"  State from: {task.source}")
        if task.mismatch:
            lines.append(f"  Mismatch: {task.mismatch}")
        if task.markers:
            lines.append(f"  Markers: {', '.join(task.markers)}")
        if task.record_problem:
            lines.append(f"  Record: {task.record_problem}")
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


FILTERS = ("Ready", "Working", "Blocked", "Unknown", "Review", "Mismatch")


def _state_label(task: Task) -> tuple[str, str]:
    if task.readiness == "MISMATCH":
        return "Mismatch", "blocked"
    if task.lifecycle in ("ready_for_review", "done") and not task.readiness.startswith(
            ("BLOCKED", "UNKNOWN")):
        return "Review", "ready"
    if task.readiness == "READY":
        return "Ready", "ready"
    if task.readiness == "IN PROGRESS":
        return "Working", "working"
    if task.readiness.startswith("BLOCKED"):
        return "Blocked", "blocked"
    return "Unknown", "unknown"


def _filter_counts(snapshot: Snapshot | None) -> dict[str, int]:
    counts = {name: 0 for name in FILTERS}
    for task in snapshot.tasks if snapshot else ():
        counts[_state_label(task)[0]] += 1
    return counts


def _cycle_filter(snapshot: Snapshot | None, current: str, direction: int) -> str:
    filters = ("All", *FILTERS)
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
    add(f"Task {task.task_id}", "muted")
    add(f"○ {label}", color)
    if task.source != "main":
        add(f"State from {task.source}", "muted")
    if task.mismatch:
        add(f"Mismatch: {task.mismatch}", "blocked")
    for marker in task.markers:
        add(f"● {marker.capitalize()}", "working")
    if task.record_problem:
        add(task.record_problem[:1].upper() + task.record_problem[1:], "blocked")
    add("")
    add("Dependencies", "muted")
    states = dict(task.dependency_states)
    for dependency in task.dependencies:
        add(f"{dependency} — {states.get(dependency, 'state unavailable')}")
    if not task.dependencies:
        add("none")
    if not compact:
        add("")
    add("Objective", "muted")
    for value in task.objective or ("Unavailable", "Searched headings: Objective, Goal"):
        add(value)
    if not compact:
        add("")
    if task.criteria:
        add("Acceptance criteria", "muted")
        for value in task.criteria:
            add(value)
        if not compact:
            add("")
    add("─" * min(20, width), "line")
    if not compact:
        add("")
    add("Next directive", "muted")
    command = task.launch_command
    add(f"{command}  [copy]  [l launch]" if command else task.next_action, "action")
    return lines


def _visible_tasks(snapshot: Snapshot | None, status_filter: str, search: str) -> list[Task]:
    tasks = snapshot.tasks if snapshot else ()
    return [
        task for task in tasks
        if (status_filter == "All" or _state_label(task)[0] == status_filter)
        and search.casefold() in (
            f"{task.task_id} {task.title} "
            + " ".join(_group_label(heading) for heading in task.phase)
        ).casefold()
    ]


def _group_label(heading: str) -> str:
    """Remove a queue descriptor while retaining the heading's identity."""
    return re.sub(r"\s+Queue(?=\s*(?:[—–:]|$))", "", heading, flags=re.IGNORECASE)


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
             "Blocked": "blocked", "Unknown": "unknown", "Review": "ready",
             "Mismatch": "blocked"}[name]
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


LIST_ID_X = 3
LIST_STATUS_WIDTH = 11
LIST_AGE_WIDTH = 9
LIST_MIN_TITLE_WIDTH = 8


@dataclass(frozen=True)
class ListLayout:
    id_x: int
    id_width: int
    title_x: int
    title_width: int
    status_x: int
    age_x: int


def _list_layout(all_tasks: tuple[Task, ...] | list[Task], left_width: int) -> ListLayout:
    """Column positions for the task list.

    The ID width follows the longest ID of the full open task set, so filtering
    or searching never moves a column. It is capped at a third of the pane and
    never squeezes the title below its minimum width.
    """
    status_x = left_width - LIST_STATUS_WIDTH - LIST_AGE_WIDTH - 2
    longest = max((len(task.task_id) for task in all_tasks), default=0)
    room = status_x - 2 - LIST_MIN_TITLE_WIDTH - LIST_ID_X - 1
    id_width = max(1, min(longest, left_width // 3, room))
    title_x = LIST_ID_X + id_width + 1
    return ListLayout(
        LIST_ID_X, id_width, title_x,
        max(LIST_MIN_TITLE_WIDTH, status_x - 2 - title_x),
        status_x, left_width - LIST_AGE_WIDTH - 1,
    )


def _draw_list(screen, tasks: list[Task], selected_id: str | None,
               offset: int, left_width: int, height: int,
               palette: dict[str, int],
               all_tasks: tuple[Task, ...] | list[Task] | None = None) -> int:
    layout = _list_layout(tasks if all_tasks is None else all_tasks, left_width)
    title_width = layout.title_width
    _put(screen, 3, 2, "Tasks", layout.title_x + title_width - 2, palette["muted"])
    _put(screen, 3, layout.status_x, "Status", LIST_STATUS_WIDTH, palette["muted"])
    _put(screen, 3, layout.age_x, "Updated", LIST_AGE_WIDTH, palette["muted"])
    entries: list[tuple[str, Task | None]] = []
    previous: tuple[str, ...] = ()
    for task in tasks:
        shared = 0
        for old, new in zip(previous, task.phase):
            if old != new:
                break
            shared += 1
        for depth, heading in enumerate(task.phase[shared:], shared):
            entries.append(("  " * depth + _group_label(heading), None))
        entries.append(("", task))
        previous = task.phase
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
        _put(screen, line_number, layout.id_x, _clip(task.task_id, layout.id_width),
             layout.id_width, row_attr if selected else palette["muted"])
        _put(screen, line_number, layout.title_x, _clip(f"○ {task.title}", title_width),
             title_width, row_attr)
        label, color = _state_label(task)
        flags = ("↺" if task.changes_requested else "") + ("●" if task.active_writer else "")
        _put(screen, line_number, layout.status_x,
             f"{label} {flags}" if flags else label, LIST_STATUS_WIDTH,
             row_attr if selected else palette[color])
        _put(screen, line_number, layout.age_x,
             _age(task.updated_at), LIST_AGE_WIDTH, row_attr if selected else palette["muted"])
    if not tasks:
        _put(screen, body_top + 1, 2, "No matching open tasks", left_width - 4, palette["muted"])
    return offset


def _detail_view(task: Task | None, width: int, height: int, top: int,
                 offset: int, palette: dict[str, int]) -> tuple[list[tuple[str, int]], int, int]:
    """Build a detail viewport and clamp its offset for this exact terminal size."""
    if task is None:
        return [], 0, 1
    lines = _detail_lines(task, width - 2, palette, compact=height < 30)
    body_lines = max(1, height - top - 2)
    return lines, min(max(0, offset), max(0, len(lines) - body_lines)), body_lines


def _scroll_detail(task: Task | None, width: int, height: int, top: int,
                   offset: int, delta: int, palette: dict[str, int]) -> int:
    lines, offset, body_lines = _detail_view(task, width, height, top, offset, palette)
    return min(max(0, offset + delta), max(0, len(lines) - body_lines))


def _draw_detail(screen, task: Task | None, x: int, top: int, width: int,
                 height: int, offset: int, palette: dict[str, int]) -> set[int]:
    if task is None:
        _put(screen, top, x, "No task selected", width, palette["muted"])
        return set()
    lines, offset, body_lines = _detail_view(task, width, height, top, offset, palette)
    for y, (value, attr) in enumerate(lines[offset:offset + body_lines], top):
        _put(screen, y, x, value, width - 1, attr)
    if offset:
        _put(screen, top, x + max(0, width - 13), "↑ more above", 12, palette["muted"])
    if offset + body_lines < len(lines):
        _put(screen, top + body_lines - 1, x + max(0, width - 13), "↓ more below", 12,
             palette["muted"])
    if not task.launch_command:
        return set()
    action_start = next(i for i, (value, _) in enumerate(lines)
                        if value == "Next directive") + 1
    return {
        top + i - offset for i in range(action_start, len(lines))
        if offset <= i < offset + body_lines
    }


def _draw_launch_prompt(screen, width: int, height: int, agent: str | None,
                        request: LaunchRequest | None, palette: dict[str, int]) -> None:
    """Draw the two explicit steps required before starting a mutable agent."""
    if agent is None and request is None:
        return
    lines = (
        ("Launch agent", "title"),
        ("This starts an agent that may modify the project.", "blocked"),
    )
    if agent is not None:
        lines += (
            ("Choose an agent: 1 Claude Code   2 Codex", "text"),
            ("Esc cancels. Nothing has started.", "muted"),
        )
    else:
        assert request is not None
        lines += (
            (f"Agent: {request.agent}", "text"),
            (f"Directive: {request.directive}", "text"),
            (f"Directory: {request.directory}", "text"),
            ("Enter launches and assigns this task; Esc cancels.", "action"),
        )
    panel_width = min(width - 8, max(len(value) for value, _ in lines) + 4)
    top = max(4, (height - len(lines) - 2) // 2)
    left = max(2, (width - panel_width) // 2)
    for index, (value, style) in enumerate(lines):
        _put(screen, top + index, left, value, panel_width, palette[style])


def run_terminal(screen, state: ConsoleState, interval: float) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    palette = _palette(screen)
    try:
        curses.mousemask(curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED
                         | getattr(curses, "BUTTON4_PRESSED", 0)
                         | getattr(curses, "BUTTON5_PRESSED", 0))
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
    detail_focused = False
    status_filter = "All"
    last_poll = 0.0
    notice = ""
    notice_until = 0.0
    launch_agent: str | None = None
    launch_request: LaunchRequest | None = None
    while True:
        now = time.monotonic()
        state.apply_pending()
        if now - last_poll >= interval and state.start_refresh():
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
        detail_bounds: tuple[int, int] | None = None
        detail_width = 0
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
                    "c or click [copy]  Copy a permitted task directive",
                    "l  Choose Claude Code or Codex, then confirm an iTerm2 launch",
                    "Tab  Cycle All and nonempty states; click any tab",
                    "r  Refresh now", "q  Quit", "",
                    "Project state is read-only; copy writes to the clipboard.",
                    "Updated is the last committed change to the task file.",
                    "Agent activity is unavailable without a verified source.",
                    "Launching uses macOS iTerm2 only after explicit confirmation.",
                )
                for y, line in enumerate(help_lines, 4):
                    _put(screen, y, 2, line, width - 4, palette["text"] if y == 4 else palette["base"])
            elif detail_open:
                detail_width = width - 4
                detail_bounds = (2, width - 3)
                _, detail_offset, _ = _detail_view(selected_task, detail_width, height, 4,
                                                   detail_offset, palette)
                action_rows = _draw_detail(screen, selected_task, 2, 4, width - 4,
                                           height, detail_offset, palette)
                action_bounds = (2, width - 4, action_rows)
            else:
                left_width = int(width * .68) if wide else width
                offset = _draw_list(screen, visible, selected_id, offset, left_width,
                                    height, palette,
                                    snapshot.tasks if snapshot else ())
                if wide:
                    divider = left_width - 1
                    for y in range(3, height - 2):
                        _put(screen, y, divider, "│", 1, palette["line"])
                    detail_x = left_width + 1
                    detail_width = width - left_width - 2
                    detail_bounds = (detail_x, width - 3)
                    _, detail_offset, _ = _detail_view(selected_task, detail_width, height, 4,
                                                       detail_offset, palette)
                    action_rows = _draw_detail(screen, selected_task, detail_x, 4,
                                               width - left_width - 2, height,
                                               detail_offset, palette)
                    action_bounds = (detail_x, width - 3, action_rows)
            _draw_launch_prompt(screen, width, height, launch_agent, launch_request, palette)
            if notice and time.monotonic() < notice_until:
                footer = notice
            elif state.error:
                footer = f"STALE: {state.error}"
            elif searching:
                footer = f"Search: {search}"
            elif detail_open or help_visible:
                footer = "Esc back   [/] scroll   r refresh   q quit"
            else:
                footer = ("? help   ↑/↓ move   [/] scroll detail   tab filter   enter details   "
                          "c copy   l launch   / search   r refresh   q quit")
            _put(screen, height - 2, 0, "─" * max(0, width - 1),
                 width - 1, palette["line"])
            _put(screen, height - 1, 1, footer, width - 2,
                 palette["stale"] if state.error else palette["muted"])
        screen.refresh()
        key = screen.getch()
        if key == -1:
            continue
        if launch_agent is not None:
            if key == 27:
                launch_agent = None
                notice, notice_until = "Launch cancelled", time.monotonic() + 2
            elif key in (ord("1"), ord("2")):
                selected = "claude" if key == ord("1") else "codex"
                launch_request, error = _launch_request(selected_task, state.project, selected) if selected_task else (
                    None, "No task selected")
                launch_agent = None
                if error:
                    notice, notice_until = error, time.monotonic() + 3
            continue
        if launch_request is not None:
            if key == 27:
                launch_request = None
                notice, notice_until = "Launch cancelled", time.monotonic() + 2
            elif key in (10, 13):
                success, message = _start_launch(launch_request)
                launch_request = None
                notice, notice_until = message, time.monotonic() + (3 if success else 5)
            continue
        if key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, button_state = curses.getmouse()
            except curses.error:
                continue
            wheel_up = getattr(curses, "BUTTON4_PRESSED", 0)
            wheel_down = getattr(curses, "BUTTON5_PRESSED", 0)
            in_detail = bool(detail_bounds and detail_bounds[0] <= mouse_x <= detail_bounds[1])
            if button_state & (wheel_up | wheel_down):
                if selected_task and (detail_open or in_detail) and detail_width:
                    detail_offset = _scroll_detail(
                        selected_task, detail_width, height, 4, detail_offset,
                        -3 if button_state & wheel_up else 3, palette)
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
            elif in_detail:
                detail_focused = True
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
            detail_open = detail_focused = help_visible = False
            continue
        if key in (ord("q"), ord("Q")):
            return
        scroll_focus = detail_open or detail_focused
        page = max(1, height - 4 - 2)
        if (key in (ord("j"), curses.KEY_DOWN) and scroll_focus and not help_visible
                and selected_task and detail_width):
            detail_offset = _scroll_detail(selected_task, detail_width, height, 4,
                                           detail_offset, 1, palette)
        elif (key in (ord("k"), curses.KEY_UP) and scroll_focus and not help_visible
              and selected_task and detail_width):
            detail_offset = _scroll_detail(selected_task, detail_width, height, 4,
                                           detail_offset, -1, palette)
        elif key == curses.KEY_NPAGE and selected_task and detail_width:
            detail_offset = _scroll_detail(selected_task, detail_width, height, 4,
                                           detail_offset, page, palette)
        elif key == curses.KEY_PPAGE and selected_task and detail_width:
            detail_offset = _scroll_detail(selected_task, detail_width, height, 4,
                                           detail_offset, -page, palette)
        elif key in (ord("j"), curses.KEY_DOWN) and not detail_open and not help_visible:
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
        elif key == ord("]") and selected_task and detail_width:
            detail_offset = _scroll_detail(selected_task, detail_width, height, 4,
                                           detail_offset, 1, palette)
        elif key in (9, curses.KEY_BTAB) and not detail_open and not help_visible:
            direction = -1 if key == curses.KEY_BTAB else 1
            status_filter = _cycle_filter(snapshot, status_filter, direction)
            offset = detail_offset = 0
        elif key in (10, 13) and selected_task and not help_visible:
            detail_open = True
            detail_focused = True
            detail_offset = 0
        elif key == ord("/"):
            searching = True
            search = ""
        elif key == ord("r"):
            if state.start_refresh():
                last_poll = time.monotonic()
        elif key == ord("c") and selected_task and not help_visible:
            command = selected_task.launch_command
            notice = (f"Copied: {command}" if command and _copy_to_clipboard(command)
                      else "Clipboard unavailable" if command
                      else "No launch command for this task")
            notice_until = time.monotonic() + 2
        elif key in (ord("l"), ord("L")) and selected_task and not help_visible:
            if selected_task.launch_command:
                launch_agent = "choose"
            else:
                notice, notice_until = "No eligible directive for this task", time.monotonic() + 2
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
    if args.once:
        state.refresh()
        print(one_shot(state))
        return 1 if state.error else 0
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("interactive mode requires a terminal; use --once")
    curses.wrapper(run_terminal, state, args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
