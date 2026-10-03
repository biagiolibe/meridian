# Task 140 — Let `integrate stage` complete rows of project-shaped Governed queues

> **ID**: `140`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Blocked integration of Palimpsest task M37-CAUSE-001, 2026-10-03

## Objective

`meridian worktree integrate stage` completes the queue row of the task it
integrates (tasks 103 and 117). For Governed SDD it recognizes only rows of the
exact template shape, seven columns:
`| Order | ID | Priority | Status | Review | Dependencies | Task file |`
(`_GOVERNED_QUEUE_TASK_ROW` in `scripts/meridian.py`). A project that keeps its
own queue with a different, valid shape cannot integrate any task: Palimpsest's
queue has six columns (`| Order | ID | Priority | Status | Dependencies | Estimate |`),
and stage stopped with `BLOCKED: unrecognized completion row for task
M37-CAUSE-001 in docs/TASK_QUEUE.md`. The previous task of that project had been
integrated before the 1.2.4 upgrade, when stage did not touch the queue. Make
stage locate the row by column name so project-shaped queues work, without
guessing when a shape is truly ambiguous.

## Acceptance Criteria

- [ ] For Governed SDD, stage finds the task's row in the resolved queue file by the
  table header of the section that contains it: it requires an `ID` column and a
  `Status` column, matched by name, and changes only the `Status` cell of that row
  to `ACCEPTED`. Every other cell, the column order, the spacing, and the rest of
  the file stay byte-for-byte unchanged.
- [ ] A queue row of the existing seven-column template shape behaves exactly as
  today, including the review-record check, and the existing tests keep passing
  unchanged.
- [ ] When the table has no `Review` column, the review requirement
  (`REQUIRED` or `NOT_REQUIRED`) comes from the task record using the same reader
  the console uses, not from a new parser. A `REQUIRED` task is completed only when
  its merged review record's latest attempt is `APPROVE`; otherwise stage reports
  the existing `REVIEW_PENDING` result and retains its status.
- [ ] Stage still blocks, without changing any lifecycle record, when: the ID appears
  zero times or more than once across the queue's tables; the section has no table
  header with both required columns; the row's cell count differs from the
  header's; or the `Status` value is not a known Governed status. Each message
  names the file, the section, and the reason.
- [ ] Heading levels, per-milestone sections, em-dash dependency cells, and
  suffixes such as `— complete` in section headings are accepted. Backticked IDs
  are matched as today.
- [ ] Phase archival is unchanged: a section whose header is not the template shape
  is skipped and never moved, so a project-shaped queue is never archived by this
  change. A test proves a fully accepted project-shaped section stays in place.
- [ ] Lean Delivery stage behavior is unchanged.
- [ ] A dependency or review column in another position, or extra columns such as
  `Estimate`, does not change the result.
- [ ] The documentation (`docs/WORKTREE_LIFECYCLE.md` and the Governed workflow
  text that says unknown shapes are blocked) states the new rule: recognition is by
  header name, with the exact set of required columns and the conditions that still
  block.
- [ ] Tests cover: a Palimpsest-shaped queue (six columns, per-milestone sections,
  `—`) completing correctly; the same with a `Review` column in another position;
  an `Estimate` column; a missing `Status` column; a duplicate ID across sections; a
  cell-count mismatch; an unknown status value; a `REQUIRED` task with and without an
  approving review record; archival not moving a project-shaped section; and the
  seven-column shape unchanged.
- [ ] A rehearsal on a scratch copy of the real Palimpsest queue stages M37-CAUSE-001
  through `integrate stage`, shows the one-cell diff, and aborts the staged merge.
  The result and the diff are recorded in the handoff; the real project is not touched.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`. Because the stage
  behavior is shipped CLI code, this is a CLI-only change unless managed template
  text changes.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_GOVERNED_QUEUE_TASK_ROW`, `_governed_completion_row`, and the archival helper. |
| `scripts/console_workflow.py` | Column-aware queue parsing and the review reader to reuse. |
| `docs/WORKTREE_LIFECYCLE.md` | Stage contract for queue rows. |
| `templates/workflows/governed-sdd/` | Workflow text that mentions unknown shapes, only if it must change. |
| `tests/test_task_worktree_isolation.py` | Stage tests with fixtures. |

## Technical Context

- Observed on 2026-10-03 in Palimpsest: `meridian worktree integrate stage
  M37-CAUSE-001` blocked with `unrecognized completion row` because its queue row
  is `| 2 | M37-CAUSE-001 | P0 | QUEUED | M37-SPIKE-001 | 60–90m |` (six columns, no
  `Review`, no task-file column). F1-FIGURE-001 was integrated on 2026-10-01 under a
  Meridian that did not modify the queue; the upgrade to 1.2.4 on 2026-10-03 added
  the row completion. The agent stopped without a manual merge or push, the primary
  checkout was clean, and the machine evidence was recorded, so stage is safely
  restartable once this is fixed.
- The console already parses queues by column name for both workflows
  (`parse_queue`), so project-shaped queues are displayed correctly; stage should
  not keep a second, stricter grammar.
- Archival requires the template header
  (`| Order | ID | Priority | Status | Review |`), so a project-shaped section is
  not moved today; this task keeps that behavior and does not add an archival mode
  for such queues.
- The project's queue is a long single file with one section per milestone; the
  change must not require the project to restructure it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`
- The recorded scratch rehearsal on the Palimpsest queue.

## Out of scope

Rewriting or migrating a project's queue, adding an archival mode for
project-shaped queues, changing Lean Delivery, changing the review policy, and
touching the real Palimpsest repository.

## Dependencies

- **Depends on**: —
- **Blocks**: none
