# Task 101 — Add `meridian worktree closure-status`

> **ID**: `101`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Add a read-only `meridian worktree closure-status <TASK-ID> --project <primary> --format json` that derives, from Git and lifecycle state alone, the current closure step (C1 to C10), the stop reason if any, and the resume command, per Decision 5 of `docs/TASK_CLOSURE_DESIGN.md`.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] Output contains `step`, `stop_reason` (or null), and `resume` for every state the design lists, and prints `BLOCKED <REASON>; resume: <command>` in text mode.
- [ ] The command mutates nothing: no Git write, no lease, no file; tests assert the repository and lifecycle state are byte-identical before and after.
- [ ] States covered by tests: not prepared, in progress, completion committed, active integration, finalized and unpushed, pushed, cleaned.
- [ ] Exit codes follow `docs/WORKTREE_LIFECYCLE.md` (0, 2 blocked, 64 usage).
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

- **Depends on**: 100
