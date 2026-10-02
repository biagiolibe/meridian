# Task 112 — Add a sharded test runner with a coverage proof

> **ID**: `112`
> **Category**: Test tooling
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 101 validation could not finish in the agent host

## Objective

The full suite (`python3 -m unittest discover -s tests`, 446 tests) takes about
90 seconds. A host that interrupts a command after roughly 30 seconds never
returns an exit status, so the required validation cannot be recorded. Add a
repository script that runs the suite in deterministic, disjoint shards, each
short enough for such a host, and that prints enough to prove afterwards that
every test belonged to exactly one shard.

## Acceptance Criteria

- [ ] `python3 scripts/run_tests.py --shard I/N` (1-based `I`, `N` at least 1)
  discovers the tests under `tests/`, sorts their ids, selects the ids whose
  zero-based position modulo `N` equals `I - 1`, runs them with the standard
  `unittest` runner, and exits with that runner's status.
- [ ] Before running, the script prints one line with these fields:
  `shard=I/N total=T selected=K digest=<sha256>`, where `digest` is the SHA-256
  of the sorted test ids joined by newlines. Every shard of the same tree prints
  the same `total` and `digest`.
- [ ] `python3 scripts/run_tests.py --list` prints `total` and `digest` only and
  runs nothing.
- [ ] The selection is deterministic across runs and platforms, the shards for a
  given `N` are disjoint, and their union is every discovered test. A test
  proves this on a small generated suite, and another proves that adding a test
  changes the digest.
- [ ] An invalid shard (`0/4`, `5/4`, `a/b`, a missing value) exits with status 2
  and a usage message. A shard that selects no test exits with status 2 and says
  so; it is never reported as a pass.
- [ ] The default shard count is documented, chosen from measured timings: the
  handoff records each shard's wall time on the developer's machine, and the
  default `N` makes the slowest shard finish well inside 25 seconds. If no `N`
  achieves that, the task reports the slowest module and stops instead of
  choosing a number.
- [ ] `python3 -m unittest discover -s tests` remains the canonical full run and
  is unchanged; the sharded runner does not replace it.
- [ ] The script uses the standard library only, executes only the discovered
  tests, and does not take a command to run.
- [ ] `CONTRIBUTING.md` documents the runner, the coverage line, and that a
  sharded run is complete only when all `N` shards ran on the same tree with the
  same digest.
- [ ] `CHANGELOG.md` records the script under `[Unreleased]`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/run_tests.py` | New runner. |
| `tests/test_run_tests.py` | New tests. |
| `CONTRIBUTING.md` | Validation section. |
| `CHANGELOG.md` | `[Unreleased]` entry. |

## Technical Context

- On 2026-10-02 the discovery counted 446 tests. The largest classes are
  `test_meridian_cli.MeridianCliTest` (63), `BudgetCliTest` (26), and
  `CapabilityProfileManifestTest` (24). Test counts are not timings, so the
  modulo split balances counts; the timing check in the criteria decides whether
  that is good enough.
- The reported host limit (about 30 seconds without an exit status) comes from the
  developer's report on Task 101 and was not measured here.
- The digest and total are what Task 113's verifier uses to prove coverage of a
  sharded run.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_run_tests.py' -v`
- Evidence tier: selection, digest, and exit statuses are program-computed and
  asserted; the shard timings are recorded from a real run on the developer's
  machine.

## Out of scope

The evidence record and its verifier (Task 113), the CI trigger (Task 114),
parallel execution, test selection by duration, and any change to the tests
themselves.

## Dependencies

- **Depends on**: 100
- **Blocks**: 113
