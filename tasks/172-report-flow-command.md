# Task 172 — Add `meridian report flow` over the lifecycle journal

> **ID**: `172`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Rigidity measurement follow-up to ADR stops and denials, 2026-10-05

## Objective

Turn the journal from task 171 into the three numbers that show whether
Meridian is getting lighter or heavier:
- how long a task takes from preparation to integration;
- how often and where tasks stop;
- what share of the work fixes friction that Meridian caused.

## Acceptance Criteria

- [ ] `meridian report flow [--project <primary>] [--since YYYY-MM-DD]
  [--format text|json]` is read-only and reads the current and rotated journal
  files.
- [ ] Per task, it reports:
  - lead time from the first successful `prepare` to the successful `integrate
    finalize`;
  - stops by code;
  - number of aborts;
  - number of `prepare --resume` runs.
- [ ] Across the period, it reports totals and the median lead time, and stops
  grouped by code and by class, with the class taken from the stop registry.
- [ ] It reads an optional task header `> **Origin**: capability | friction |
  maintenance | release` from the task record or its archive. It reports the
  share of each origin, and `unknown` for tasks without the header. `friction`
  means the task fixes a problem caused by Meridian's own rules or tools.
- [ ] This repository's `tasks/TASK_BLUEPRINT.md` gains the optional `Origin`
  line, if that file is not a managed copy. Template blueprints are not changed
  in this task.
- [ ] Malformed journal lines are counted and reported, never fatal. An empty
  or missing journal gives an empty report and exit status 0.
- [ ] Tests cover lead time, stop grouping, the period filter, origin shares,
  malformed lines, and an empty journal.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | New `report flow` command. |
| `capabilities/stop-codes-v1.json` | Stop classes. |
| `tasks/TASK_BLUEPRINT.md` | Optional `Origin` line. |
| `tests/` | Report tests. |

## Technical Context

- Lifecycle state already records `started_at`. Prefer the journal when
  available, and fall back to `started_at` only for tasks prepared before the
  journal existed.
- Unbacked `BLOCKED` records from task 173 are reported when present, as
  their own line.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Dashboards, the console, sending data anywhere, and adding `Origin` to the
template blueprints.

## Dependencies

- **Depends on**: 171
- **Blocks**: none
