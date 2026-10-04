# Task 158 — Migrate legacy budget state only at upgrade, never from a read

> **ID**: `158`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Palimpsest integration blocked by `PRIMARY_DIRTY`, 2026-10-04

## Objective

Task 152 moved mutable budget state to `<git-common-dir>/meridian-budget.json`.
`migrate_budget_state` (`scripts/meridian.py` ~7679) moves a legacy tracked
`.meridian/budget.json` there and runs `git rm --cached` on it, which stages a
deletion in the primary checkout. It is called from `load_budget_state` (~7700),
so any command that only reads budget state (hook briefings, `task identity`
diagnostics, budget reads) mutates the primary index. The next integration then
stops with `PRIMARY_DIRTY` on `D  .meridian/budget.json`, a change the developer
did not make and whose source is not visible. The audit message and the
changelog both say the migration happens "on the next budget write", so the
behaviour also contradicts the documentation.

Make the migration an explicit, announced step that happens once, and keep every
read free of side effects.

## Acceptance Criteria

- [ ] `load_budget_state` and every other read-only path never move, delete, or
  unstage a file and never run `git rm`. When only the legacy tracked file exists
  they return its content.
- [ ] `write_budget_state` performs the migration (move the content into the
  git-common-dir state, remove the legacy file from the index) only when it is
  actually writing, as documented, and reports once on stderr that
  `.meridian/budget.json` was removed from the index and the deletion must be
  committed.
- [ ] `meridian upgrade --apply` performs the same migration for a project that
  tracks `.meridian/budget.json`, lists it in its result, and states the commit
  to make; `upgrade --check` shows a plan row for it and changes nothing.
- [ ] `meridian worktree integrate stage` still refuses a dirty primary, and its
  `PRIMARY_DIRTY` message names the staged or modified paths (counts and path
  list, bounded) so the cause is visible. When the only dirty path is
  `.meridian/budget.json`, the message states that it is the legacy budget file
  and that committing its deletion is the remedy.
- [ ] Task-worktree commands never write a tracked `.meridian/budget.json` into a
  task branch: a test proves that running budget commands from a task worktree
  leaves its index and tree unchanged apart from the common-dir state.
- [ ] Tests on fixtures prove: a read leaves `git status` clean; a write migrates
  once and a second write changes nothing further; upgrade migrates and reports;
  the PRIMARY_DIRTY message; and the task-worktree case.
- [ ] One changelog fragment states the fix under `Fixed` and, if upgrade now
  stages a deletion, under `Upgrade notes`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `migrate_budget_state`, `load_budget_state`, `write_budget_state`, `tracked_budget_state` (~7660–7715); audit advisory (~5986); upgrade apply path; `integrate stage` dirty-primary check. |
| `tests/test_meridian_cli.py` | Budget and integration fixtures. |
| `docs/WORKTREE_LIFECYCLE.md` | `PRIMARY_DIRTY` description, if it names causes. |

## Technical Context

- Observed in Palimpsest on 2026-10-04: after a prior commit
  (`21253d9` "remove dirty meridian budget") deleted the file, a later task again
  stopped with a staged `D  .meridian/budget.json`. `.git/meridian-budget.json`
  held the state (modified the same day).
- Palimpsest commit `72e176e` had committed a *modified* tracked `budget.json`
  "so the primary checkout is clean", i.e. an older CLI still wrote the tracked
  file. Hypothesis, not verified: task branches or worktrees created before the
  upgrade, or an older CLI or hook, keep writing or re-adding the tracked file,
  and the newer CLI then stages its deletion. The test for task-worktree writes
  covers the part reproducible in this repository; confirm against the Palimpsest
  history before closing.
- Decision recorded here: no automatic commit of the deletion by Meridian; the
  developer or the closing agent commits it, after being told once.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing where budget state lives, committing on the developer's behalf, and
reworking the integration lease.

## Dependencies

- **Depends on**: —
- **Blocks**: none
