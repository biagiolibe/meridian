# Task 168 — Report queue sections that archival cannot read

> **ID**: `168`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

Issue #2: `_archive_completed_queue_sections` skips any section whose heading
level or table header it does not recognize, and reports nothing. One Governed
SDD project's queue grew to about 88 KB without an archive. This breaks the
"never silent" property of `docs/ADR_STOPS_AND_DENIALS.md`. Make the skip
visible. The archival rules themselves do not change.

## Acceptance Criteria

- [x] When a queue section contains a table with a `Status` column that the
  archiver does not recognize, `integrate stage` reports a warning naming the
  section heading and the reason, such as heading level or column order. The
  same warning appears in the `meridian worktree closure-status` or stage JSON
  output under `warnings`.
- [x] A warning never blocks the stage and never changes the merged tree.
  Recognized sections are archived exactly as before.
- [x] A section that stays open only because of an `INCONCLUSIVE` row is
  reported as such, without changing whether it is archived.
- [x] Tests reproduce issue #2's example (`## ` heading with `Dependencies |
  Estimate` columns), a recognized section, and an `INCONCLUSIVE` section.
- [x] One changelog fragment is added under `Changed`; this is a CLI-only change.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_archive_completed_queue_sections` and the stage output. |
| `tests/test_meridian_cli.py` | Archival tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decision 2, property 4.
- Whether `INCONCLUSIVE` closes a section, and whether the archiver should
  read other heading levels or column orders, are open questions in issue #2.
  They are not decided here.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing which sections are archived, the `INCONCLUSIVE` rule, and supporting
other queue shapes.

## Dependencies

- **Depends on**: 162
- **Blocks**: none
