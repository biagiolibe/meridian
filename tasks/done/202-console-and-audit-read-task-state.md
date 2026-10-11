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

- [x] The console reads each task's state file through the shared reader from
  task 199 before any queue cell, record field, or review heading. It shows
  status and verdict from the state file. A task without a state file falls
  back to today's behavior and is labeled `legacy` in the detail pane and the
  `--once` output.
- [x] An invalid state file is shown as an explicit per-task error with its
  coded detail. It never silently falls back to prose.
- [x] The console opens only the state files of rows in the active queue, by
  task ID, and never scans the `.meridian/tasks/` directory. A test with many
  state files for archived tasks proves that they are not read.
- [x] `meridian audit` adds one row per task state file:
  - `PASS` when the queue `Status` cell and the record `Status:` field equal
    the state;
  - `ADVISORY` naming the file, the projection, and both values when they
    differ.
  It never edits a file.
- [x] The `done` count and the behavior of tasks 195 and 196 do not change for
  legacy tasks.
- [x] Tests cover a state-backed task, a legacy task, an invalid state file,
  and an audit drift row.
- [x] One changelog fragment states the change under `Changed`; this is a
  CLI-only change.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py`, `scripts/console_workflow.py` | Status and verdict derivation. |
| `scripts/meridian.py` | `audit` rows. |
| `tests/test_project_console.py`, `tests/test_meridian_cli.py` | Tests. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decisions 4 and 7.
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

## Completion

The console addresses machine state by active queue task ID through the shared
reader, including task-branch and worktree state. Status and review verdict
come from the validated snapshot; Class remains metadata for choosing the
SPIKE machine. Missing state retains the existing prose behavior and is
labeled legacy in details and one-shot output. Invalid state produces a coded
per-task error and disables task launch without hiding other tasks.

Audit explicitly enumerates task state, compares normalized queue status and
record status, and emits one PASS, ADVISORY, or invalid-state FAIL row per
file without writing. It also checks archived projections. Console refresh
never enumerates the task-state directory or opens archived tasks' state.

Validation on `6b64b569c13d407916a61039270b2d00a5e33e3b`:
- `python3 scripts/check_repository.py` — exit 0.
- `python3 scripts/run_tests.py --parallel` — exit 0; 961 tests, zero failures
  or errors, one named environmental skip, eight shards, complete coverage.
- `git diff --check` — exit 0.

Tests cover authoritative state before unknown queue projections, branch and
worktree state, review verdict precedence, invalid primary/worktree JSON,
legacy labels and unchanged launch behavior, 150 unread archived state files,
Lean derived progress, SPIKE terminal state, audit drift and read-only output,
invalid audit state, and archived Lean checkbox normalization. Existing
legacy closure, progress, dependency, and done-count tests remain passing.

The skipped `test_project_console.AgentLaunchTest.test_split_payload_compiles_as_applescript`
reports that osacompile cannot resolve the iTerm2 dictionary in this environment
(Connection Invalid for com.apple.hiservices-xpcservice; compilation error
-2740). Its verbose isolated invocation reports the skip with exit 0. No
acceptance criterion depends on AppleScript compilation.
