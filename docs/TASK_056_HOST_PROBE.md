# Task 056 Host Probe Evidence

Date: 2026-09-28

## Codex CLI

- Profile: Codex CLI 0.157.1, project rules loaded explicitly with `codex
  execpolicy check`.
- Source form: the task worktree's `bin/meridian` was first on `PATH`, so the
  canonical executable name remained `meridian` while exercising the pending
  implementation.
- Repository: a temporary local Git repository with primary checkout
  `/private/tmp/meridian-task056-probe.J8d9Gz/project` and configured worktree
  root `/private/tmp/meridian-task056-probe.J8d9Gz/worktrees`.
- Prepare/check: `prepare` created exactly one `task-056` worktree at the
  repository-qualified path; `check` from that directory returned `ready`, a
  clean tree, matching effective/canonical paths, and no errors.
- Policy: actual execpolicy evaluation returned `allow` for the canonical
  `integrate stage`, `integrate finalize`, and `cleanup` invocations. The unit
  decision table covers all seven lifecycle actions plus unmatched unknown and
  incomplete forms.
- Integration: stage returned `REUSE` and candidate tree
  `b69700b5114e79cfee6780b385e8518b1d631053`; validation ran separately as
  `git diff --check`; finalize created merge commit
  `4450537617c15708540f211cec8a6b6137d471b9`; cleanup then removed the
  worktree and merged local branch.
- Approval observation: no command approval was requested during the bounded
  lifecycle probe. Filesystem access, rule decision, Git transition, and the
  lack of a remote/push requirement were observed separately.

## Claude Code

- Profile: Claude Code 2.1.283.
- Launch: non-interactive Claude was started with its process working directory
  set to the exact prepared Meridian worktree, permission prompts disabled, and
  only bounded `pwd` and branch inspection tools offered.
- Result: the client created session
  `9a8d465f-1189-47f3-ab8a-13d6377f5fb2` but returned `Not logged in · Please
  run /login` before an API turn or tool use. Git worktree enumeration before
  launch contained only the primary and prepared worktree; the later successful
  Meridian cleanup proved no substitute checkout was registered.
- Classification: `UNVERIFIED`, not enforced. The executable and existing-
  directory launch path are available, but authentication is an external
  activation precondition. Repeat the probe after Claude login; do not treat
  this result as proof that a usable fresh worker can attach to the prepared
  directory.
