# Task 149 — Warn at upgrade when a markerless managed copy keeps local edits

> **ID**: `149`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Fusa upgrade from 1.2.4 to 1.2.7, 2026-10-04

## Objective

Since 1.2.7, `meridian audit` reports `FAIL managed-copy-digest` for a markerless
managed copy whose content differs from the digest `meridian upgrade` recorded
(task 146). `upgrade` still three-way merges such a file and, when the merge is
clean, keeps the project's edits and records the template digest. In Fusa,
`docs/OPERATOR_PROMPTS.md` had been edited before the upgrade; the plan showed an
ordinary `MERGE`, the apply succeeded, and the first audit afterwards failed. The
developer learns about the problem only after applying. Make the upgrade plan
report it before anything is written.

## Acceptance Criteria

- [ ] For a markerless managed copy (a file with no capability markers that the
  digest audit checks), when the local file differs from its installed baseline,
  `upgrade --check` and `--apply` print a distinct plan row (for example
  `EDITED-COPY`) naming the file, stating that the audit will fail while local
  edits remain, and naming the remedy: restore the released text and keep
  project content in the project's own files.
- [ ] The row does not change what `--apply` writes today: a clean merge is still
  applied and a conflicting one is still a `CONFLICT`. The summary line counts
  these rows separately from conflicts, and `--apply` exits as it does today.
- [ ] Files with capability markers, and files excluded from the digest audit,
  never produce the row; an unedited markerless copy keeps its current
  `REPLACE` or `KEEP` row.
- [ ] The rule that decides "markerless managed copy checked by the audit" is the
  same function the audit uses, not a second list.
- [ ] Tests cover: an edited markerless copy with a clean merge (row shown, file
  merged); an edited one that conflicts (still `CONFLICT`); an unedited copy (no
  row); a marker-bearing file with local edits (no row); and the audit result
  after apply matching the warning.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change and needs no migration.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Upgrade planning rows and summary; the audit's managed-copy digest selection. |
| `tests/` | Upgrade plan and audit tests. |

## Technical Context

- Observed on 2026-10-04 in Fusa: after `upgrade --apply` from 1.2.4,
  `meridian audit` reported `FAIL managed-copy-digest — docs/OPERATOR_PROMPTS.md`;
  restoring `.meridian/baselines/1.2.7/docs/OPERATOR_PROMPTS.md` cleared it.
- Palimpsest hit the same file as a `CONFLICT` and was fixed by hand the same day.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Letting a project declare a managed non-normative file as its own (deferred by
the developer), changing which files the audit checks, and changing merge
behavior.

## Dependencies

- **Depends on**: —
- **Blocks**: none
