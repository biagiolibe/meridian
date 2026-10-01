# Task 104 — Apply phase archival during `integrate stage`

> **ID**: `104`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Implement the archival part of Decision 2: when, on the integrated candidate tree, every row of a phase is `[x]`, `integrate stage` moves that section to `tasks/QUEUE_ARCHIVE.md`, mirroring its table structure and creating the file when absent.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] Archival happens only when the whole section is `[x]` on the candidate tree, never from a task branch.
- [ ] The step is idempotent and `BLOCKED` on an unrecognized section shape without editing.
- [ ] Tests cover a closing phase, a still-open phase, a missing archive file, and a rerun.
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

- **Depends on**: 100, 103
