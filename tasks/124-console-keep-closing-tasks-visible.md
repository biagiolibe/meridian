# Task 124 — Keep a closing task visible in the console until cleanup, in both workflows

> **ID**: `124`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Console observation during task closure, 2026-10-03

## Objective

The project console drops a task as soon as `meridian worktree integrate stage`
runs, although the task still has candidate validation, finalize, the `main`
push, and cleanup to do. Everything the task does after staging, including the
closure progress added by task 119, is invisible. Keep the task listed, with its
closure step, until cleanup removes its canonical worktree. The behavior and the
console features added by tasks 105, 118, and 119 must hold for Governed SDD as
well as Lean Delivery.

Design decision: the queue status is **not** changed for the closing window.
`integrate stage` owns queue and plan status, task branches must not edit them,
and a new persisted state would need parser, profile, and migration changes in
both workflows. The console instead derives a display-only `CLOSING` lifecycle
value, like the derived `[/]` of task 105, from facts Meridian already owns.

## Acceptance Criteria

- [ ] A task whose staged or finalized state marks its queue row done (`[x]` in
  Lean Delivery, `ACCEPTED` in Governed SDD) in the primary checkout stays in the console while any closure work remains: an
  active integration lease or staged merge, a finalized merge awaiting the
  `main` push, or a registered canonical worktree or branch not yet cleaned up.
- [ ] While listed in that state, the task shows the derived `CLOSING` readiness
  and lifecycle value (queue and plan files keep their real status, and nothing
  is written), plus its
  `closure-status` step and resume action, its elapsed time, and the lifecycle
  progress phase (candidate validation, push pending, cleanup pending).
- [ ] The task disappears from the active list once cleanup has completed (no
  canonical worktree, no unmerged branch, no integration state). A task that is
  `[x]` with no closure work left is hidden exactly as today.
- [ ] A closing task does not count as ready, does not offer launch actions
  intended for a TODO task, and does not unblock its dependents earlier than
  the existing rule allows.
- [ ] Governed SDD parity: the closing behavior above works with the
  `governed-sdd` profile; elapsed time and lifecycle progress (task 119) are
  also shown for a Governed task in `READY_FOR_REVIEW` that has a registered
  worktree, and the progress phases include the review gate (`REVIEW_REQUIRED`
  at C3) so a task waiting for approval does not read as `unavailable`.
- [ ] Framework identity (task 118) and the derived in-progress and closure stop
  reasons (task 105) are verified for `governed-sdd` and any gap is fixed here.
- [ ] Reading lifecycle state for this path remains non-fatal: a transient
  failure shows `unavailable` and never makes the console stale.
- [ ] `--once` output lists the closing task with the same facts.
- [ ] Tests run for both profiles and cover: visible after stage, visible after finalize with a pending
  push, hidden after cleanup, hidden for an ordinary completed task, filter and
  count behavior, launch exclusion, the `CLOSING` label, Governed `READY_FOR_REVIEW` elapsed time and progress,
  and the transient-failure case.
- [ ] The console documentation describes the closing state.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | Row filter that skips done rows, progress and closure display. |
| `scripts/console_workflow.py` | Effective-state derivation from the primary row and branch facts. |
| `tests/test_project_console.py` | Console state and rendering tests. |
| `README.md` | Console field documentation. |

## Technical Context

- `integrate stage` applies the `[x]` status to the primary checkout's queue
  and plan on the merged candidate tree. The console builds its task list from
  that queue and skips every row whose phase is done
  (`scripts/project_console.py`, the loop over `active_rows`), so the staged
  task vanishes even though `closure-status` still reports steps C7 to C10.
- The facts needed to keep it visible already exist: the registered worktree,
  the branch, and the lifecycle integration state, which `closure_status`
  derives. Reuse that derivation and do not add a second interpretation.
- Task 105 derives `[/]` for active tasks; this extends the same idea to the
  closing window, which is the gap its design did not cover.
- Observed Governed gap (from code reading): the lifecycle read in
  `scripts/project_console.py` runs only when `effective.lifecycle ==
  "in_progress"`, so a Governed task in `READY_FOR_REVIEW` gets no elapsed time
  or progress, and `_lifecycle_progress` has no review phase. The existing
  console tests have no Governed case for progress.
- Confirm the cause by reproducing it with a staged fixture before changing the
  filter; this task was written from code reading, not from a reproduction.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing `integrate stage`, queue or plan content, closure semantics, and the
command policies (task 123).

## Dependencies

- **Depends on**: 119
- **Blocks**: none
