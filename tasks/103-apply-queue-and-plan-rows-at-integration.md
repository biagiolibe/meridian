# Task 103 — Apply queue and plan row status during `integrate stage`

> **ID**: `103`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Implement the row-status part of Decision 2: after its no-commit merge, `integrate stage` sets the task's row to `[x]` in `tasks/QUEUE.md` and `PROJECT_PLAN.md` on the candidate tree, so task branches no longer need to edit those files.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] The edit is deterministic text editing of the known row shapes by Meridian code; it runs no project-provided command.
- [ ] It is idempotent: a row already holding the target text is a no-op, and an unrecognized row shape is `BLOCKED` without editing.
- [ ] A branch that does not touch the governance files integrates cleanly after `main` gains a registration commit; a test reproduces the 063 trigger shape (+1 plan line, +10 queue lines on `main`).
- [ ] A branch that still carries its own `[x]` edits integrates as today.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

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

- **Depends on**: 100, 102
