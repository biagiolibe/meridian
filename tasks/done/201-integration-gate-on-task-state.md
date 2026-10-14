# Task 201 — Gate `integrate stage` on task state and the approved commit

> **ID**: `201`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR machine task state, 2026-10-11
> **Origin**: friction

## Objective

Implement Decisions 3, 4 (queue projection), and 5 of
`docs/ADR_MACHINE_TASK_STATE.md`. `integrate stage` decides from the task
state file and Git only. It stops before the lease and merge when acceptance
is not proven, and it never integrates with a non-blocking `REVIEW_PENDING`.

## Acceptance Criteria

- [x] For a project that has adopted task state (a `.meridian/tasks/`
  directory exists), `integrate stage` reads the candidate's state file through
  the shared reader, before the lease and the merge.
  - A missing file is `TASK_STATE_MISSING`.
  - An invalid file is `TASK_STATE_INVALID`.
  - A status that is not the terminal value the workflow requires is
    `TASK_STATE_INVALID`.
- [x] For a required review, stage also requires `review.verdict ==
  "APPROVE"` (else `REVIEW_NOT_APPROVED`) and `review.reviewed_commit` to be
  an ancestor of the task branch `HEAD`. It also requires `git diff
  --name-only <reviewed_commit> <HEAD>` to name only these paths, else
  `REVIEW_STALE`:
  - the task record or its exact archive;
  - the handoff and the review record;
  - the state file;
  - the canonical `.meridian/execution-evidence.json`.
  Each detail names the file, the expected value, and the value found, or the
  offending paths.
- [x] `REVIEW_NOT_APPROVED` and `REVIEW_STALE` are registered with tests that
  assert their output lines.
- [x] The state file of the task is added to the paths a task branch may change
  and that stage accepts in the task diff, including under the `REUSE` proof.
- [x] Stage writes the queue `Status` cell from the state file on the
  candidate tree. `REVIEW_PENDING` is removed as a result: stage completes the
  row or stops. `meridian worktree advance` reports the new stops through the
  registry.
- [x] A project without `.meridian/tasks/` keeps today's behavior until it
  adopts task state (task 203). The prose verdict path stays only for that
  legacy case, and the result labels it `legacy`.
- [x] Tests cover:
  - an approved task integrates;
  - a code change after approval gives `REVIEW_STALE`;
  - a missing verdict gives `REVIEW_NOT_APPROVED`;
  - a missing state file gives `TASK_STATE_MISSING`;
  - a SPIKE task and a review-not-required task integrate;
  - the queue projection;
  - nothing is merged or leased on any stop.
  Include a regression for consumer project A's dated heading
  (`## Attempt 1 — 2026-10-11 — APPROVE`), which no longer affects the
  decision.
- [x] One changelog fragment states the gate under `Changed`; this is a
  CLI-only change.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_governed_completion_row`, `_apply_task_completion_rows`, stage path checks, `advance`. |
| `capabilities/stop-codes-v1.json` | New codes. |
| `docs/WORKTREE_LIFECYCLE.md` | Stage contract. |
| `tests/` | Gate tests. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decisions 3 to 5.
- Evidence: consumer project A `F2-TOKENS-001` (`be74ae7`) and `F2-TILE-001` were
  integrated with `REVIEW_PENDING`, and their queue rows stayed `QUEUED`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

The console, import, and managed text.

## Dependencies

- **Depends on**: 200
- **Blocks**: 203

## Completion

Implemented the pre-lease task-state gate, commit-bound review checks, registered
review stops, and state-driven queue projection. Legacy prose decisions are
labeled and missing approval blocks integration. The task state is allowed in
task-local lifecycle changes, SPIKE diffs, and the documented REUSE proof.
The committed record supplies SPIKE classification only; status and verdict
come from the shared state reader. No console, import, or managed procedure
text changed. The lifecycle contract and its managed-copy digest were updated.

Validation on `6ef2580b298b509df71cdf769275af27cdd060d6`:
- `python3 scripts/check_repository.py` — exit 0.
- `python3 scripts/run_tests.py --parallel` — exit 0; 951 tests, no failures,
  errors, or skips, eight shards, complete coverage.
- `git diff --check` — exit 0.

The 20 integration-state tests cover approved finalization, dated review
headings, missing/rejected verdicts, missing/malformed/non-UTF-8 state,
impossible history, nonterminal state, stale code, ancestor proof, task-local
governance paths, other-task state, SPIKE classification, both SPIKE terminal
values, review-not-required and Lean tasks, queue projection, legacy behavior,
and advance stop propagation. Gate failures preserve HEAD, tree, queue, lease,
merge, and integration state.
