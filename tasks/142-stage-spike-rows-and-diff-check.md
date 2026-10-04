# Task 142 — Recognize spike rows at stage and require `git diff --check` at finalize

> **ID**: `142`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2.5h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D4/D5, design approved 2026-10-04

## Objective

Two lifecycle-command defects reported by a Governed SDD consumer (Palimpsest,
Meridian 1.2.6):

1. `review-policy` v2 tells a project to put `SPIKE` in a queue row's `Review`
   column and to record `ANSWERED` or `INCONCLUSIVE`. In Governed mode,
   `_archive_completed_queue_sections` matches the template table header literally
   and raises `unrecognized queue section shape` when any row fails
   `_GOVERNED_QUEUE_TASK_ROW`, whose pattern accepts neither `SPIKE` nor those two
   statuses. A template-shaped queue that follows the policy therefore blocks
   `integrate stage` for every other task in that section. `_governed_completion_row`
   also rejects `ANSWERED`/`INCONCLUSIVE` and a `SPIKE` review value.
2. The documented candidate gate always includes `git diff --check`, but
   `integrate finalize` does not require it in the candidate evidence, and a
   `none` candidate-validation declaration then enforces nothing at all.

Approved decisions: a spike integrates through `integrate stage` like any task,
but only with its deliverable (an ADR or documented reference value) and
governance records, never production code; `finalize` requires `git diff --check`
in every declaration state.

## Acceptance Criteria

- [ ] Governed queue recognition accepts `SPIKE` as a `Review` value and
  `ANSWERED`/`INCONCLUSIVE` as statuses, in both the template-shaped regex and the
  header-named reader from task 140. A template-shaped section containing a spike
  row no longer blocks stage for another task.
- [ ] Phase archival moves a Governed section only when every row is `ACCEPTED` or
  `ANSWERED`; a section containing `INCONCLUSIVE` stays in the queue.
- [ ] For a task whose record declares `Class: SPIKE`, stage completes the queue
  row to the record's terminal state (`ANSWERED` or `INCONCLUSIVE`), never to
  `ACCEPTED`, and does not require a review record.
- [ ] For a spike, stage returns `BLOCKED` without lease, merge, or staged state
  when the task diff against its validated base contains any path other than the
  task record or its exact archive rename, its handoff, ADR log or documentation
  paths named in the task's deliverable, and changelog fragments. The message names
  each disallowed path.
- [ ] `integrate finalize` rejects candidate evidence whose commands do not include
  `git diff --check`, for `declared` and `none` states alike, with a message naming
  the missing command. Existing declared-fragment checks are unchanged.
- [ ] `docs/WORKTREE_LIFECYCLE.md` (both workflow templates and this repository's
  copy) states the spike integration rule and the always-required
  `git diff --check`.
- [ ] Lean Delivery stage and finalize behavior is otherwise unchanged.
- [ ] Tests cover: a template-shaped section with a spike row and another task
  integrating; archival with `ANSWERED`, and retention with `INCONCLUSIVE`; spike
  completion to `ANSWERED`; a spike diff with a source file blocked; finalize with
  and without `git diff --check` under `declared` and `none`.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; managed copies changed
  here get refreshed digests.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_GOVERNED_QUEUE_TASK_ROW`, `_GOVERNED_QUEUE_STATUSES`, `_governed_completion_row`, `_archive_completed_queue_sections`, `stage_task_integration`, finalize evidence check (`missing_candidate_validation_commands`). |
| `templates/workflows/*/docs/WORKTREE_LIFECYCLE.md`, `docs/WORKTREE_LIFECYCLE.md` | Documented stage and finalize rules. |
| `tests/test_task_worktree_isolation.py` and stage tests | Lifecycle tests. |

## Technical Context

- Task 140 made stage locate a Governed row by header name; this task extends the
  accepted values, not the lookup.
- `record_review` and the task-record reader used by the console are the sources
  for `Class: SPIKE`; do not add a new parser.
- The capability text that tells spikes their branch "is never merged" is corrected
  by task 145; this task ships only the command behavior and its reference doc.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Capability text in `PROJECT_WORKFLOW.md` and workflow documents (task 145), the
queue-briefing hook (task 143), and any change to how non-spike tasks are reviewed.

## Dependencies

- **Depends on**: —
- **Blocks**: 145
