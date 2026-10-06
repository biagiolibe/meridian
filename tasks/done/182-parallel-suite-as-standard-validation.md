# Task 182 — Make the parallel test runner this repository's standard validation

> **ID**: `182`
> **Category**: Refactor
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Test suite cost review, 2026-10-06
> **Origin**: friction

## Objective

This repository's validation names the sequential suite,
`python3 -m unittest discover -s tests`, in `CLAUDE.md`, in task records, in
the FULL outcome of `.meridian/candidate-validation.json`, and in CI. On
2026-10-06 that run took 343 s for 848 tests, while
`python3 scripts/run_tests.py --parallel` ran the same 848 tests in 61 s with
the same coverage digest. A task runs the suite at least twice (task
validation and candidate validation), so roughly 10 minutes per task go to
waiting on a sequential run.

Make the parallel runner the standard validation command for this
repository, and keep the sequential run as the release gate and the manual
fallback.

## Acceptance Criteria

- [x] `CLAUDE.md`'s `## Commands` section (outside the `git-workflow` marker)
  names `python3 scripts/run_tests.py --parallel` as the test command. No
  capability-marker text changes.
- [x] `CONTRIBUTING.md` names the parallel run as the standard validation and
  the sequential `unittest discover` run as the release gate and the
  fallback for a host where the parallel run cannot start its workers. It no
  longer calls the sequential run "the canonical full test run" without that
  qualification.
- [x] `.meridian/candidate-validation.json` FULL lists `scripts/run_tests.py`
  in place of `unittest discover`, and an `advance` or `integrate finalize`
  with evidence from the parallel command is accepted. Evidence that names
  only `unittest discover` is still accepted, or the change states why not.
- [x] An agent in this repository can run `python3 scripts/run_tests.py
  --parallel` without a permission prompt: Codex through the tracked
  `.codex/rules/local.rules`, and Claude Code through the project allowlist
  that `meridian setup` writes, next to the existing
  `Bash(python3 -m unittest discover -s tests)` entry. The handoff states
  whether that allowlist entry also reaches other projects and why that is
  acceptable.
- [x] `.github/workflows/validate.yml` runs the parallel runner.
  `.github/workflows/release.yml` keeps the sequential
  `python3 -m unittest discover -s tests -v` run.
- [x] The Validation sections of open task records (`tasks/*.md`, not
  `tasks/done/`) name the parallel command. Archived records and handoffs
  are not edited.
- [x] The default candidate-validation proposal that `meridian setup` offers
  other projects is unchanged. This task changes only this repository's own
  validation, so it adds no migration and ships no template change.
- [x] The handoff records the wall time of the sequential and the parallel
  run on the same tree, with the `total` and `digest` the parallel run
  printed.
- [x] One changelog fragment is added per `CONTRIBUTING.md`, only if a
  shipped file changes; otherwise the handoff states that none is needed.
- [x] `python3 scripts/check_repository.py` and
  `python3 scripts/run_tests.py --parallel` pass.

## Relevant Files

| File | Role |
|------|------|
| `CLAUDE.md` | Project commands, outside the managed marker. |
| `CONTRIBUTING.md` | Test-run documentation. |
| `.meridian/candidate-validation.json` | FULL outcome fragments. |
| `.github/workflows/validate.yml` | CI validation. |
| `.github/workflows/release.yml` | Release gate; keeps the sequential run. |
| `.codex/rules/local.rules` | This repository's tracked Codex rules. |
| `scripts/run_tests.py` | Parallel runner; read only unless a gap is found. |
| `scripts/meridian.py` | Setup's Claude Code allowlist; `missing_candidate_validation_commands` and the setup proposal are read only. |
| `tasks/*.md` | Open task Validation sections. |

## Technical Context

- **Current behavior**: the sequential suite is the named validation
  everywhere. `run_tests.py --parallel` exists (tasks 112, 138, 179) and
  documents itself as an optional faster equivalent.
- **Desired behavior**: the parallel run is the default for agents and CI,
  and the sequential run stays as the release gate.
- Candidate evidence is matched by substring
  (`missing_candidate_validation_commands`), so the FULL fragment must be a
  substring of the parallel command.
- `run_tests.py --parallel` exits 1 when any shard fails or ends without a
  result, and prints `total` and `digest` for coverage.

<!-- TODO: add relevant code snippets and file paths -->

## Suggested Implementation

<!-- TODO: add relevant code snippets and file paths -->

## Constraints and Considerations

- Do not change `templates/`, managed marker text, or the consumer default in
  `proposed_candidate_validation_declaration`.
- Out of scope: shared test fixtures, splitting `tests/test_meridian_cli.py`,
  and removing tests.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/182-parallel-suite-as-standard-validation.md)"$'\n\nExecute this task in the current project.'
```
