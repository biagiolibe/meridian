# Task 202 — Read task state in the console and in `meridian audit`

> **ID**: `202`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR machine task state, 2026-10-11
> **Origin**: friction

## Objective

Implement the read side of Decision 4 of `docs/ADR_MACHINE_TASK_STATE.md`:
the console takes status and verdict from the task state file, and `audit`
reports where prose projections differ from it.

## Acceptance Criteria

- [ ] The console reads each task's state file through the shared reader from
  task 199 before any queue cell, record field, or review heading. It shows
  status and verdict from the state file. A task without a state file falls
  back to today's behavior and is labeled `legacy` in the detail pane and the
  `--once` output.
- [ ] An invalid state file is shown as an explicit per-task error with its
  coded detail. It never silently falls back to prose.
- [ ] `meridian audit` adds one row per task state file:
  - `PASS` when the queue `Status` cell and the record `Status:` field equal
    the state;
  - `ADVISORY` naming the file, the projection, and both values when they
    differ.
  It never edits a file.
- [ ] The `done` count and the behavior of tasks 195 and 196 do not change for
  legacy tasks.
- [ ] Tests cover a state-backed task, a legacy task, an invalid state file,
  and an audit drift row.
- [ ] One changelog fragment states the change under `Changed`; this is a
  CLI-only change.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py`, `scripts/console_workflow.py` | Status and verdict derivation. |
| `scripts/meridian.py` | `audit` rows. |
| `tests/test_project_console.py`, `tests/test_meridian_cli.py` | Tests. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decision 4.
- `latest_review_verdict` remains only for legacy tasks.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing the queue's Markdown format and repairing prose automatically.

## Dependencies

- **Depends on**: 199
- **Blocks**: 203
