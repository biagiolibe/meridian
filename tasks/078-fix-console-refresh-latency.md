# Task 078 — Remove the console refresh latency introduced by effective-state reads

> **ID**: `078`
> **Category**: Developer tooling
> **Priority**: 🔴 P1
> **Assigned to**: unassigned
> **Session**: Developer report that the console became very slow after Task 076

## Objective

Make the project console responsive again. Task 076 resolves each open task's
identity through the shared resolver on every refresh. Profiling this repository
with four open tasks showed a snapshot taking about 5.5 seconds, of which about
98% was `resolve_task_identity` spawning roughly 77 `git` subprocesses per task
(`git check-ref-format` in `_identity_derivations`). The refresh runs in the same
loop that reads keys, so input is blocked for most of each cycle.

## Acceptance Criteria

- [ ] On this repository's current queue, `load_snapshot` completes in under
  0.5 seconds on a warm run, measured by a recorded command, with the
  subprocess count per task bounded and stated in the handoff.
- [ ] The cause of the repeated `check-ref-format` calls is identified and
  recorded in the handoff before the fix is chosen.
- [ ] Branch names and task identity keep coming from the shared resolver; the
  console does not reimplement `milestone` or `opaque` derivation. Results for
  the same ID are identical to those before the change.
- [ ] A task identity is resolved at most once per task per console process
  unless the identity declaration changes.
- [ ] A refresh no longer blocks key handling: the interface keeps responding
  while a snapshot loads, and a finished snapshot replaces the previous one
  without partial or mixed state.
- [ ] A slow or failed refresh keeps the last good snapshot visible and marks it
  stale with the error, as today; no overlapping refreshes run concurrently.
- [ ] Any change to `resolve_task_identity` or `_identity_derivations` keeps the
  worktree lifecycle commands' behavior and tests unchanged.
- [ ] A regression test fails when per-task subprocess work grows with the number
  of known tasks.
- [ ] `meridian console`, `--project`, and the refresh interval are unchanged.

## Relevant Files and Context

- `scripts/project_console.py`: `_branch_facts`, `load_snapshot`,
  `ConsoleState.refresh`, and the polling in `run_terminal`.
- `scripts/meridian.py`: `resolve_task_identity` and `_identity_derivations`,
  shared with the worktree lifecycle commands.
- Measured evidence: 318 subprocess calls, 5.7 s for one snapshot of four open
  tasks; individual `git` calls cost about 18 ms each.
- Task 076 introduced the per-task resolver call so that `milestone` identity
  projects resolve their branches correctly. That behavior must be preserved.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Before and after timing and subprocess counts for `load_snapshot` on this
  repository, recorded in the handoff.
- Interactive PTY smoke check that keys remain responsive during a refresh.

## Out of scope

Launching any agent or process (Task 077), changes to workflow documents or
lifecycle semantics, and a new caching layer that persists across processes.

## Dependencies

- **Depends on**: 076
- **Blocks**: 077
