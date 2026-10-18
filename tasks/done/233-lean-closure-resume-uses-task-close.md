# Task 233 — Resume a Lean closure without state through `task close`

> **ID**: `233`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: 1.4.1 blocking fixes, 2026-10-18
> **Origin**: friction

## Objective

When a Lean task commits its completion records but skips `meridian task
close`, `meridian worktree advance` stops at closure step C6 with
`BLOCKED TASK_STATE_MISSING`. The resume it prints is `meridian task
transition <TASK-ID> DONE --project <task-worktree>`. That command writes
DONE state but neither archives the record nor stages anything, and
afterwards `task close` refuses the task as already DONE. Following the
printed resume therefore leads away from the documented Lean closure.

Task 218 added this resume on 2026-10-15, and `task close` arrived the same
day without it. Cardine hit the stop in task 015 and fixed it in its task
018 (Cardine commit `18d1881`). Port that fix to Meridian 1.4.1 as a
blocking defect.

## Acceptance Criteria

- [x] For a Lean task whose record is not archived and whose state file is
  missing at the task commit, `advance` stops at C6 with
  `TASK_STATE_MISSING`. Its `commands` and `resume` name, in order:
  `meridian task close <TASK-ID>` run in the registered task worktree, a
  commit of the staged closure records, and the same `advance` command again.
  Each command runs unchanged from the location it names.
- [x] A test follows those commands and reaches the next closure step
  (stage), with the record archived under `tasks/done/` and the DONE state
  tracked at the task commit.
- [x] When the record is already archived but the state file is missing, the
  stop names that state and a resume that does not call `task close`.
- [x] Governed SDD keeps its current resume for this stop.
- [x] The `TASK_STATE_MISSING` entry in `capabilities/stop-codes-v1.json`
  describes the Lean closure resume. `test_advance_state_gate_runs_before_stage`
  in `tests/test_task_integration_state.py` asserts the new Lean resume and
  keeps its other assertions.
- [x] No file under `templates/` or `migrations/` changes.
- [x] `changelog.d/233.md` describes the fix.
- [x] Every command under Validation passes.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` (`advance_task_closure`, step C6) | Builds the Lean resume. |
| `capabilities/stop-codes-v1.json` | Registry entry. |
| `tests/test_task_integration_state.py` | C6 state-gate tests. |
| Cardine commit `18d1881` (`biagiolibe/cardine`) | Reference implementation and tests. |

## Technical Context

- Current code: in step C6, `advance_task_closure` catches
  `TASK_STATE_MISSING` and, for `lean-delivery`, sets
  `resume = f"meridian task transition {task} DONE --project ..."`.
- Cardine's fix changed `scripts/meridian.py`, the stop registry, and
  `tests/test_task_integration_state.py`. Port it by hand: cross-repository
  cherry-picks are not part of the authorized lifecycle.

## Out of scope

Other closure steps and template text.

## Dependencies

- **Depends on**: 232
- **Blocks**: 234

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`
