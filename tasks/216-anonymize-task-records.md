# Task 216 — Anonymize private-project references in task records

> **ID**: `216`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

About 104 files under `tasks/` (queue, archive, task records, reviews, and
handoffs) name the developer's private projects. The records stay public as
evidence that Meridian is built with Meridian. Anonymize them the way task 215
did, and extend the name guard to the whole tree.

## Acceptance Criteria

- [ ] No tracked file under `tasks/` contains either denied name as a whole
  word. Mentions use the same neutral descriptions as task 215.
- [ ] Only names change. Statuses, IDs, dates, commit SHAs, verdicts, and
  measured facts are unchanged. A test or the handoff shows that
  `meridian audit`, the console snapshot, and queue parsing give the same
  results before and after.
- [ ] The name guard of task 215 no longer excludes `tasks/`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `tasks/` | Records to anonymize. |
| `scripts/check_repository.py` | Guard scope. |

## Technical Context

- Editing archived records is anonymization, not a change of history. It is
  out of the scope of the "do not rewrite historical records" clause of
  `docs/ADR_MACHINE_TASK_STATE.md`, which concerns status and verdicts.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Git history and moving `tasks/` out of the distributed tree.

## Dependencies

- **Depends on**: 215
- **Blocks**: none
