# Task 167 — Make the execution preflight satisfiable during remediation

> **ID**: `167`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1.5h
> **Assigned to**: Claude Code
> **Session**: ADR stops and denials, 2026-10-05

## Objective

Issue #6: `execution_preflight` requires the task record status to equal the
task's queue row status. A task branch may not edit the queue, and a review
that requests changes returns the record to `IN_PROGRESS`. Every Governed SDD
remediation is therefore blocked in `ready-check`, `validate`, and possibly
`investigate`. The only workaround writes a false status. This breaks the
"satisfiable" property of `docs/ADR_STOPS_AND_DENIALS.md`. Make the gate
accept the states that the workflow itself produces.

## Acceptance Criteria

- [x] On a task branch, the preflight accepts a queue row of `QUEUED` against
  a task record of `QUEUED`, `IN_PROGRESS`, `CHANGES_REQUESTED`, or
  `READY_FOR_REVIEW`. This is the second option proposed in issue #6. If the
  developer has chosen a different option in the issue before work starts,
  implement that one and record the choice in the handoff.
- [x] Combinations that the workflow cannot produce still fail, with the coded,
  actionable message from task 166. The message names which document the
  current actor is permitted to change.
- [x] Tests reproduce issue #6 for `ready-check` and `validate` and pass after
  the fix. A test also proves that `investigate` takes the same path.
- [x] No gate in this change requires the actor on the task branch to edit
  `tasks/QUEUE.md`, `tasks/QUEUE_ARCHIVE.md`, or `PROJECT_PLAN.md`.
- [x] One changelog fragment is added under `Fixed`; this is a CLI-only change.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `execution_preflight`, `run_validation`, `record_investigation`. |
| `tests/test_meridian_cli.py` | Remediation tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decision 2, property 2.
- The comparison was introduced by `85f1c16` ("enforce execution evidence
  contracts").
- The freshness of execution evidence raised in the issue's comment is a
  separate decision and stays out of scope.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Evidence freshness, changing who edits governance files, and the handoff field
format (task 166).

## Dependencies

- **Depends on**: 166
- **Blocks**: none
