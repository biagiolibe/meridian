# Task 200 — Add `meridian review verdict` bound to the reviewed commit

> **ID**: `200`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR machine task state, 2026-10-11
> **Origin**: friction

## Objective

Implement the verdict part of Decision 2 of
`docs/ADR_MACHINE_TASK_STATE.md`. A reviewer records a verdict through a
command, which stores the reviewed commit in the task state file and applies
the matching transition. It does not write a heading that a gate later
parses.

## Acceptance Criteria

- [ ] `meridian review verdict <TASK-ID> APPROVE|CHANGES_REQUESTED|BLOCKED
  [--owner] --project <path> --format json`, run in the task worktree:
  - sets `review.required`, `review.verdict`, the next `review.attempt`,
    `review.reviewed_commit` (the task branch `HEAD`), and `review.approved_by`
    (`reviewer`, or `owner` with `--owner`);
  - applies the state-machine transition: `APPROVE` from `READY_FOR_REVIEW`
    gives `ACCEPTED`, and `CHANGES_REQUESTED` gives `CHANGES_REQUESTED`;
  - leaves the status unchanged for `BLOCKED`.
- [ ] It also appends the attempt heading to the review record as a
  human-readable projection, using the reviewer's free-form body. No gate
  reads that heading.
- [ ] It refuses, with `TASK_STATE_INVALID` and no write:
  - a verdict in a status that does not allow it;
  - a dirty worktree;
  - a `HEAD` that is not the task branch.
- [ ] The verdict and transition are written in one atomic file write.
  Rerunning the same verdict at the same commit is a no-op.
- [ ] Tests cover each verdict, `--owner`, refusal in a wrong status, a dirty
  worktree, the attempt counter, and the no-op rerun.
- [ ] One changelog fragment states the command under `Added`; this is a
  CLI-only change.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | New `review` subcommand and the shared state reader from task 199. |
| `tests/` | Verdict tests. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decision 2.
- The commit binding is checked later by `integrate stage` (task 201). This
  task only records it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

The integration gate and the managed review procedure text.

## Dependencies

- **Depends on**: 199
- **Blocks**: 201
