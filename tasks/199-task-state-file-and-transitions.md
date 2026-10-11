# Task 199 — Add the task state file, its state machines, and `meridian task transition`

> **ID**: `199`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR machine task state, 2026-10-11
> **Origin**: friction

## Objective

Implement Decisions 1 and 2 of `docs/ADR_MACHINE_TASK_STATE.md` for status:
one tracked, schema-validated `.meridian/tasks/<TASK-ID>.json` per task, and
a command that changes its status only through the workflow's state machine.

## Acceptance Criteria

- [ ] A schema in `schemas/` defines version 1 of the state file:
  - top-level `version`, `task_id`, `workflow`, `status`, `transitions`;
  - an optional `review` object with `required`, `verdict`, `attempt`,
    `reviewed_commit`, and `approved_by`.
  Commits are full 40-character SHAs, and times are ISO-8601 UTC.
- [ ] One module defines the two state machines and validates a whole
  transition history against them:
  - Governed SDD: `QUEUED`, `IN_PROGRESS`, `CHANGES_REQUESTED`,
    `READY_FOR_REVIEW`, and `ACCEPTED`, plus `ANSWERED` and `INCONCLUSIVE` for
    SPIKE tasks;
  - Lean Delivery: `QUEUED` and `DONE`.
- [ ] `meridian task transition <TASK-ID> <STATUS> --project <path> --format
  json`:
  - creates the file on the first transition;
  - appends one transition with the current `HEAD` and time, and writes the
    file atomically;
  - updates the record's `Status:` field as a projection when the record has
    one.
  It refuses a transition that is not allowed, an unknown status, or an
  invalid existing file with `TASK_STATE_INVALID`. The detail names the field
  or transition, the allowed values, and the value found, and nothing is
  written.
- [ ] `TASK_STATE_MISSING` and `TASK_STATE_INVALID` are registered in
  `capabilities/stop-codes-v1.json` with tests that assert their output lines.
- [ ] A shared reader returns the parsed state or a coded stop, and every
  later consumer uses it. No other code parses the file.
- [ ] Tests cover:
  - every allowed transition and a refused one in each workflow;
  - first-file creation, atomic write, and projection of the record field;
  - a schema failure, an impossible history, and an unknown status.
- [ ] One changelog fragment states the command under `Added`; this is a
  CLI-only change.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `task` subcommands (around the `task` parser), the shared reader, and the stop helper. |
| `schemas/` | State file schema. |
| `capabilities/stop-codes-v1.json` | New codes. |
| `tests/` | State machine and command tests. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decisions 1, 2, and 5.
- Status vocabulary matches `_GOVERNED_QUEUE_STATUSES`. Lean in-progress state
  stays derived from the worktree, so Lean has only `QUEUED` and `DONE`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Review verdicts (task 200), the integration gate (task 201), the console
(task 202), and managed text (task 203).

## Dependencies

- **Depends on**: —
- **Blocks**: 200, 202
