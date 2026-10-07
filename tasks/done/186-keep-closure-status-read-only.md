# Task 186 — Keep `closure-status` read-only when reporting lifecycle state

> **ID**: `186`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: CI failure review, 2026-10-07
> **Origin**: friction

## Objective

Restore the read-only contract of `meridian worktree closure-status`.

The validation workflow on `main` failed at commit `e5927576` because
`test_closure_status_covers_lifecycle_states_without_mutation` found a changed
maintenance lock after the `WRONG_WORKTREE` (`C4`) status path. The command's
help explicitly promises to report the next closure step without changing
lifecycle state.

## Acceptance Criteria

- [x] `meridian worktree closure-status` does not create or modify a lifecycle
  journal, maintenance lock, repository file, or task worktree file for every
  reported lifecycle state, including `C4` / `WRONG_WORKTREE`, in text and JSON
  output modes.
- [x] The command preserves its current status, stop-code, and resume-command
  reporting semantics.
- [x] A regression test reproduces the former `C4` mutation and proves the
  primary checkout and task worktree remain byte-identical after each
  `closure-status` invocation it covers.
- [x] `python3 scripts/check_repository.py` passes.
- [x] `python3 scripts/run_tests.py --parallel` passes.
- [x] A changelog fragment is added if a shipped file changes, following
  `CONTRIBUTING.md`.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Lifecycle command dispatch and journal observation. |
| `tests/test_meridian_cli.py` | Lifecycle state and non-mutation regression coverage. |
| `changelog.d/` | Release-note fragment when required. |

## Technical Context

- **Current behavior**: `closure-status` is included in
  `JOURNALED_WORKTREE_COMMANDS`. Its observation path can write a maintenance
  lock even when the command reports `WRONG_WORKTREE`.
- **Desired behavior**: status inspection remains observational. Commands that
  are intentionally mutating retain their existing lifecycle-journal behavior.
- **CI evidence**: GitHub Actions run `37624457802`, job `validate`, failed in
  `WorktreeLifecycleCliTest.test_closure_status_covers_lifecycle_states_without_mutation`.

## Suggested Implementation

1. Trace the `closure-status` dispatch and journal-observation path.
2. Exclude read-only status reporting from any write path while preserving its
   output contract.
3. Strengthen the existing snapshot regression coverage for the `C4` case and
   other affected output modes.

## Constraints and Considerations

- Do not weaken the test by excluding the maintenance lock from its snapshot.
- Do not change lifecycle state, queue status, or task records as part of the
  status query.
- Keep the defect separate from Task 185, which improved parallel-test output
  and timing-test reliability.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/186-keep-closure-status-read-only.md)"$'\n\nExecute this task in the current project.'
```
