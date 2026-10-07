# Task 185 — Report failing tests by name in the parallel runner and make timing tests tolerate a loaded runner

> **ID**: `185`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: CI failure review, 2026-10-07
> **Origin**: friction

## Objective

CI failed on "Integrate 181" (2 failures in shard 1/4) and "Integrate 184"
(1 failure in shard 2/4). A rerun of the 184 job passed with no change, and
the suite passed locally in a shallow clone with a CI-length path, no `gh`,
`codex`, or `claude` on `PATH`, and 4 workers. The failures are flaky under
load, but their names are not in the log.

Two defects caused this:

1. `scripts/run_tests.py --parallel` prints only the last `FAILURE_LINES`
   (60) lines of a failing shard. In both runs those lines were release-test
   output, so the `FAIL:` block and its traceback were cut and the failing
   test could not be named from the log.
2. Some tests assert an absolute wall-clock bound. Since task 182, CI runs 4
   shards at once on a 4-core runner, and these bounds are exceeded under
   that load. Both failing shards contained
   `test_queue_briefing.QueueBriefingTest.test_stays_under_two_seconds_on_a_300_row_queue`
   (`< 2.0` s, already seen at 2.13 s on a loaded machine in task 176) and
   `test_project_console.BackgroundRefreshTest.test_refresh_is_non_blocking_single_flight_and_published_atomically`
   (`< 1` s).

## Acceptance Criteria

- [ ] For a failing shard, `run_tests.py --parallel` prints every `FAIL:` and
  `ERROR:` block with its full traceback, whatever their position in the
  shard's output, followed by the shard's summary line. Other output stays
  bounded. A test proves that a failure followed by more than
  `FAILURE_LINES` lines of unrelated output is still printed by name with its
  traceback.
- [ ] A shard that ends without a unittest result (killed or crashed) still
  prints its bounded output tail, as today.
- [ ] Every test that asserts a wall-clock bound is listed in the handoff with
  its bound. At least `test_stays_under_two_seconds_on_a_300_row_queue`,
  `test_refresh_is_non_blocking_single_flight_and_published_atomically`, and
  the `test_task_state_lookups` elapsed check no longer fail on load alone:
  each either asserts the property without a wall-clock bound (for example a
  call count, a non-blocking return proven by an event, or a relative
  comparison measured in the same process), or keeps a bound with margin
  justified in the handoff by measurement under `run_tests.py --parallel`.
- [ ] Each changed test still fails when the property it protects is broken.
  The handoff states, per test, how that was checked (for example by
  temporarily slowing or blocking the code path).
- [ ] `python3 scripts/run_tests.py --parallel 4` passes five consecutive runs
  on the developer's machine, recorded in the handoff with their times.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`, only if a shipped
  file changes; otherwise the handoff states that none is needed.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/run_tests.py` | `bounded`, `FAILURE_LINES`, and the combined report. |
| `tests/test_run_tests.py` | Runner tests. |
| `tests/test_queue_briefing.py` | 300-row queue timing test. |
| `tests/test_project_console.py` | Background refresh timing test. |
| `tests/test_task_state_lookups.py` | State lookup elapsed check. |

## Technical Context

- **Current behavior**: `bounded()` keeps the last 60 lines, "where unittest
  prints its failure diagnostics", which is false when tests print after the
  failure block or the shard prints a long summary.
- **Desired behavior**: the log always names the failing test and shows its
  traceback; timing tests assert behavior, not machine speed.
- CI evidence: runs 37536696307 and 37537987772 (the latter passed on rerun
  of attempt 2).

<!-- TODO: add relevant code snippets and file paths -->

## Suggested Implementation

<!-- TODO: add relevant code snippets and file paths -->

## Constraints and Considerations

- Do not reduce CI parallelism or return CI to the sequential run; task 182
  chose the parallel run deliberately.
- Do not skip a timing test in CI only; a test that cannot fail in CI
  protects nothing there.
- Out of scope: shared fixtures (task 183) and removing tests.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/185-diagnosable-parallel-failures-and-load-tolerant-timing-tests.md)"$'\n\nExecute this task in the current project.'
```
