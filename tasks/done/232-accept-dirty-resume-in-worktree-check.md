# Task 232 — Let `worktree check` accept a dirty worktree during Resume

> **ID**: `232`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: 1.4.1 blocking fixes, 2026-10-18
> **Origin**: friction

## Objective

Every Resume of an interrupted task with uncommitted work stops, whatever the
agent does. The managed `bounded-worktree-lifecycle` text says that after
`meridian worktree prepare <task-id> --resume` returns `dirty: true`,
`dirty-worktree` is the only error that `worktree check` may report, and the
agent continues after reading the status and the diff. But `worktree check`
exits 2 with `BLOCKED WRONG_WORKTREE` for that error. Its resume command is
`worktree prepare` without `--resume`, which refuses the dirty worktree.
`AGENTS.md` and `CLAUDE.md` treat every `BLOCKED` line as a valid stop.

Cardine, which runs on Meridian 1.4.0, hit this stop in three of 22 tasks:
009, 019, and 021. Fix it in 1.4.1 as a blocking defect, without changing
any template, so that 1.4.1 stays a CLI-only release.

## Acceptance Criteria

- [x] When `dirty-worktree` is the only error, `meridian worktree check`
  exits 0, prints no `BLOCKED` line, and writes nothing. Its report says
  `status: ready-dirty`, `next_action: inspect-dirty`, and the changed and
  untracked path counts. Any other error, alone or together with
  `dirty-worktree`, still stops with `BLOCKED WRONG_WORKTREE`.
- [x] A fresh start stays protected without the check:
  - `worktree prepare` without `--resume` still refuses an existing dirty
    worktree;
  - `execution start` without `--resume` still refuses a dirty worktree,
    except for its existing repeated-start case.

  Tests prove both.
- [x] A test runs the whole dirty Resume, `prepare --resume`, `check`, and
  `execution start --resume`, with exit 0 at every step and no `BLOCKED`
  line.
- [x] `test_resume_accepts_a_dirty_worktree_and_changes_nothing` in
  `tests/test_task_worktree_isolation.py` keeps its `inspect_task_worktree`
  assertions, and adds the CLI exit 0 case.
- [x] No file under `templates/`, `migrations/`, or this repository's managed
  copies changes. The managed text already allows this state.
- [x] `changelog.d/232.md` describes the fix.
- [x] Every command under Validation passes.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `worktree check` handler, `inspect_task_worktree`, `_execution_worktree`. |
| `tests/test_task_worktree_isolation.py`, `tests/test_execution_boundaries.py` | Resume tests. |
| `changelog.d/232.md` | Release note. |

## Technical Context

- The `worktree check` handler raises `stop_error` whenever
  `inspect_task_worktree` is not ready, with no case for `dirty-worktree`.
- `_execution_worktree` already accepts `errors == ["dirty-worktree"]` on
  `--resume`.
- Cardine task 028 fixes the same defect with an explicit `check --resume`
  flag and new managed text. Meridian 1.4.1 must not change templates, so it
  relies on the existing `prepare` and `execution start` gates for fresh
  starts.

## Out of scope

Template text, migrations, and the `check --resume` flag.

## Dependencies

- **Depends on**: none
- **Blocks**: 234

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`
