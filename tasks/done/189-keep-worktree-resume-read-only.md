# Task 189 — Keep worktree resume independent of Git metadata writes

> **ID**: `189`
> **Category**: Bug fix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 183 resume access failure, 2026-10-08
> **Origin**: friction

## Objective

Make `meridian worktree prepare <task-id> --resume` honor its documented
non-mutating lifecycle contract. A Codex worker that can read the primary
checkout's Git metadata and its existing task worktree must not need write
access to `.git/meridian-worktrees` merely to resume the task.

## Acceptance Criteria

- [x] Resuming an existing clean or dirty canonical worktree that has a
  matching lifecycle state file returns the same branch, path, base commit,
  `started_at`, and resume and dirty information as today. It does not create,
  replace, or change the lifecycle state file, Git references, the index, or
  the worktree contents.
- [x] A resume succeeds when the existing lifecycle state and the shared Git
  metadata are readable but lifecycle-state writes are denied. A focused
  regression test detects any attempted temporary-file creation or atomic
  rewrite of the state file, for example by denying writes to the state
  directory or by failing `_write_json_atomic`. It does not rely only on the
  file contents being unchanged.
- [x] Mismatched lifecycle state (a state file naming another worktree or
  branch) stops with a registered, actionable stop code instead of the current
  generic error. The detail names the state file and the expected and found
  values. Existing branch and worktree mismatch protections and integration
  lease protections stay intact.
- [x] Missing lifecycle state on resume is neither repaired nor a dead end. A
  dirty worktree has no other entry point, because `prepare` without
  `--resume` refuses a dirty worktree. In that case the resume:
  - succeeds without writing anything;
  - derives the branch, path, and dirty information from Git;
  - reports `base_commit` from `git merge-base main <branch>` with
    `base_commit_source: "derived"` and no `started_at`;
  - adds `state: "missing"` and a `state_repair` command telling the worker
    to run `meridian worktree prepare <task-id> --project <primary-checkout>
    --format json` once the worktree is clean.

  The existing state repair done by `prepare` without `--resume` on a clean
  worktree is unchanged. A test covers a dirty worktree with missing state,
  from resume through the later repair.
- [x] The best-effort lifecycle journal entry for a resume is kept, and a
  failed journal write never turns a valid resume into a failure. The managed
  `bounded-worktree-lifecycle` text is not changed, so no marker bump or
  migration is needed. `docs/WORKTREE_LIFECYCLE.md` states that the
  non-mutation promise covers lifecycle state, Git, and the worktree, and that
  the diagnostic journal is the one explicit exception.
- [x] The task records whether any other step that runs on the worker side
  writes under the primary checkout's `.git/` directory (for example
  `meridian-worktrees/` or the journal). With closure now driven by `meridian
  worktree advance` from the primary checkout, none is expected. Any
  exception found is listed in the handoff as a proposed follow-up and is not
  fixed here.
- [x] One changelog fragment states the fix under `Fixed`, per
  `CONTRIBUTING.md`.
- [x] Focused worktree and CLI regression tests, the repository checks, and
  the full parallel test suite pass. The exact commands and results are
  recorded in the handoff.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `prepare_task_worktree`, atomic state write, stop registry helper, and best-effort lifecycle journal. |
| `capabilities/stop-codes-v1.json` | Code for the mismatched-state stop. |
| `tests/test_task_worktree_isolation.py` | Direct resume and non-mutation regression coverage. |
| `tests/test_meridian_cli.py` | CLI resume and journal behavior. |
| `docs/WORKTREE_LIFECYCLE.md` | Journal exception to the resume non-mutation promise. |

## Technical Context

- `prepare_task_worktree(..., resume=True)` currently calls
  `_write_json_atomic(state_path, state)` even when it only reads an existing
  canonical worktree. That call creates a temporary file beside
  `.git/meridian-worktrees/<task-id>.json` before replacing the state file.
- Task 183 reported `BLOCKED OS_ACCESS_FAILED` while creating
  `.git/meridian-worktrees/.183.json.<tmp>` in a restricted Codex session.
  Ownership and ordinary Unix mode bits alone did not explain the denial.
  Task 183 has since been cancelled and archived, so it is evidence only.
- The direct tests compare state-file contents before and after resume, which
  does not detect an identical atomic rewrite. The CLI journal tests expect a
  resume entry in the shared best-effort journal.
- The managed copies of the resume rule are in `PROJECT_WORKFLOW.md` and
  `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md`
  (`bounded-worktree-lifecycle`). This task leaves them unchanged.
- `docs/ADR_STOPS_AND_DENIALS.md` requires every stop to be satisfiable by the
  actor it blocks. The missing-state criterion above exists for that reason.

## Constraints and Considerations

- Do not widen host permissions, change ACLs, or bypass the sandbox to make a
  read-only operation pass.
- Preserve normal non-resume `prepare` behavior and existing safety checks.
- Treat journal behavior separately from the lifecycle state write.

## Validation

- `python3 -m unittest discover -s tests -p 'test_task_worktree_isolation.py'`
- Focused CLI resume and journal tests from `tests/test_meridian_cli.py`.
- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Dependencies

- **Depends on**: none
- **Blocks**: none
