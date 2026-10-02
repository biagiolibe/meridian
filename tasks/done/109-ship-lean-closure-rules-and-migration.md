# Task 109 — Ship the Lean Delivery closure rules and migration

> **ID**: `109`
> **Category**: Workflow template
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Ship Decisions 1, 2, 5, and 6 to Lean Delivery: the authority rule, the governance-file ownership rule, the closure procedure with its stop reasons, and the validation-skip rule, in the Lean template and this repository's own workflow documents, with a migration.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md` states the authority rule with the exclusion list from `docs/TASK_CLOSURE_DESIGN.md` and the closure procedure, in a bumped capability block.
- [ ] This repository's `PROJECT_WORKFLOW.md`, `CLAUDE.md`, and `AGENTS.md` carry the same text and keep the language policy.
- [ ] A migration (next free number) records the capability versions, managed paths, and delta; marker baselines and the upgrade tests are updated; consumer-owned text is preserved.
- [ ] The change is declared template-changing and the release bookkeeping follows the release procedure.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/lean-delivery/` | Changed or read by this task. |
| `PROJECT_WORKFLOW.md` | Changed or read by this task. |
| `migrations/` | Changed or read by this task. |
| `release-baselines/` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 100, 101, 102, 103, 104, 106, 107, 108
