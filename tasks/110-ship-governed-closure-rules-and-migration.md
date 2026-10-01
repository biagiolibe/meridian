# Task 110 — Ship the Governed SDD closure rules and migration

> **ID**: `110`
> **Category**: Workflow template
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Ship the same rules to Governed SDD with Decision 7: `Review: REQUIRED` remains a gate that stops closure at `REVIEW_REQUIRED`, `NOT_REQUIRED` tasks run to cleanup, and the reviewer-integrator performs the integration steps after approval.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] The Governed `PROJECT_WORKFLOW.md`, implementation and review procedures state the authority rule, the exclusion list, and the stop reasons in bumped capability blocks.
- [ ] The text states that a required review is a gate and not a request for authorization.
- [ ] A migration, marker baselines, and upgrade tests follow the pattern of migrations 056 and 057.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/` | Changed or read by this task. |
| `migrations/` | Changed or read by this task. |
| `release-baselines/` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 109
