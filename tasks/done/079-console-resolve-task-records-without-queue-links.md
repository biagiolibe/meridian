# Task 079 — Resolve task records in the console when the queue has no file link

> **ID**: `079`
> **Category**: Developer tooling
> **Priority**: 🔴 P1
> **Assigned to**: unassigned
> **Session**: Developer report that the console shows STALE on the Palimpsest project

## Objective

Make the project console usable on Governed SDD projects whose queue carries no
file-link column. Launched on Palimpsest, whose queue
(`docs/TASK_QUEUE.md`) has the columns
`Order | ID | Priority | Status | Dependencies | Estimate`, the console shows
`STALE: task M37-CAUSE-001 has no unambiguous file link` and no tasks. The task
records exist (`docs/tasks/M37/M37-CAUSE-001.md`) and the project declares
them through `task_roots`, but `_task_path` in `scripts/project_console.py`
accepts only a queue link, and one unresolved record aborts the whole snapshot.

## Acceptance Criteria

- [x] A task's record is resolved in this order: the queue row's file link when
  present; otherwise a file named `<ID>.md` under the task roots returned by
  `resolve_project_locations`, searched recursively.
- [x] The search ignores review records and handoffs: any path under the
  project's declared review root or handoff root, and any directory named
  `reviews` or `handoffs`.
- [x] A queue link that is present but invalid keeps its current rejection;
  the fallback search is used only when the row has no link at all.
- [x] Zero matches or more than one match for a task is a per-task problem, not
  a snapshot failure: the task still appears with its title and status from the
  queue, the detail view states "task record not found" or lists the ambiguous
  paths, and the task offers no launch directive.
- [x] Missing record data (objective, criteria, update time) renders as
  unavailable and never blocks the rest of the list.
- [x] The same resolution is used when a task's record is read from its task
  branch, so effective-state reads work for projects without links.
- [x] A queue without a `Review` column is read as no declared review policy;
  the console does not infer `REQUIRED` or `NOT_REQUIRED`, and offers no
  `Review` directive for such a task.
- [x] Lean Delivery projects and Governed SDD projects with link columns behave
  exactly as before.
- [x] A fixture shaped like Palimpsest passes: a queue without file or review
  columns, records under `docs/tasks/<milestone>/`, review records under
  `docs/tasks/reviews/`, handoffs under `tasks/handoffs/`, and statuses
  including `ANSWERED`. The console lists every task and reports no `STALE`
  state.
- [x] Running the console against a local copy of Palimpsest, or against this
  repository's equivalent fixture, lists all queue rows and reports no error;
  the exact command and result are recorded in the handoff.
- [x] Scan time stays within the bound set by Task 078: record resolution does
  not add per-task subprocess work.

## Relevant Files and Context

- `scripts/project_console.py`: `_task_path`, `load_snapshot`, `_branch_facts`.
- `scripts/console_workflow.py`: `QueueRow`, `parse_queue`, `link_target`.
- `scripts/meridian.py`: `resolve_project_locations`, which returns the queue,
  `task_roots`, `handoff_root`, and `review_root`.
- Measured before this task on Palimpsest: 300 queue rows; with review and
  handoff directories excluded, every row matches exactly one
  `<ID>.md` under `tasks/` and `docs/tasks/`. Without that exclusion, 148 rows
  match more than one file because review records share the task ID.
- The 076 and 077 drafts assumed the template's `Task file` column; Palimpsest
  shows a real project may omit it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- New tests: the Palimpsest-shaped fixture, a duplicate record, a missing
  record, a present-but-invalid link, a row without a review column, and a
  record read from a task branch.
- Interactive PTY smoke check against the Palimpsest-shaped fixture.

## Out of scope

Launching agents (Task 077), editing Palimpsest, changing any project's queue
format, and the refresh behavior covered by Task 078.

## Dependencies

- **Depends on**: 076, 078
- **Blocks**: 077
