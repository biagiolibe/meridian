# Task 193 — Align the SPIKE blueprint with worktree closure

> **ID**: `193`
> **Category**: Workflow template
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: GitHub issue triage, 2026-10-10

## Objective

Fix [issue #9](https://github.com/biagiolibe/meridian/issues/9): the managed
blueprint says to commit a SPIKE deliverable directly to `main` and never merge
its branch, contradicting dedicated task worktrees and governed integration.

## Acceptance Criteria

- [x] The SPIKE shape distinguishes the separate local throwaway probe branch
  from the canonical task branch. Probe code is never merged or pushed; the
  task branch carries the deliverable and permitted lifecycle/evidence records
  and completes through the ordinary governed closure.
- [x] Replace every direct-to-main instruction for SPIKE deliverables in the
  affected managed blueprint and keep corresponding skill assets in parity.
- [x] Ship the correction through a bumped `task-blueprint` capability and a
  migration following the current release procedure. Consumer-owned text is
  preserved; no historical task record is rewritten automatically.
- [x] Upgrade tests cover an existing baseline and prove that the corrected
  blueprint arrives without contradictory managed instructions or drift.
- [x] Add a template-changing changelog fragment with Upgrade notes that tell
  consumers to inspect copied instructions in non-terminal SPIKE records.
- [x] Repository checks, the full unit suite, and `git diff --check` pass.

## Relevant Files

`templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md`, `skills/`,
`migrations/`, marker baselines, upgrade tests, `changelog.d/`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing SPIKE outcomes, production-code permissions, or consumer task records.

## Dependencies

- **Depends on**: 192
- **Blocks**: none

## Completion

Implemented in `37a7a58507a18dcab204539cad6108363155331c`. All acceptance criteria are met; validation and the single named sandbox skip are recorded in `tasks/handoffs/193.md`.
