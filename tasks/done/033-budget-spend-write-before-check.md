# Task 033 — `budget_spend()` durably consumes budget before the cap check can reject it

> **ID**: `033`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned

## Objective

`budget_spend()` in `scripts/meridian.py` writes the incremented counter to
disk via `write_budget_state()` *before* checking whether the new count
exceeds the cap. When the cap check then raises `MeridianError`, the
incremented counter has already been persisted — the spend is durably
consumed even though it was rejected.

This breaks callers that spend budget as a precondition for recording a
result, such as `record_investigation()`. If the budget-exhausting call is
the one that would have recorded the finding, the finding is lost (the
`MeridianError` propagates before the finding is written to
`.meridian/execution-evidence.json`), but the consumed unit stays spent.
A second attempt then has no budget left to retry.

## Acceptance Criteria

- [x] `budget_spend()` does not durably persist a counter increment that it
      is about to reject via `MeridianError`. Either check the prospective
      count against the cap before writing state, or otherwise make the
      write and the raise consistent (e.g. write only after confirming the
      spend is accepted).
- [x] A spend that would exceed the cap raises `MeridianError` and leaves
      the on-disk budget state unchanged from before the call.
- [x] A regression test exercises `record_investigation()` (or
      `budget_spend()` directly) hitting the cap and confirms the stored
      counter for that task/kind is not incremented past what was already
      durably committed, and that a subsequent retry at the same scope is
      not silently starved by a rejected attempt.
- [x] Existing budget/investigation tests continue to pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `budget_spend()` (~line 2346) writes state before the cap check; `record_investigation()` (~line 2662) is the caller that loses a finding when this fires. |
| `tests/` | Add/extend a regression test for the ordering. |

## Technical Context

- **Current behavior**: `budget_spend()` computes `count = counters.get(counter_key, 0) + amount`, stores it into `counters`/`state`, calls `write_budget_state(project_root, state)`, and only then checks `if count >= cap: raise MeridianError(...)`. The write happens unconditionally, even on the branch that raises.
- **Desired behavior**: A call to `budget_spend()` that ends up raising `MeridianError` because the spend would exceed the cap must not change the persisted budget state. The caller should be able to retry the same spend later without having lost budget to a rejected attempt.

## Suggested Implementation

1. In `budget_spend()`, compute the prospective `count` and compare it to
   `cap` before calling `write_budget_state()`.
2. If the prospective count meets or exceeds the cap, raise
   `MeridianError` without writing state.
3. Only write state (and return `(count, cap)`) on the accepted path.
4. Add a test that drives a task to its investigation cap via
   `record_investigation()` (or `budget_spend()` directly), confirms the
   rejected call raises without altering the stored counter, and confirms
   the finding tied to the rejected call was never persisted to
   `execution-evidence.json`.

## Constraints and Considerations

- Preserve the existing return shape `(count, cap)` for the accepted path.
- Do not change the semantics of `BUDGET_FIELD_NAMES` / cap resolution
  (`task_cap`) — only the ordering of write vs. check.
- Keep the fix scoped to `budget_spend()`; do not restructure
  `record_investigation()` or other callers unless required to preserve
  their current contract.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/033-budget-spend-write-before-check.md)"$'\n\nExecute this task in the current project.'
```
