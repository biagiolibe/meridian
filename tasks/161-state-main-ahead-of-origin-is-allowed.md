# Task 161 — State that a local `main` ahead of `origin/main` does not block integration

> **ID**: `161`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 160 integration stopped by an agent, 2026-10-04

## Objective

An agent closing task 160 stopped with `BLOCKED MAIN_BEHIND_ORIGIN` because the
primary checkout was at `ceda209` while `origin/main` was at `90c4e14`. That is
a local `main` one commit *ahead* of `origin/main`, a state that
`meridian worktree integrate stage` accepts: its check
(`scripts/meridian.py` ~1783) raises `MAIN_BEHIND_ORIGIN` only when local `main`
is an ancestor of the fetched `origin/main` and the two differ, that is, only
when `main` is behind. The agent stopped on its own reading of the documents,
which say the primary must be "at `origin/main`" (managed block in
`PROJECT_WORKFLOW.md` and the Lean router copies) and "`main` equal to
`origin/main`" (`docs/TASK_CLOSURE_DESIGN.md`, C6). The text is stricter than
the behaviour, so a careful agent refuses a state the tool allows, and the stop
code it reports names a condition that did not occur.

State the real rule in the managed text and make the real block self-explanatory.

## Acceptance Criteria

- [ ] The managed sentence "stage from a clean primary checkout at
  `origin/main`" is replaced, in every template that carries it, by wording
  that says: local `main` equals `origin/main`, or is ahead of it with commits
  not yet pushed (they are pushed with the integration); `main` behind the
  fetched `origin/main` is `MAIN_BEHIND_ORIGIN`. The same change is made in this
  repository's own copies. The capability marker version of the affected block
  is bumped as the marker rules require.
- [ ] `docs/TASK_CLOSURE_DESIGN.md` C6 and `docs/WORKTREE_LIFECYCLE.md` state the
  same rule; the historical design text is changed only where it contradicts the
  behaviour, with a note that the rule was clarified.
- [ ] A test proves that `integrate stage` succeeds when local `main` is ahead of
  a fetched `origin/main` (one unpushed commit) and still fails with
  `MAIN_BEHIND_ORIGIN` when `main` is behind, as the existing test
  (`test_integrate_stage_blocks_when_fetched_origin_main_is_ahead`) does.
- [ ] The `MAIN_BEHIND_ORIGIN` message names the local and the fetched
  `origin/main` commits and states "local main is behind"; it is not raised for
  an ahead or equal `main`.
- [ ] `meridian worktree closure-status` continues to report `PUSH_PENDING` when
  `main` is ahead after finalization; a test or the existing one covers it.
- [ ] A migration whose `to` is the next release delivers the changed managed
  block to adopted projects, using the existing mechanism for a capability
  version bump; `upgrade --check` on copies of the Palimpsest and Fusa manifests
  shows the update and no `BLOCKED`, recorded in the handoff.
- [ ] `VERSION`, `.claude-plugin/plugin.json`, and the release ledger are bumped
  by this task only if no earlier unreleased task has already done so for the
  same release; nothing is tagged or published.
- [ ] One changelog fragment states the clarification under `Documentation` and
  the message change under `Changed`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | The behind check and message (~1783–1797). |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` (~234), `templates/workflows/lean-delivery/{PROJECT_WORKFLOW,AGENTS,CLAUDE}.md` (~73–145), `PROJECT_WORKFLOW.md` (~109) | The managed `git-workflow` block text. |
| `docs/TASK_CLOSURE_DESIGN.md`, `docs/WORKTREE_LIFECYCLE.md` | C6 and the lifecycle text. |
| `tests/test_meridian_cli.py` | Existing behind test (~7582) and the new ahead test. |
| `migrations/` | New migration for the block text. |

## Technical Context

- The stop-code list `PRIMARY_DIRTY`, `MAIN_BEHIND_ORIGIN`, `LEASE_HELD`, … is
  repeated in the managed block and in `tests/test_project_console.py` (~963);
  the code names stay unchanged.
- Pushing an ahead `main` together with the integration is the existing C9 step
  (`PUSH_PENDING`); only unpushed governance commits (task registrations) are
  expected to be ahead.
- Not verified: whether the agent ran `integrate stage` before stopping. It
  reported the code but the code path above cannot raise it for an ahead `main`.
- Changing the managed block makes the release template-changing; it shares the
  release with task 159 if both land before publication.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Renaming `MAIN_BEHIND_ORIGIN`, requiring a push before staging, and changing
the push race handling (`PUSH_REJECTED`).

## Dependencies

- **Depends on**: —
- **Blocks**: none
