# Task 107 — Block `integrate stage` when `main` is behind `origin` and report a pending push

> **ID**: `107`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Add the C6 precondition and the C9 report from Decision 5: `integrate stage` returns `BLOCKED MAIN_BEHIND_ORIGIN` when local `main` lacks commits that `origin/main` has, and `closure-status` reports a finalized but unpushed integration.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [x] The check uses the already fetched remote ref and never runs `git push`, `git pull`, or `git fetch` inside the lifecycle command; the agent fetches first.
- [x] A repository without an origin skips the check.
- [x] `closure-status` reports `PUSH_PENDING` when local `main` is ahead of `origin/main` after finalize.
- [x] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |
| `docs/WORKTREE_LIFECYCLE.md` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 100, 101
