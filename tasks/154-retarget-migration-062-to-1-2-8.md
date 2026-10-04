# Task 154 — Retarget migration 062 to 1.2.8 and reject same-version migrations

> **ID**: `154`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Release readiness check after task 152, 2026-10-04

## Objective

Task 152 changed managed template text and added
`migrations/062-primary-project-declaration-and-review-authority.json` with
`from: 1.2.7` and `to: 1.2.7`, but left `VERSION`, `.claude-plugin/plugin.json`,
and the release ledger at the already published 1.2.7. As a result two different
template baselines carry the number 1.2.7: `meridian upgrade --check` on a 1.2.7
project (Fusa) merges `PROJECT_WORKFLOW.md` and `docs/workflows/REVIEW.md` but
lists no `MIGRATION 062` row and reports `1.2.7 -> 1.2.7`, so the manifest would
record 1.2.7 for content that differs from the 1.2.7 release.
`CONTRIBUTING.md` requires the task that adds a migration to bump the version
records; `scripts/check_repository.py` only rejects a migration ahead of
`VERSION`, so the error passed. Retarget the migration to the next release and
make the check catch this class of error.

## Acceptance Criteria

- [ ] Migration 062 declares `from: 1.2.7` and `to: 1.2.8`; its id, content,
  capability versions, and managed paths are otherwise unchanged.
- [ ] `VERSION` and `.claude-plugin/plugin.json` are `1.2.8`, and
  `releases/1.2.8.json` lists migration `062-primary-project-declaration-and-review-authority`
  with `baselineChanged: true`, `workflowBaselineVersion: 1.2.8`, `protocolVersion`
  unchanged, and `gitTag: v1.2.8`. No tag is created and nothing is published.
- [ ] `meridian upgrade --check` on a project at 1.2.7 reports `1.2.7 -> 1.2.8`
  and a `MIGRATION 062-…` row; a test proves it on a fixture.
- [ ] `scripts/check_repository.py` fails, with a message naming the file, when a
  migration's `from` equals its `to`, and when a migration targets a version that
  already has a `v<version>` tag while its id is not part of that version's
  release ledger (the existing contiguity and not-ahead rules stay). Tests cover
  both failures and the passing case.
- [ ] Changelog fragments already present for 148–153 are kept unchanged; one
  fragment for this task states that the 1.2.8 release is template-changing
  because of migration 062.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `migrations/062-primary-project-declaration-and-review-authority.json` | Target version. |
| `VERSION`, `.claude-plugin/plugin.json`, `releases/1.2.8.json` | Version records. |
| `scripts/check_repository.py` | `check_migrations` (~line 346). |
| `tests/` | Repository-check and upgrade-plan tests. |

## Technical Context

- Observed on 2026-10-04: `meridian upgrade --project ../fusa --check` printed
  `Meridian 1.2.7 -> 1.2.7` with `MERGE` rows for the two files of migration 062
  and no migration row; Fusa's `appliedMigrations` ends at `061-governed-phase-reads`.
- Release preparation for a template-changing release does not use
  `release.py prepare`; publishing stays the developer's action.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Publishing 1.2.8, changing migration 062's content, and changing tasks 150 or 153.

## Dependencies

- **Depends on**: —
- **Blocks**: none
