# Task 148 — Drop retired markers from project sections carried by a restructure

> **ID**: `148`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Palimpsest upgrade from 1.2.6 to 1.2.7, 2026-10-04

## Objective

A `RESTRUCTURE` upgrade of `docs/CODE_REVIEW_PROMPT.md` installs the standalone
`code-review-prompt` v1 block and carries the project's own level-2 sections after
it (`restructured_text` and `project_sections` in `scripts/meridian.py`). In
Palimpsest the existing `## Project review checklist` section also contained the
three inline markers that migration 061 retires (`ci-verified-validation` v1,
`manual-verification-review-check` v1, `task-worktree-review` v4). The carried
section kept them, so the upgraded file held the new block plus duplicated
retired blocks, and `meridian audit` reported two `FAIL` rows (retired marker
still present) and one `UNVERIFIED` row. The developer had to delete them by hand.
Make a restructure remove retired marker blocks from the sections it carries.

## Acceptance Criteria

- [ ] When a restructure carries a project section, every complete marker block
  of a capability/version that the restructuring migration retires is removed from
  that section, together with the blank lines it leaves; all other project text in
  the section is kept byte for byte, in order.
- [ ] A marker block that is not retired by the migration, or a project section
  without such blocks, is carried unchanged.
- [ ] A retired marker block whose content differs from its released text is not
  dropped silently: the plan row reports it, and the pre-restructure backup still
  holds the original file.
- [ ] After `upgrade --apply`, `meridian audit` reports no retired-marker `FAIL`
  for the restructured file.
- [ ] Tests cover: a carried section containing the three retired inline markers
  (the Palimpsest shape) becoming checklist-only; a section without markers
  unchanged; a non-retired marker kept; an edited retired marker reported; and an
  end-to-end upgrade from a 1.2.6 project followed by a clean audit.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change and needs no migration.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `restructured_text`, `project_sections`, `pending_restructured_markers`, `migration_restructures`, and the `RESTRUCTURE` plan row. |
| `migrations/061-governed-phase-reads.json` | Declared restructure and retired markers to read, not to change. |
| `tests/` | Upgrade restructure tests. |

## Technical Context

- Observed on 2026-10-04: the Palimpsest audit after `upgrade --apply` showed
  `FAIL marker-integrity` for `manual-verification-review-check` v1 and
  `task-worktree-review` v4 and `UNVERIFIED` for `ci-verified-validation` v1, all
  in the carried checklist section; removing the three blocks gave a clean audit.
- Reuse the retired-marker list the migration already declares; do not add a
  second list.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing which markers migration 061 retires, the backup naming, and other upgrade
actions.

## Dependencies

- **Depends on**: —
- **Blocks**: none
