# Task 188 — Raise Meridian's minimum supported Python version to 3.12

> **ID**: `188`
> **Category**: Maintenance
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Python version request, 2026-10-08
> **Origin**: maintenance

## Objective

Make Python 3.12 the documented and CI-tested minimum for Meridian's own
maintenance commands, CLI launcher, and test suite. This aligns the project
baseline with the `unittest --durations` measurement required by Task 183.

## Acceptance Criteria

- [x] The root README and contributor guidance state Python 3.12 or later as
  the minimum. The README gives a usable macOS Homebrew installation and PATH
  check without altering a user's existing Python installation.
- [x] Validation and release GitHub Actions use Python 3.12; the validation
  workflow still runs its repository, profile, audit, and parallel-suite gates.
- [x] Current host-capability guidance names Python 3.12 or later for the
  unverified Codex launcher probe. Historical probe observations remain intact.
- [x] A repository search finds no current claim that Python 3.11 is the
  supported minimum. Historical task and handoff records are unchanged.
- [x] `python3 scripts/check_repository.py` and the full parallel suite pass.
  The GitHub Actions validation run on the task commit passes under Python 3.12
  before integration.
- [x] Add one changelog fragment for the support-policy change according to
  `CONTRIBUTING.md`.

## Relevant Files

| File | Role |
|------|------|
| `README.md` | User and contributor minimum-version guidance. |
| `CONTRIBUTING.md` | Contributor prerequisites. |
| `.github/workflows/validate.yml` | Minimum-version validation gate. |
| `.github/workflows/release.yml` | Release validation interpreter. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Current launcher probe requirement. |
| `changelog.d/` | Support-policy release note. |

## Technical Context

- **Current behavior**: README and both workflows state Python 3.11, while
  `unittest --durations` is available only in Python 3.12 or later.
- **Desired behavior**: documentation and CI agree on Python 3.12 as the
  earliest supported interpreter.
- This repository's `templates/base/README.md` is a stack-agnostic project
  template and makes no Python-version claim.

## Constraints and Considerations

- Do not rewrite historical release, task, or probe evidence.
- Do not modify Task 183's active worktree or its uncommitted changes.
- Installing Python on a developer's Mac is outside repository scope; provide
  instructions rather than altering their machine.
- Do not create a release or move a tag.

## Dependencies

- **Depends on**: none
- **Blocks**: none
