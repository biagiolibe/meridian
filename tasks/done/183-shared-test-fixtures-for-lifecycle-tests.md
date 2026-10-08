# Task 183 — Build lifecycle test repositories once per class and copy them per test

> **ID**: `183`
> **Category**: Refactor
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Test suite cost review, 2026-10-06
> **Origin**: friction

## Objective

No test module uses `setUpClass` or `setUpModule`. Every lifecycle test
builds its Git repository from scratch in `setUp` (`git init`, `git config`,
writing the project files, `git add`, `git commit`, often a bare `origin` and
a worktree), each step a separate process. On 2026-10-06, 222 tests above
0.5 s took 256 s of the 343 s sequential run, and the parallel run spent
162 s in system time, mostly process creation.

Build each class's starting repository once, keep it read-only, and give
every test its own copy, so each test stays isolated but stops paying for
the same setup.

## Acceptance Criteria

- [ ] At least these classes build their starting repository once per class
  (or once per module) and copy it into a fresh temporary directory for each
  test: `test_meridian_cli.WorktreeLifecycleCliTest`,
  `test_meridian_cli.BudgetCliTest`,
  `test_meridian_cli.LifecycleJournalTest`,
  `test_task_worktree_isolation.BoundedWorktreeLifecycleTest`, and the
  `test_project_console` closing-task classes. Other classes may follow the
  same pattern where setup dominates.
- [ ] Each test still gets its own repository, remote, and worktree root. No
  test can change the shared seed: the seed is checked unchanged after the
  class runs, or is created read-only, and a test proves that a mutating test
  leaves the next test's copy unaffected.
- [ ] Absolute paths recorded inside a copied repository (for example a
  remote URL or a registered worktree) are valid for the copy, not the seed.
  A seed that registers a worktree is either avoided or repaired after the
  copy.
- [ ] No test is removed, renamed, or skipped, and no assertion changes.
  `python3 scripts/run_tests.py --list` prints the same `total` before and
  after, and only helper code and setup move.
- [ ] The sequential wall time of the classes listed above drops by at least
  25% on the developer's machine. The handoff records per-class time before
  and after, and the full sequential and parallel wall times, measured with
  `python3 -m unittest discover -s tests --durations 0` and
  `python3 scripts/run_tests.py --parallel` on the same tree.
- [ ] The parallel runner still passes, and the tests still pass when run one
  at a time by id (`python3 -m unittest <test id>`).
- [ ] `python3 scripts/check_repository.py` and
  `python3 scripts/run_tests.py --parallel` pass.

## Relevant Files

| File | Role |
|------|------|
| `tests/test_meridian_cli.py` | Lifecycle, budget, and journal test classes. |
| `tests/test_task_worktree_isolation.py` | Bounded worktree lifecycle tests. |
| `tests/test_project_console.py` | Closing-task console tests. |
| `tests/` | A shared fixture helper module, if one is added. |
| `scripts/run_tests.py` | Parallel runner; read only. |

## Technical Context

- **Current behavior**: `WorktreeLifecycleCliTest.setUp` runs `git init`,
  two `git config` calls, writes the project, then `git add` and
  `git commit`, all as separate processes, before every test.
- **Desired behavior**: one build per class, then a directory copy per test.
- Measured on 2026-10-06 (sequential, per class): `WorktreeLifecycleCliTest`
  60.4 s, `MeridianCliTest` 57.3 s, `BudgetCliTest` 30.0 s,
  `BoundedWorktreeLifecycleTest` 28.5 s, `LifecycleJournalTest` 10.7 s,
  `LeanClosingTaskTest` 11.3 s, `GovernedClosingTaskTest` 9.6 s.
- A per-test coverage analysis on the same date found no safe bulk test
  removal: identical line coverage usually means different inputs, so the
  cost is setup, not redundant tests.

<!-- TODO: add relevant code snippets and file paths -->

## Suggested Implementation

<!-- TODO: add relevant code snippets and file paths -->

## Constraints and Considerations

- Test-only change: no shipped file, template, or managed text changes, so no
  migration. Add a changelog fragment only if `CONTRIBUTING.md` requires one
  for test-only changes.
- Out of scope: removing or merging tests, splitting
  `tests/test_meridian_cli.py`, and changing the validation command (task
  182).
- `shutil.copytree` must keep Git's file modes and symlinks
  (`symlinks=True`).

## Resolution

Cancelled on 2026-10-08 by the developer. Controlled measurements on the same
Mac with Python 3.12.15 compared pre-refactor commit `2d0753ee` with the
shared-seed implementation. The six required classes improved from 358.27 s
to 351.89 s, a 1.8% reduction, below the required 25%.

| Class | Before (s) | After (s) | Reduction |
|---|---:|---:|---:|
| `WorktreeLifecycleCliTest` | 147.49 | 141.67 | 3.9% |
| `BudgetCliTest` | 86.80 | 88.90 | -2.4% |
| `LifecycleJournalTest` | 26.86 | 26.59 | 1.0% |
| `BoundedWorktreeLifecycleTest` | 55.38 | 51.91 | 6.3% |
| `LeanClosingTaskTest` | 22.60 | 23.14 | -2.4% |
| `GovernedClosingTaskTest` | 19.14 | 19.68 | -2.8% |

The investigation found that the dominant cost is CLI subprocess invocation
(about 230 ms each), not per-test repository setup. Restore the original test
setup and reopen only if a lower-cost subprocess strategy is in scope.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/183-shared-test-fixtures-for-lifecycle-tests.md)"$'\n\nExecute this task in the current project.'
```
