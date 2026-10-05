# Task 179 — Stabilize the parallel runner output comparison test

> **ID**: `179`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~0.5h
> **Assigned to**: Claude Code
> **Session**: CI failures on "Integrate 163" and "Integrate 164", 2026-10-05

## Objective

`test_failing_shards_are_shown_first_in_shard_order_and_bounded` in
`tests/test_run_tests.py` runs the same failing suite twice and compares the
outputs after `stable()` normalizes them. `stable()` removes only the
`time=…s` summary. A failing shard's diagnostics also contain unittest's own
`Ran 1 test in 0.000s` line, and on the slower GitHub runner that value is
sometimes `0.001s`. The comparison then fails at random, which caused the CI
failures on `5a4d943` and `0571006`.

## Acceptance Criteria

- [ ] `stable()` also normalizes unittest's `Ran N test(s) in X.XXXs`
  timing, so that two otherwise identical runs compare equal.
- [ ] The runner (`scripts/run_tests.py`) is unchanged, and no assertion is
  weakened apart from the timing normalization.
- [ ] A test proves that `stable()` maps two outputs that differ only in the
  inner timing to the same text.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `tests/test_run_tests.py` | `stable()` and the flaky comparison. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changes to the runner output format.

## Dependencies

- **Depends on**: —
- **Blocks**: none
