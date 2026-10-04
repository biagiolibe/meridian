# Task Execution Queue

Only `ACCEPTED` tasks satisfy dependencies. Choose the highest-priority queued task whose dependencies are all accepted.

New or materially revised tasks must follow `tasks/TASK_BLUEPRINT.md`. A task is startable without repository-wide exploration only when it names its authority, declared dependencies, expected code surface, acceptance criteria, validation, and out-of-scope boundary; dependencies must be `ACCEPTED` before implementation. Record completion evidence with `docs/COMPLETION_REPORT_TEMPLATE.md`, not in the queue row.

| Order | ID | Priority | Status | Review | Dependencies | Task file |
|---:|---|---|---|---|---|---|
| 1 | TASK-001 | P0 | QUEUED | REQUIRED | — | [TASK-001](TASK-001.md) |

A task branch never edits this file. `IN_PROGRESS`, `READY_FOR_REVIEW`, and
`CHANGES_REQUESTED` are recorded in the task record, and `meridian worktree
integrate stage` applies the status here once, on the merged candidate tree. For
`CHANGES_REQUESTED`, the reviewer records `IN_PROGRESS` in the task record
alongside the durable review record; that record, rather than chat output, is
the implementer's source of requested changes.

**Archiving.** Once this table grows large enough that opening it costs more
than the queue-briefing summary can save, move its `ACCEPTED` rows to
`tasks/QUEUE_ARCHIVE.md` (create it, mirroring this file's own column
structure, if it doesn't exist yet), keeping this table to active and queued
work only — the same archiving convention Lean Delivery projects already
follow for closed phases. `ACCEPTED` rows still satisfy dependencies from
their archived location; nothing about moving a row changes what it
satisfies, only where it is read from.
