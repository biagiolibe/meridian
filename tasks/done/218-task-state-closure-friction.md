# Task 218 — Detect missing closure state early and point recovery at the task worktree

> **ID**: `218`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 209 closure stop, 2026-10-14
> **Origin**: friction

## Objective

Task 209 archived its record and handed off without running
`meridian task transition 209 DONE`. Three tool behaviors then turned one
missed step into a manual recovery:

1. `meridian worktree advance` accepted the closure and failed only inside
   `integrate stage`, with `BLOCKED TASK_STATE_MISSING`.
2. The stop's resume hint, from `capabilities/stop-codes-v1.json`, named the
   primary checkout as `--project`. Run there, the command writes the state
   file on `main`, outside the task commit, and the gate still fails.
3. `meridian task transition` and `meridian task state import` resolve only
   the unarchived record, so recovery required moving the archived record back
   out of `tasks/done/`, importing, and archiving again.

Make the stop arrive before integration, with a resume command that works
as printed.

## Acceptance Criteria

- [ ] `meridian worktree advance` checks, before it starts `integrate
  stage`, that the task commit tracks `.meridian/tasks/<TASK-ID>.json` with a
  terminal status for its workflow. When the file is missing, advance stops
  with `TASK_STATE_MISSING` and an `action_required` that names the exact
  command to run in the task worktree. When the file is present but not
  terminal, it stops with the existing state stop. Nothing is staged in either
  case.
- [ ] Every printed `TASK_STATE_MISSING` resume command uses the canonical
  task worktree path as `--project` when a registered worktree exists for the
  task, and the primary checkout only when none exists. The stop-code registry
  documents both forms.
- [ ] `meridian task transition` and `meridian task state import` accept a
  task whose record is already archived at its exact archive path under
  `tasks/done/`. The state file is written in the same project. The record is
  never moved.
- [ ] Tests cover:
  - advance with a missing state, with a non-terminal state, and with a
    terminal state;
  - the resume path with and without a registered worktree;
  - transition and import on an archived record.
- [ ] One changelog fragment states the behavior under `Fixed`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `advance_task_closure`, the integration state gate, `transition_task_state`, `task state import`, stop rendering. |
| `capabilities/stop-codes-v1.json` | `TASK_STATE_MISSING` resume text. |
| `tests/` | Lifecycle and task-state tests. |

## Technical Context

- The integration gate reads the state with `git show <task_commit>:<path>`
  and raises `TASK_STATE_MISSING` when it is absent. Advance can use the same
  reader against the same commit.
- Evidence: commits `f14a257` (archive without state), `cecbe95` (restore and
  import), `4867c27` (re-archive), and `0558701` (integration).
- CLI-only. No managed text changes.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Creating the state file automatically, and changing the closure order in
managed text. Both are decided separately.

## Dependencies

- **Depends on**: —
- **Blocks**: none
