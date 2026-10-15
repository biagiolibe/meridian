# Task 220 — Accept a queue link to a record archived on its task branch

> **ID**: `220`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Task 217 closure stop, 2026-10-15
> **Origin**: friction

## Objective

A task branch must archive its record under `tasks/done/` but may not edit
`tasks/QUEUE.md`. `integrate stage` relinks the queue row on the merged
candidate (`_relink_archived_task_row` in `scripts/meridian.py`). Until then,
`python3 scripts/check_repository.py` on the task branch reports the queue
row's link as broken. Tasks 208, 209, and 215 recorded the failure as
expected. Task 217 treated it as a blocker, restored its record, and stopped.
A required validation command must not fail on a state that the workflow
requires.

## Acceptance Criteria

- [x] `check_local_markdown_links` accepts exactly one case. A link in
  `tasks/QUEUE.md` whose target `tasks/<name>.md` is missing is accepted when
  `tasks/done/<name>.md` exists. It still fails for every other missing
  target, including a missing archive and links from any other file.
- [x] The accepted case is printed as an informational line that names the
  link and states that `integrate stage` relinks it. The check still exits
  `0`.
- [x] Tests cover the accepted case, a missing archive, the same link from a
  file other than `tasks/QUEUE.md`, and an ordinary broken link.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | `check_local_markdown_links`. |
| `tests/` | Repository-check tests. |

## Technical Context

- On `main` the case never occurs, because `integrate stage` relinks the row
  before finalize. The tolerance therefore matters only on task branches.
- Repository maintenance check only. No CLI or managed text changes, and no
  changelog fragment.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing the relink in `integrate stage` and checks in adopter projects.

## Dependencies

- **Depends on**: —
- **Blocks**: none
