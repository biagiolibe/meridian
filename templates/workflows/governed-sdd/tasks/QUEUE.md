# Task Execution Queue

Only `ACCEPTED` tasks satisfy dependencies. Choose the highest-priority queued task whose dependencies are all accepted.

New or materially revised tasks must follow `tasks/TASK_BLUEPRINT.md`. A task is startable without repository-wide exploration only when it names its authority, declared dependencies, expected code surface, acceptance criteria, validation, and out-of-scope boundary; dependencies must be `ACCEPTED` before implementation. Record completion evidence with `docs/COMPLETION_REPORT_TEMPLATE.md`, not in the queue row.

| Order | ID | Priority | Status | Review | Dependencies | Task file |
|---:|---|---|---|---|---|---|
| 1 | TASK-001 | P0 | QUEUED | REQUIRED | — | [TASK-001](TASK-001.md) |

Update a task's status here in the same commit that updates its task file. For
`CHANGES_REQUESTED`, the reviewer records `IN_PROGRESS` here alongside the
durable `tasks/reviews/<TASK-ID>.md` review record; the review record, rather
than chat output, is the implementer's source of requested changes.

**Archiving.** Once this table grows large enough that opening it costs more
than the queue-briefing summary can save, move its `ACCEPTED` rows to
`tasks/QUEUE_ARCHIVE.md` (create it, mirroring this file's own column
structure, if it doesn't exist yet), keeping this table to active and queued
work only — the same archiving convention Lean Delivery projects already
follow for closed phases. `ACCEPTED` rows still satisfy dependencies from
their archived location; nothing about moving a row changes what it
satisfies, only where it is read from.
