# Task 105 — Derive `[/]` and show closure stop reasons in the console

> **ID**: `105`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Make the project console show a task as in progress from its branch, registered worktree, and unarchived record (Decision 2) and show the closure stop reason and next action from `closure-status` (Decision 7).

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [x] A task with a canonical branch and registered worktree but a `[ ]` queue row displays as in progress.
- [x] The detail pane shows the stop reason and resume command for each stop in the design, including `REVIEW_REQUIRED`.
- [x] Refresh latency does not regress: tests or a timing check cover the added reads (see task 078).
- [x] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | Changed or read by this task. |
| `scripts/console_workflow.py` | Changed or read by this task. |
| `tests/test_project_console.py` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 101, 103
