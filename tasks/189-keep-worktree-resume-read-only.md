# Task 189 — Keep worktree resume independent of Git metadata writes

> **ID**: `189`
> **Category**: Bug fix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 183 resume access failure, 2026-10-08
> **Origin**: maintenance

## Objective

Make `meridian worktree prepare <task-id> --resume` honor its documented
non-mutating lifecycle contract. A Codex worker that can read the primary
checkout's Git metadata and its existing task worktree must not need write
access to `.git/meridian-worktrees` merely to resume the task.

## Acceptance Criteria

- [ ] Resuming an existing clean or dirty canonical worktree returns the same
  branch, path, base commit, `started_at`, and resume/dirty information without
  creating, replacing, or changing its lifecycle state file, Git references,
  index, or worktree contents.
- [ ] A resume succeeds when the existing lifecycle state and shared Git
  metadata are readable but lifecycle-state writes are denied. Add a focused
  regression test that detects an attempted temporary-file creation or atomic
  rewrite; do not depend only on unchanged file contents.
- [ ] Missing or mismatched lifecycle state is rejected with a coded,
  actionable stop rather than silently repaired during resume. Existing
  branch/worktree mismatch and integration-lease protections remain intact.
- [ ] Reconcile the documented "never creates or changes anything" promise
  with the best-effort lifecycle journal entry. Journal failure must not turn
  an otherwise valid resume into a failure; document any diagnostic-journal
  exception to the non-mutation contract explicitly.
- [ ] Run focused worktree and CLI regression tests, repository checks, and
  the full parallel test suite. Record the exact commands and results.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `prepare_task_worktree`, atomic state write, and best-effort lifecycle journal. |
| `tests/test_task_worktree_isolation.py` | Direct resume and non-mutation regression coverage. |
| `tests/test_meridian_cli.py` | CLI resume and journal behavior. |
| `PROJECT_WORKFLOW.md` | Self-hosting resume contract, if clarification is needed. |
| `templates/base/PROJECT_WORKFLOW.md` | Managed workflow copy, if its contract changes. |

## Technical Context

- `prepare_task_worktree(..., resume=True)` currently calls
  `_write_json_atomic(state_path, state)` even when it only reads an existing
  canonical worktree. That call creates a temporary file beside
  `.git/meridian-worktrees/<task-id>.json` before replacing the state file.
- Task 183 reported `BLOCKED OS_ACCESS_FAILED` while creating
  `.git/meridian-worktrees/.183.json.<tmp>` in a restricted Codex session.
  Ownership and ordinary Unix mode bits alone did not explain the denial.
- Current direct tests compare state-file contents before and after resume,
  which does not detect an identical atomic rewrite. CLI journal tests also
  expect a resume entry in the shared best-effort journal.

## Constraints and Considerations

- Do not alter Task 183's branch, worktree, measurements, or task record.
- Do not widen host permissions, change ACLs, or bypass the sandbox to make a
  read-only operation pass.
- Preserve normal non-resume `prepare` behavior and existing safety checks.
- Treat journal behavior separately from the lifecycle state write; the
  diagnostic journal may remain best-effort if the documented contract says so.

## Validation

- `python3 -m unittest discover -s tests -p 'test_task_worktree_isolation.py'`
- Focused CLI resume and journal tests from `tests/test_meridian_cli.py`.
- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Dependencies

- **Depends on**: none
- **Blocks**: none; Task 183 has an immediate coordinator-side resume workaround.
