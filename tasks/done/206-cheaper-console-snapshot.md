# Task 206 — Make the console snapshot cheaper

> **ID**: `206`
> **Category**: Performance
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: GitHub issue #13 triage, 2026-10-13
> **Origin**: friction

## Objective

Reduce the cost of `load_snapshot`, which the periodic refresh pays on every
cycle. The issue #13 measurements were taken on 2026-10-13 at `4ca3aa1`, warm:

| Project | Snapshot | Main costs |
|---|---|---|
| Meridian | about 2.1 s | `_closing_task`: `closure_status` about 0.8 s and `lifecycle_started_at` about 0.2 s per task, both resolving identity without the console's `IdentityCache`; `git worktree list` runs about 26 times. |
| Consumer project A | about 4 s | `delivery_readiness` for `READY_FOR_REVIEW` rows, 1.5–3.9 s; `_branch_facts` about 2.5 s; about 110 `git` subprocesses. |

## Acceptance Criteria

- [x] `closure_status` and `lifecycle_started_at` accept an already resolved
  task identity. The console passes the one from its `IdentityCache`, and
  their command-line behavior is unchanged.
- [x] `git worktree list --porcelain` runs at most once per snapshot. Its
  result is passed to every consumer that needs it, and a test counts the
  subprocess invocations per snapshot.
- [x] The result of `delivery_readiness` for a task is cached by the task
  worktree `HEAD`, the handoff file's identity (path, size, and modification
  time), and the task's state file identity. An unchanged review-ready task is
  not rechecked on the next refresh, and any change to one of those inputs
  invalidates the entry.
- [x] The snapshot output is identical with and without the caches on the
  existing console fixtures, including the behavior of tasks 195, 196, and
  202.
- [x] The handoff records the warm `load_snapshot` time before and after, on
  Meridian and on a copy of consumer project A, with the same method as the issue.
- [x] One changelog fragment states the change under `Changed`; this is a
  CLI-only change.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | `load_snapshot`, `_closing_task`, `_branch_facts`, `IdentityCache`. |
| `scripts/meridian.py` | `closure_status`, `lifecycle_started_at`, `canonical_project_root`. |
| `tests/test_project_console.py` | Subprocess-count, cache, and output-equality tests. |

## Technical Context

- [Issue #13](https://github.com/biagiolibe/meridian/issues/13) has the
  profile data and proposals.
- The Meridian figures are inflated by tasks 082 and 085, which are left in
  the closing state as in issue #7. Check whether their leftovers need
  cleanup, and report it in the handoff without deleting anything.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Launch threading (task 205), changing what the console shows, and removing
leftover worktrees.

## Dependencies

- **Depends on**: 205
- **Blocks**: none
