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
- Preparation: from the temporary repository's primary checkout, `meridian
  worktree prepare 056` created the repository-qualified worktree
  `/private/tmp/meridian-task056-probe.J8d9Gz/worktrees/local/repositories/project-6316bc4c7e1a/task-056`.
- Launch: authenticated non-interactive Claude was started with its process
  working directory set to that exact existing worktree, without `--worktree`,
  with permission prompts disabled, and with only bounded `pwd` and branch
  inspection tools offered.
- Result: session `8a0e37e4-9ee1-4e5c-b632-cc739c2b3bff` completed an API turn
  and reported the exact prepared path and branch `task-056`, with no permission
  denials. A subsequent `meridian worktree check 056` returned `ready`, a clean
  tree, matching effective and canonical paths, and no errors.
- Isolation: Git worktree enumeration after the Claude turn contained exactly
  the primary checkout and the prepared Meridian worktree. No
  `.claude/worktrees` directory or other registered substitute checkout
  appeared. Verified Meridian cleanup then removed the prepared worktree and
  its merged-equivalent local branch.
- Classification: `VERIFIED`. A fresh authenticated Claude worker can attach to
  the existing Meridian-prepared directory without creating a second checkout.
