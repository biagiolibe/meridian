# Task 227 — Re-deliver a governed task after a handoff-only correction

> **ID**: `227`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: GitHub issue #14 triage, 2026-10-16
> **Origin**: friction

## Objective

Fix [issue #14](https://github.com/biagiolibe/meridian/issues/14). In Governed
SDD, `COMPLETION_REPORT_TEMPLATE.md` tells an implementer to correct a wrong
handoff commit field with a lifecycle-only commit that changes only the
handoff, then begin the next review attempt. After `meridian execution
deliver`, that path is blocked:

- `delivery_readiness` (`scripts/meridian.py`) rejects any change to the
  handoff after the delivery transition with `EVIDENCE_INCOMPLETE: changes
  after delivery require renewed implementation and delivery`;
- `execution_deliver` returns early when the task is already
  `READY_FOR_REVIEW`, so it creates no new `Deliver <TASK-ID> for review`
  commit;
- `REVIEW.md` step 5 requires a passing `ready-check`, and only a review
  verdict leaves `READY_FOR_REVIEW`, but the review preflight stops before any
  verdict.

Let `execution deliver` re-deliver when the only change after delivery is the
handoff, and catch a malformed commit field before the first delivery.

## Acceptance Criteria

- [ ] When the task is `READY_FOR_REVIEW` and every path changed after the
  delivery transition commit is the task's handoff record, `meridian
  execution deliver` records a fresh delivery. It commits a new `Deliver
  <TASK-ID> for review` that leaves the task `READY_FOR_REVIEW` and anchors
  the delivery at the corrected handoff, then returns a passing
  `ready-check` result. The task record's state and transitions are written
  by the command, never by hand.
- [ ] Any other change after delivery still stops with `EVIDENCE_INCOMPLETE`
  as today, including a change to implementation files, the task record,
  execution evidence, or the state file.
- [ ] `meridian execution ready-check` and `deliver` fail before delivery with
  a registered stop code when the handoff's `Current task commit` field is
  missing, names the validated base `main` commit, or uses a descriptive form
  without the commit subject that `REVIEW.md` step 3 requires. The message
  names the field and the expected form.
- [ ] The governed-SDD workflow text describes the supported correction path:
  commit the handoff-only correction, then rerun `meridian execution deliver`,
  then start the next review attempt. Prefer wording that the current managed
  text already permits. If managed text inside capability markers must change,
  the change ships with its migration, and the handoff records that the
  release becomes template-changing.
- [ ] Tests cover:
  - re-delivery after a handoff-only change;
  - refusal of a later implementation change and of a later task-record
    change;
  - a second re-delivery after another handoff-only correction;
  - each malformed `Current task commit` case;
  - an unchanged `deliver` on a `READY_FOR_REVIEW` task with no later commit.
- [ ] A changelog fragment `changelog.d/227.md` records the fix under
  `Fixed`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `delivery_readiness`, `execution_deliver`, `ready-check`. |
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Correction instruction inside capability markers. |
| `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | Preflight steps 3 and 5. |
| `migrations/` | Required only if managed marker text changes. |
| `capabilities/stop-codes-v1.json` | Registry for any new stop code. |
| `tests/` | Execution and delivery tests. |

## Technical Context

- The issue lists three options. This task takes the second (re-deliver from
  `READY_FOR_REVIEW`), because it keeps the `Deliver` commit as the review
  anchor and needs no new transition or verdict path. The first option would
  accept silent handoff changes after delivery; the third adds a public
  preflight verdict for a narrow case.
- `delivery_readiness` computes the allowed later paths as the owned paths
  minus the execution evidence and the handoff, so the handoff is rejected
  today.
- The reporting project resolved the case with a developer ruling recorded as
  a rule discrepancy; no repository data needs repair.

## Out of scope

Changing review verdicts or the `READY_FOR_REVIEW` transitions. Lean
Delivery, which has no delivery transition. Budget attempts (task 228).

## Dependencies

- **Depends on**: none
- **Blocks**: none. Task 228 also edits `scripts/meridian.py`; run them one
  after the other.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/227-redeliver-after-handoff-correction.md)"$'\n\nExecute this task in the current project.'
```
