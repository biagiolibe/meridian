# Task 198 — Report retired framework text left outside managed markers

> **ID**: `198`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Fusa TASK-046 reasoning stop after upgrading to 1.2.12, 2026-10-11
> **Origin**: friction

## Objective

Migration 063 (1.2.9) retired the reasoning budget contract. It removed the
protected block and the template text, but an upgrade never removes text
outside managed markers, because that text belongs to the project. Fusa,
upgraded to 1.2.12, still carried the bootstrap-era wording in the
project-owned parts of two files:
- in `docs/EXECUTION_EVIDENCE_PROFILE.md`: "confirm the session's effective
  setting equals the task's `Reasoning` value … if it cannot be confirmed,
  stop and start a fresh session at the declared value";
- in `docs/CONTEXT_BUDGET_POLICY.md`: a `## Reasoning profile` section.

An agent stopped on that text for TASK-046. Neither `upgrade --check` nor the
1.2.9 upgrade notes told the adopter to remove it. Make Meridian report such
leftovers so that the adopter can remove them by hand. Meridian never removes
them itself.

## Acceptance Criteria

- [x] A registry `capabilities/retired-text-v1.json` lists, for each retired
  capability, the version that retired it, a small set of distinctive phrases,
  the files where they were seeded, and a one-line remedy. The first entry
  covers `reasoning-budget-contract` (retired in 1.2.9) with at least these
  phrases:
  - `fresh session at the declared value`;
  - `effective setting equals the task's`;
  - `Reasoning justification`;
  - `reasoning cap`;
  - `## Reasoning profile`.
  A schema in `schemas/` validates the file.
- [x] `meridian upgrade --check` and `meridian audit` scan only the
  project-owned text of the listed files, outside `MERIDIAN:BEGIN/END`
  regions, and only in projects whose framework version is at or after the
  retiring version.
  - Each match is reported as an advisory naming the file, the line, the
    retired capability, and the remedy. `audit` uses its existing `ADVISORY`
    state.
  - A match never blocks, never changes the exit status of an otherwise
    passing run, and never modifies a file.
- [x] Task records, handoffs, review records, and archives are not scanned,
  so historical `Reasoning` fields in tasks produce no advisory.
- [x] Phrase matching is case-insensitive and literal, not a regular
  expression, and text inside managed regions never matches.
- [x] `CONTRIBUTING.md` requires every future retirement migration to register
  its distinctive phrases in the registry, in the same task.
- [x] Tests cover:
  - a project-owned match in each listed file;
  - the same phrase inside a managed region, which is not reported;
  - a matching phrase in a task record, which is not reported;
  - a project older than the retiring version;
  - a clean project;
  - that the exit status and files are unchanged.
- [x] One changelog fragment states the advisory under `Added`. Its `Upgrade
  notes` tell 1.2.9+ adopters to remove the reported reasoning text from
  project-owned sections by hand.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `capabilities/retired-text-v1.json` | New registry. |
| `schemas/` | Registry schema. |
| `scripts/meridian.py` | `upgrade --check` reporting and the `audit` rows. |
| `CONTRIBUTING.md` | Rule for future retirement migrations. |
| `tests/test_meridian_cli.py` | Advisory tests. |

## Technical Context

- Evidence: Fusa `docs/EXECUTION_EVIDENCE_PROFILE.md` lines 171–182 and
  `docs/CONTEXT_BUDGET_POLICY.md` lines 135–160, all outside markers, seeded
  at bootstrap (`9733487`) and kept by every upgrade through 1.2.12.
  Palimpsest at 1.2.12 carries `Reasoning` fields only in historical task
  records.
- `docs/ADR_STOPS_AND_DENIALS.md` already makes such text advice rather than
  a valid stop. This task removes the source of the confusion. It is not a
  new gate.
- This is a CLI-only change and needs no migration.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Removing or rewriting project-owned text, editing released migrations,
scanning task records, and agent-evaluation scenarios.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## Completion

Implemented and validated on `task-198`; see `tasks/handoffs/198.md`.
Registry-backed retired-text advisories preserve project files and command exit
status. Queue and project-plan closure are owned by integration stage.
