# Task 187 — Stabilize the `closure-status` non-mutation test against Git maintenance

> **ID**: `187`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: CI failure after Task 186, 2026-10-07
> **Origin**: friction

## Objective

Make the `closure-status` non-mutation regression test reliably distinguish
changes caused by `closure-status` from transient Git housekeeping in its
fixture. GitHub Actions run `37636426181` failed after Task 186 was integrated:
the test's snapshot contained `.git/objects/maintenance.lock` before the C5
status query and not afterward. The completed Task 186 remains closed.

## Acceptance Criteria

- [x] Determine and document which operation creates and removes the transient
  maintenance lock in the test fixture. Do not infer that `closure-status`
  created it merely because the snapshots differ.
- [x] The test controls or waits for fixture-owned Git maintenance before
  taking a snapshot, without excluding real repository or worktree mutations
  caused by `closure-status` from the comparison.
- [x] The test still fails when `closure-status` writes a lifecycle journal or
  another persistent file in either checkout. Include a focused negative
  control or equivalent evidence in the handoff.
- [x] Text and JSON status reporting, including C4 and C5, remain covered.
- [x] The focused regression test passes repeatedly under parallel suite load
  or an equivalent Git maintenance stress reproduction; record the command and
  results in the handoff.
- [x] `python3 scripts/check_repository.py` and the full unit suite pass. Add
  a changelog fragment if a shipped file changes under `CONTRIBUTING.md`.

## Relevant Files

| File | Role |
|------|------|
| `tests/test_meridian_cli.py` | Fixture Git operations and non-mutation snapshots. |
| `scripts/meridian.py` | Read-only command behavior, if diagnosis reveals a runtime write. |
| `tasks/handoffs/186.md` | Previous validation evidence. |

## Technical Context

- **Current behavior**: the test hashes every file under the fixture's primary
  checkout and task worktree. Git commands that set up C5 may trigger
  background maintenance, whose transient lock can disappear between the
  snapshots.
- **Desired behavior**: fixture-owned asynchronous work cannot invalidate the
  snapshot assertion, while writes by the status command remain detectable.
- **Evidence**: CI run `37636426181`, shard 2/4, reports the lock only on the
  expected (before) side of the C5 assertion. Task 186 removed
  `closure-status` from `JOURNALED_WORKTREE_COMMANDS`; its remaining
  `journal.observe` and `journal.stopped` calls update in-memory fields.

## Constraints and Considerations

- Do not remove the lock or all of `.git` from the snapshot just to make the
  test pass.
- Do not change `closure-status` behavior without evidence of a runtime bug.
- Keep Task 186's completion and archive records intact.

## Dependencies

- **Depends on**: 186 (complete)
- **Blocks**: none
