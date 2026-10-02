# Task 102 — Add the evidence command and recompute main-advance facts in `integrate stage`

> **ID**: `102`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Collect handoff facts by command (Decision 4) and make `integrate stage` recompute the facts a moved `main` makes stale (Decision 3). Read `docs/EXECUTION_EVIDENCE_PROFILE.md` first and place the command where it fits.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] A command writes the stage evidence JSON (untracked) with the validated task commit, validated base commit, changed paths, and the validation commands and exit codes the agent passes in; it runs no validation command.
- [ ] `integrate stage` computes the paths changed on `main` since the validated base and their overlap with the task paths; typed `main_advanced_*` fields can only raise the scope to `FULL`, never lower it.
- [ ] Overlap yields `FULL`; no overlap and no declared dependency keeps `REUSE` or `BOUNDED`; tests cover each.
- [ ] Existing hand-written evidence files still validate.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |
| `docs/WORKTREE_LIFECYCLE.md` | Changed or read by this task. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 100
