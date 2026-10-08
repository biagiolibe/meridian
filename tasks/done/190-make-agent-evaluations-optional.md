# Task 190 — Make agent evaluations an optional tool, not a release gate

> **ID**: `190`
> **Category**: Process
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: Claude Code
> **Session**: Release 1.2.11 preparation, 2026-10-08
> **Origin**: friction

## Objective

Task 178 made a full agent-evaluation run on Claude Code mandatory before
every template-changing release. A missed safety threshold blocked the
release, and the pass counts had to be recorded in the release commit message.
A full run is 30 billed agent sessions. The developer has decided that the
harness is an on-demand tool, used when a change warrants it, and not a
release gate. Remove the obligation everywhere it is stated, and keep the
harness itself unchanged.

## Acceptance Criteria

- [x] `CONTRIBUTING.md`:
  - "Agent evaluations" describes the harness as an optional, on-demand tool;
  - it gives examples of when a run is useful, such as a change to stop,
    denial, or closure rules in managed text, or an agent behavior regression
    to reproduce;
  - it no longer requires a run before a release, a release block on a missed
    safety threshold, or pass counts in the release commit message;
  - the release procedure no longer mentions agent evaluations as a step.
- [x] `scripts/release.py` no longer prints the agent-evaluation reminder in
  `prepare`, in its dry run, or when it directs a prepared release to
  `publish`. `agent_eval_reminder` is removed.
- [x] `tests/test_release.py` asserts that no release path prints
  `run_agent_evals`, and the other release behavior is unchanged.
- [x] `docs/ADR_STOPS_AND_DENIALS.md` keeps its follow-up list but no longer
  says the evaluations run on template-changing releases. It states that they
  run on demand, with a short note that the developer decided this on
  2026-10-08.
- [x] `scripts/run_agent_evals.py`, the scenarios, and their thresholds are
  unchanged; a run still reports `threshold MET` or `MISSED`.
- [x] No changelog fragment is added. This is a maintainer-only process change,
  and no release note ever announced the evaluation gate (tasks 177 and 178
  added none). Corrected during implementation.
- [x] `python3 scripts/check_repository.py`, the parallel unit suite, and `git
  diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `CONTRIBUTING.md` | Agent evaluations section and release procedure. |
| `scripts/release.py` | `agent_eval_reminder` and its three call sites. |
| `tests/test_release.py` | Reminder tests. |
| `docs/ADR_STOPS_AND_DENIALS.md` | Follow-up wording. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Dependencies

- **Depends on**: none
- **Blocks**: publication of 1.2.11 without an agent-evaluation run
