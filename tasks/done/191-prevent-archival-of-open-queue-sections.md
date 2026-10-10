# Task 191 — Prevent archival of open queue sections

> **ID**: `191`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Assigned to**: unassigned
> **Session**: GitHub issue triage, 2026-10-10

## Objective

Fix [issue #8](https://github.com/biagiolibe/meridian/issues/8): a completed
`###` subsection can carry later `##` phases and open rows into the archive.
Make section boundaries and completion checks conservative and deterministic.
Authority: `docs/ADR_STOPS_AND_DENIALS.md`, the never-silent gate contract.

## Acceptance Criteria

- [x] A regression test reproduces issue #8 before the fix: `B-SPIKE` stays in
  the operational queue and never appears in the archive afterwards.
- [x] A section ends at the next heading of the same or higher level. Nested
  sections cannot cause overlapping archival or duplicate content.
- [x] Every task table and row in an archival range is checked. No range
  containing a non-terminal task row is archived, even when its first table
  is complete. Ambiguous input is retained and reported with its section and
  reason instead of being assumed complete.
- [x] Tests cover mixed heading levels, multiple tables, nested headings,
  terminal and non-terminal rows, idempotency, and both workflow modes.
- [x] Existing recognized closed sections still archive correctly. Task 168's
  warnings remain meaningful and agree with the corrected boundaries.
- [x] A generated archive header refers to the resolved queue location or to
  the operational queue role; it never assumes `tasks/QUEUE.md` for consumers.
- [x] Add a changelog fragment and document the corrected archival boundary.
- [x] Repository checks, the full unit suite, and `git diff --check` pass.

## Relevant Files

`scripts/meridian.py`, `tests/test_meridian_cli.py`,
`docs/WORKTREE_LIFECYCLE.md`, `changelog.d/`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

General support for arbitrary queue table formats, changing the meaning of
`INCONCLUSIVE`, and repairing consumer archives automatically.

## Dependencies

- **Depends on**: 168
- **Blocks**: none

## Completion

The regression failed before the fix because `B-SPIKE` disappeared from the
operational queue. It passes after the fix. Archival and warnings now share
heading ranges and all-table checks. Regression coverage lives in
`tests/test_task_worktree_isolation.py`, beside the existing archival tests.
Repository checks, all 884 unit tests, and `git diff --check` pass.
See `tasks/handoffs/191.md` for validation evidence and environment skips.
