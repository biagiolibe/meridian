# Task 184 — Bring this repository's Meridian installation to the current release and keep it upgradable

> **ID**: `184`
> **Category**: Refactor
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 181 unblock, 2026-10-06
> **Origin**: friction

## Objective

This repository installs Meridian on itself (migration
`052-install-meridian-self-hosting-surfaces`), but its
`.meridian/manifest.json` still records `frameworkVersion` and
`workflowBaselineVersion` `1.1.49` while `VERSION` is `1.2.11`. Since then,
tasks changed the managed copies by hand and refreshed their digests with
`check_repository.py --write-managed-digests`, as `CONTRIBUTING.md` allows.
The baseline snapshots never moved, so `meridian upgrade --check --project .`
on 2026-10-06 planned migrations 053 to 064 and stopped with
`BLOCKED UPGRADE_BLOCKED: 4 conflict(s)` on `PROJECT_WORKFLOW.md`,
`AGENTS.md`, `CLAUDE.md`, and `docs/CONTEXT_BUDGET_POLICY.md`. It also planned
`ADOPT-REPLACE docs/WORKTREE_LIFECYCLE.md`, which would overwrite this
repository's framework reference document with the template copy.

Tasks 176 and 181 each had to amend a criterion that required updating a
managed copy "through `meridian upgrade`". Every later task that changes a
managed template will hit the same stop.

Resolve the drift once, record the current release in the manifest, and make
the self-hosting procedure keep the manifest current from now on.

## Acceptance Criteria

- [x] `meridian upgrade --project . --check` reports no `CONFLICT`, no
  `BLOCKED`, and no `ADOPT-REPLACE` that would discard this repository's
  content. Each of the four conflicts is resolved in this task, keeping this
  repository's intended text; the handoff lists, per file, which side was
  kept and why.
- [x] `docs/WORKTREE_LIFECYCLE.md` keeps every section it has today (the
  lifecycle journal, `report flow`, the stop audit, `advance`). Either it is
  no longer treated as a managed copy of the template document, or the
  template and this file are reconciled; the handoff states which and why.
- [x] After `meridian upgrade --project . --apply`, `.meridian/manifest.json`
  records `frameworkVersion` equal to `VERSION`, `workflowBaselineVersion`
  equal to the newest migration's `to` that is not ahead of `VERSION`, the
  applied migrations through it, and baseline snapshots for that version.
  The manifest and snapshots are written only by `meridian upgrade`, never by
  hand.
- [x] A second `meridian upgrade --project . --check` reports no pending
  change.
- [x] `CONTRIBUTING.md` replaces the hand-edit-and-refresh-digests procedure
  for managed copies with one that keeps the manifest current: a task that
  changes a managed template updates this repository's copy through
  `meridian upgrade --apply` in the same task, or the procedure states the
  exact alternative and when it applies. `--write-managed-digests` remains
  only for the cases the procedure names.
- [x] `python3 scripts/check_repository.py` fails, with a message naming the
  fix, when this repository's manifest `workflowBaselineVersion` is older than
  the newest migration's `to` that is not ahead of `VERSION`. A test covers
  the failing and the passing case.
- [x] No template under `templates/`, no migration, and no capability marker
  version changes. This task changes only this repository's installation,
  its check, and its documentation, so it ships no migration.
- [x] One changelog fragment is added per `CONTRIBUTING.md`, only if a shipped
  file changes; otherwise the handoff states that none is needed.
- [x] `python3 scripts/check_repository.py` and the unit tests pass, and
  `meridian audit --project . --mode lean-delivery --ci-profile
  meridian-self-hosting` passes as it does in CI.

## Relevant Files

| File | Role |
|------|------|
| `.meridian/manifest.json`, `.meridian/baselines/` | Self-hosting installation; written by `meridian upgrade`. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CONTEXT_BUDGET_POLICY.md` | The four conflicting managed copies. |
| `docs/WORKTREE_LIFECYCLE.md` | Framework reference document planned for `ADOPT-REPLACE`. |
| `templates/workflows/lean-delivery/` | Read only: the incoming side of each merge. |
| `migrations/052-install-meridian-self-hosting-surfaces.json` | How self-hosting was installed; read only. |
| `scripts/check_repository.py` | Managed-copy checks and the new baseline-lag check. |
| `CONTRIBUTING.md` | Self-hosting procedure for managed copies. |
| `.github/workflows/validate.yml` | CI audit command; read only. |

## Technical Context

- **Current behavior**: the manifest says 1.1.49, the copies are newer, and
  `upgrade` cannot run here. Tasks work around it by hand.
- **Desired behavior**: `upgrade --check` is clean, the manifest names the
  current release, and a check keeps it from lagging again.
- Task 176's handoff (`tasks/handoffs/176.md`, `Rule discrepancies`) and task
  181 record the workaround this task retires.
- `--apply` is all-or-nothing: it changes nothing while any conflict remains.

<!-- TODO: add relevant code snippets and file paths -->

## Suggested Implementation

<!-- TODO: add relevant code snippets and file paths -->

## Constraints and Considerations

- Start after task 181 is integrated, so its `.codex/hooks.json` entry is
  part of the installation this task records.
- Do not edit `.meridian/manifest.json` or `.meridian/baselines/` by hand
  (`README.md`, "Framework upgrades").
- Out of scope: changing the upgrade engine's merge behavior, other
  projects' installations, and template text.

## Dependencies

- **Depends on**: 181
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/184-bring-self-hosting-installation-current.md)"$'\n\nExecute this task in the current project.'
```
