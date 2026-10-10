# Task 194 — Detect and repair stale worktree base records

> **ID**: `194`
> **Category**: Bugfix / Design
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Status**: DONE
> **Session**: GitHub issue triage, 2026-10-10

## Objective

Address [issue #11](https://github.com/biagiolibe/meridian/issues/11): a clean
prepared branch fast-forwarded to revised `main` can retain an obsolete
`base_commit` and attribute main's changes to the task. Define and implement
a supported, narrowly proven recovery instead of requiring manual JSON edits.
Authority: the local worktree lifecycle and `docs/ADR_STOPS_AND_DENIALS.md`.

## Acceptance Criteria

- [x] Reproduce the reported sequence and distinguish it from ordinary main
  advancement after task commits. Merely differing from the current merge base
  must not trigger automatic repair.
- [x] Record the chosen detection and repair contract in lifecycle documentation
  before implementation. Use Git ancestry and clean canonical worktree facts
  to prove the supported commit-less fast-forward case. If a broader repair
  requires unresolved architectural changes, report the concrete decision gap
  rather than silently extending this task.
- [x] `worktree check` remains read-only and identifies a proven stale record
  with a registered actionable code and a supported recovery command.
- [x] The explicit recovery preserves task identity and `started_at`, changes
  only the owned base-record facts, and rejects unrelated branches, dirty or
  mismatched worktrees, task-owned commits, and active integration state.
- [x] Evidence tied to the previous base is not silently reused or rewritten
  as passed; recovery explicitly requires or records renewed evidence.
- [x] Repeated recovery is idempotent. Tests cover the reported sequence,
  rejection cases, normal advanced-main integration, and resume non-mutation.
- [x] Document recovery and add a changelog fragment. Register any new stop
  code and preserve existing command compatibility.
- [x] Repository checks, the full unit suite, and `git diff --check` pass.

## Relevant Files

`scripts/meridian.py`, `tests/test_meridian_cli.py`,
`tests/test_task_worktree_isolation.py`, `capabilities/stop-codes-v1.json`,
`docs/WORKTREE_LIFECYCLE.md`, `changelog.d/`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Git rebase, history rewriting, automatic branch advancement, arbitrary registry
editing, and repair of branches with task-owned commits.

## Dependencies

- **Depends on**: 189
- **Blocks**: none
