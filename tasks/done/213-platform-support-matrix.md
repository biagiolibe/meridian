# Task 213 — Declare supported platforms and validate on macOS in CI

> **ID**: `213`
> **Category**: CI
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

Python 3.12 or later is required, CI runs only on `ubuntu-latest`, and the
console's agent launch works only on macOS with iTerm2. Nowhere does the
project state which platforms it supports. Declare a support matrix, and back
each "supported" claim with CI.

## Acceptance Criteria

- [x] The README has one support matrix covering OS (macOS, Linux, Windows),
  Python, Git, hosts (Claude Code, Codex), and console features, with each
  cell marked supported, best-effort, or unsupported.
- [x] Every OS marked supported runs `python3 scripts/run_tests.py
  --parallel` and `python3 scripts/check_repository.py` in
  `.github/workflows/validate.yml`. A macOS job is added. The Python minimum
  stays 3.12.
- [x] A test that cannot run on an OS is skipped by the test itself with a
  named reason, never by the workflow file.
- [x] Windows is marked unsupported or best-effort unless a CI job proves it.
- [x] One changelog fragment states the matrix under `Documentation`.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass locally. The CI run of the task
  commit passes on every job.

## Relevant Files

| File | Role |
|------|------|
| `.github/workflows/validate.yml` | CI jobs. |
| `README.md` | Support matrix. |
| `tests/` | OS-specific skips, if any. |

## Technical Context

- CI evidence for the task commit needs one `git push origin task-213`, which
  `Proceed with` authorizes for `T1_CI` validation.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`
- CI run of the task commit

## Out of scope

Supporting Windows, changing the release workflow, and console launch on
terminals other than iTerm2.

## Dependencies

- **Depends on**: —
- **Blocks**: none

## Completion

Implemented in `a51bf3fad4304c60ef26d5e8bcdb4acb5bfd4c19`. Local repository
checks, all 1,027 tests, and whitespace validation passed. CI run
[38651926265](https://github.com/biagiolibe/meridian/actions/runs/38651926265)
passed on both Ubuntu and macOS with Python 3.12. Each CI job ran 1,027 tests
with six tool-dependent skips declared by the tests. See `../handoffs/213.md`
for the validation evidence and scope.
