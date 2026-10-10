# Task 195 — Count cleanup-pending tasks as done in the console

> **ID**: `195`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: GitHub issue triage, 2026-10-10

## Objective

Fix [issue #7](https://github.com/biagiolibe/meridian/issues/7): an integrated
and pushed task remains `Closing` indefinitely while a leftover canonical
worktree exists. Treat cleanup-only C10 as completed, with a visible cleanup
hint and its resume command.

## Acceptance Criteria

- [x] A terminal queue row with a registered canonical worktree and C10 cleanup
  resume is counted as done and excluded from the `Closing` filter.
- [x] The task's cleanup-pending hint and exact resume command remain accessible
  in the console detail view without pretending the task is active work.
- [x] C6, C7, and C9 retain their current Closing behavior. Missing or unreadable
  lifecycle state is not treated as proof of completion.
- [x] Tests cover both workflow modes, active and archived terminal rows,
  cleanup-only C10, C10 without a resume, and the preceding Closing phases.
- [x] Done rows without registered worktrees incur no additional subprocess
  cost. Console refresh remains within its existing latency constraints.
- [x] Interactive and `--once` summaries agree. The console stays read-only
  and never performs cleanup itself.
- [x] Document the display distinction and add a changelog fragment.
- [x] Repository checks, the full unit suite, and `git diff --check` pass.

## Relevant Files

`scripts/project_console.py`, `tests/test_project_console.py`, `README.md`,
`changelog.d/`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Automatic worktree cleanup, changing lifecycle completion rules, or repairing
historical worktrees.

## Dependencies

- **Depends on**: 124, 186
- **Blocks**: none

## Completion

Implemented at `78b16cd16217aef25ed10c044f60108f047f1b23`. Required repository
checks, the full 898-test parallel suite (no failures, errors, or skips), and
`git diff --check` passed. See [completion report](../handoffs/195.md).
