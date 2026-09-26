# Task 047 — Run the unit test suite in CI

> **ID**: `047`
> **Category**: Infrastructure
> **Priority**: 🔴 P1
> **Estimate**: ~30min
> **Assigned to**: unassigned
> **Session**: 2026-09-23 release-management gap review

## 🎯 Objective

`.github/workflows/validate.yml` only runs `python3 scripts/check_repository.py`.
The unit tests, which are the only proof of the upgrade, adoption, and
release-ledger guarantees added by tasks 015-019, never run in CI. Add them
so a regression cannot reach `main` or a tagged release unnoticed.

## 📋 Acceptance Criteria

- [ ] `validate.yml` runs `python3 -m unittest discover -s tests -v` after
      the repository check, on both `pull_request` and `push` to `main`.
- [ ] The workflow pins a concrete supported Python version (or a small
      matrix) instead of the floating `"3.x"`, and the chosen version(s)
      match what `README.md` or `CONTRIBUTING.md` states as supported. If no
      supported version is documented, document the chosen one.
- [ ] The suite passes on the CI runner (link a green run in the task
      completion note).
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass locally.

## 📁 Relevant Files

| File | Role |
|------|------|
| `.github/workflows/validate.yml` | CI workflow to extend. |
| `README.md` / `CONTRIBUTING.md` | Supported Python version statement. |

## 🧩 Technical Context

- **Current behavior**: CI validates repository structure, JSON, migrations,
  Bash syntax, links, and marker baselines, but no behavior.
- **Desired behavior**: CI also executes the full `unittest` suite, the same
  command listed under `## Commands` in `CLAUDE.md`.

## 🔨 Suggested Implementation

1. Add a second `run:` step with the unittest command.
2. Replace `python-version: "3.x"` with the documented minimum (and
   optionally the latest stable) version.
3. Push on a branch or PR and confirm the run is green; fix only
   environment-specific test failures (for example, a missing `git` identity
   in the runner), and record anything larger as a separate task.

## ⚠️ Constraints and Considerations

- Tests that depend on host tools (`git`, `bash`) must work on
  `ubuntu-latest` without secrets.
- Do not add third-party test dependencies; the suite is stdlib `unittest`.

## 🔗 Dependencies

- **Depends on**: 054
- **Blocks**: 050

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/047-run-unit-tests-in-ci.md)"$'\n\nExecute this task in the current project.'
```
