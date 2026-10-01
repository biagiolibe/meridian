"""Workflow profiles and effective task state for the read-only project console."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass


PHASES = ("todo", "in_progress", "ready_for_review", "done")
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)")
HANDOFF_STATUS = re.compile(r"^[-*\s]*Status:\s*`?([A-Z_]+)`?\s*$", re.MULTILINE)
RECORD_STATUS = re.compile(r"^Status:\s*`?([A-Z_]+)`?\s*$", re.MULTILINE)
REVIEW_ATTEMPT = re.compile(
    r"^## Attempt (\d+) — (CHANGES_REQUESTED|APPROVE|BLOCKED)\s*$", re.MULTILINE
)
TASK_HEADING = re.compile(r"^#\s+(?:Task\s+)?\S+\s+[—-]\s+(.+?)\s*$")


class ConsoleError(Exception):
    """Project state could not be read without ambiguity."""


@dataclass(frozen=True)
class Profile:
    """Queue vocabulary of one workflow mode, normalized to console phases."""

    name: str
    tokens: dict[str, str]
    phases: dict[str, str]
    satisfying: frozenset[str]


PROFILES = {
    "lean-delivery": Profile(
        name="lean-delivery",
        tokens={"[ ]": "TODO", "[/]": "IN_PROGRESS", "[x]": "DONE"},
        phases={"TODO": "todo", "IN_PROGRESS": "in_progress", "DONE": "done"},
        satisfying=frozenset({"DONE"}),
    ),
    "governed-sdd": Profile(
        name="governed-sdd",
        tokens={name: name for name in (
            "QUEUED", "IN_PROGRESS", "READY_FOR_REVIEW", "ACCEPTED",
            "ANSWERED", "INCONCLUSIVE",
        )},
        phases={
            "QUEUED": "todo", "IN_PROGRESS": "in_progress",
            "READY_FOR_REVIEW": "ready_for_review", "ACCEPTED": "done",
            "ANSWERED": "done", "INCONCLUSIVE": "done",
        },
        satisfying=frozenset({"ACCEPTED", "ANSWERED"}),
    ),
}


@dataclass(frozen=True)
class QueueRow:
    task_id: str
    status: str
    title: str
    section: str
    dependencies: str
    link: str
    review: str


def _cell(row: dict[str, str], *names: str) -> str:
    folded = {key.casefold(): value for key, value in row.items()}
    for name in names:
        if name.casefold() in folded:
            return folded[name.casefold()]
    return ""


def parse_queue(text: str, label: str, profile: Profile) -> list[QueueRow]:
    rows: list[QueueRow] = []
    headers: list[str] = []
    section = ""
    for line_number, line in enumerate(text.splitlines(), 1):
        if line.startswith("### "):
            section = line[4:].strip()
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
        token = row.get("Status", "").strip("`")
        if token not in profile.tokens:
            raise ConsoleError(f"Unknown task status in {label}:{line_number}: {row.get('Status')}")
        task_id = row["ID"].strip("`")
        if not ID_PATTERN.fullmatch(task_id):
            raise ConsoleError(f"Invalid task ID in {label}:{line_number}")
        rows.append(QueueRow(
            task_id=task_id, status=profile.tokens[token], title=_cell(row, "Title"),
            section=section, dependencies=_cell(row, "Depends on", "Dependencies"),
            link=_cell(row, "File", "Task file"), review=_cell(row, "Review").strip("`"),
        ))
    return rows


def link_target(queue_relative: str, cell: str) -> str | None:
    """Resolve a queue link to a project-relative POSIX path, or None if it escapes."""
    match = LINK_PATTERN.fullmatch(cell)
    if not match:
        return None
    target = posixpath.normpath(posixpath.join(posixpath.dirname(queue_relative), match.group(1)))
    return None if target.startswith("..") or posixpath.isabs(target) else target


def heading_title(text: str) -> str:
    lines = text.splitlines()
    match = TASK_HEADING.match(lines[0]) if lines else None
    return match.group(1) if match else ""


def record_status(text: str | None) -> str | None:
    match = RECORD_STATUS.search(text or "")
    return match.group(1) if match else None


def handoff_status(text: str | None) -> str | None:
    match = HANDOFF_STATUS.search(text or "")
    return match.group(1) if match else None


def latest_review_verdict(text: str | None) -> str | None:
    attempts = [(int(number), verdict) for number, verdict in REVIEW_ATTEMPT.findall(text or "")]
    return max(attempts)[1] if attempts else None


@dataclass(frozen=True)
class BranchFacts:
    """Read-only observations of one task branch and its worktree."""

    branch: str
    row: QueueRow | None
    record: str | None
    handoff: str | None
    review_verdict: str | None
    ahead: bool
    worktree: str | None
    dirty: bool


@dataclass(frozen=True)
class Effective:
    lifecycle: str
    status: str
    source: str
    mismatch: str | None = None
    changes_requested: bool = False
    active_writer: bool = False


def effective_state(profile: Profile, primary: QueueRow, primary_record: str | None,
                    facts: BranchFacts | None) -> Effective:
    """Combine the primary queue row with the task branch state, never writing either."""
    if facts is None:
        row, record, source, writer = primary, primary_record, "main", False
    else:
        source = f"branch {facts.branch}"
        writer = facts.dirty
        if facts.row is None:
            return Effective(
                "in_progress", "MISMATCH", source, active_writer=writer,
                mismatch=f"main {primary.status}, {facts.branch} has no queue row",
            )
        row, record = facts.row, facts.record
        if PHASES.index(profile.phases[row.status]) < PHASES.index(profile.phases[primary.status]):
            return Effective(
                "in_progress", "MISMATCH", source, active_writer=writer,
                mismatch=f"main {primary.status}, {facts.branch} {row.status}",
            )
        if row.status == primary.status:
            source = "main"

    def mismatch(reason: str) -> Effective:
        return Effective("in_progress", "MISMATCH", source, active_writer=writer, mismatch=reason)

    phase = profile.phases[row.status]
    if profile.name == "governed-sdd":
        if row.status == "READY_FOR_REVIEW" or record == "READY_FOR_REVIEW":
            if record != row.status:
                return mismatch(f"queue {row.status}, task record {record or 'no status'}")
            if row.review != "REQUIRED":
                return mismatch(f"queue READY_FOR_REVIEW, Review {row.review or 'unset'}")
        return Effective(
            phase, row.status, source, active_writer=writer,
            changes_requested=bool(
                facts and row.status == "IN_PROGRESS"
                and facts.review_verdict == "CHANGES_REQUESTED"
            ),
        )
    if row.status == "DONE" and facts is not None:
        if facts.handoff != "DONE":
            return mismatch(f"{facts.branch} queue [x], handoff {facts.handoff or 'missing'}")
        if not facts.ahead:
            return mismatch(f"{facts.branch} queue [x], branch is not ahead of main")
        if facts.worktree and not facts.dirty:
            return Effective("ready_for_review", "READY_FOR_REVIEW", source)
        return Effective("in_progress", "IN_PROGRESS", source, active_writer=writer)
    return Effective(phase, row.status, source, active_writer=writer)
