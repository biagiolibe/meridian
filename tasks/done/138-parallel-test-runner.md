# Task 138 — Run the unit suite in parallel without changing what it covers

> **ID**: `138`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Call-count and polling analysis, 2026-10-03

## Objective

The full suite takes about two minutes (523 tests on 2026-10-03) and agents wait
for it with repeated polls (task 137 reduces the polls; this task shortens the
wait). `scripts/run_tests.py` already splits the suite into deterministic,
disjoint shards with a SHA-256 coverage proof, but it runs one shard per
invocation. The machine measured has 10 cores. Add a mode that runs the shards
concurrently and reports one result, without changing which tests run or what the
gates require.

## Acceptance Criteria

- [x] `scripts/run_tests.py --parallel N` runs N shards concurrently as separate
  processes and prints one combined result: total tests, failures, errors,
  skips, wall time, and the full-suite coverage proof computed over all shards.
  The exit status is non-zero if any shard fails, errors, or is killed, and the
  failing shard's tests and diagnostics are shown first, bounded.
- [x] The coverage proof of a parallel run equals the proof of a sequential full
  run and of the union of `--shard` runs; a test or script check proves that no
  test is dropped or duplicated for several values of N.
- [x] Output is bounded and ordered deterministically: per-shard output is
  captured and printed in shard order, not interleaved, and a passing run prints
  a short summary only.
- [x] Before the mode is documented as safe, tests prove shard isolation: no two
  shards share a mutable path, port, Git configuration, or environment variable.
  Where a test shares global state, it is fixed or serialized, and each such case
  is listed in the handoff. A run repeated several times produces the same result.
- [x] The default number of workers adapts to the machine (bounded by the CPU count
  and a documented ceiling) and can be set explicitly. `--parallel 1` behaves like
  a sequential run.
- [x] The documented validation command for the full suite is unchanged
  (`python3 -m unittest discover -s tests -q ...`). The parallel runner is offered
  as an optional faster equivalent. If this repository adopts it for its own
  validation, the project-owned candidate-validation declaration is updated in the
  same change so `integrate finalize` still finds the required fragment, and the
  handoff records that decision; a consumer's declaration is never touched.
- [x] The measured wall time of the sequential and parallel runs is recorded in the
  handoff on the same machine, with the worker count used. If the speedup is below
  about a third of the sequential time, the task reports it and the mode is
  documented as marginal rather than recommended.
- [x] CI continues to run the suite as it does today unless the handoff shows the
  parallel mode is faster and equivalent; no required check is weakened.
- [x] Tests cover: worker counts of 1, N greater than the shard count, and a count
  above the ceiling; a failing shard; a killed shard; deterministic output order;
  and the coverage proof across modes.
- [x] One changelog fragment is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/run_tests.py` | Sharded runner to extend. |
| `tests/` | Runner tests and any isolation fixes. |
| `CONTRIBUTING.md` | Documents the sharded runner and the new mode. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Optional mention of the faster equivalent. |
| `.meridian/candidate-validation.json` | Only if this repository adopts the runner. |

## Technical Context

- Measured on 2026-10-03: the sequential full suite ran in about 119 to 122
  seconds for 523 tests (task 118 report); the runner currently exposes
  `--shard I/N` and `--list` only.
- Shards are disjoint by construction, but disjoint test lists do not prove
  disjoint resources; the isolation criterion above is the risk of this task.
- Task 125 made the mandatory candidate-validation fragments project-declared;
  a different full-suite command needs a matching declaration in this
  repository's own file.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 scripts/run_tests.py --parallel <N>` compared with the sequential run
- `git diff --check`

## Out of scope

Changing which tests exist, skipping or weakening any test, a test-selection
mechanism based on changed files, and changing the consumer-facing validation
profile.

## Dependencies

- **Depends on**: —
- **Blocks**: none
