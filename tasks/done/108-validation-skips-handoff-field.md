# Task 108 — Add the `Validation skips` handoff field and its check

> **ID**: `108`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Implement Decision 6: the completion handoff records a named sandbox skip (test name, reason, reporting command), and the handoff check accepts a named skip while still rejecting an unnamed failure.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [x] The completion report templates for both workflow modes gain a `Validation skips:` line; this task changes the repository's own copies and leaves the managed shipping to tasks 109 and 110.
- [x] `meridian execution handoff-check` accepts a recorded named skip and rejects a handoff that reports a failing check without one.
- [x] Tests cover task 099's `test_split_payload_compiles_as_applescript` skip text.
- [x] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 099, 100
