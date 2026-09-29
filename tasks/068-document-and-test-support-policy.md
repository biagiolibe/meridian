# Task 068 — Document and test the upgrade support policy

> **ID**: `068`
> **Category**: Documentation
> **Priority**: 🟢 P3
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 049 distribution and update design

## 🎯 Objective

State the Decision 6 support window in README and CONTRIBUTING and prove it with a test.

## 📋 Acceptance Criteria

- [ ] A test upgrades a project from the oldest packaged baseline (`1.0.0`) to the current release in one `upgrade --apply`, or the existing equivalent test is identified and cited.
- [ ] README and CONTRIBUTING state the window, skip-release support, newest-only fixes, and the unsupported cases.
- [ ] No CLI behavior change; any discovered gap is reported as a new task.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## 📁 Relevant Files

`tests/`, `README.md`, `CONTRIBUTING.md`

## 🧩 Technical Context

Authority: `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`. Do not publish tags, releases, or marketplace listings unless the developer authorizes it separately.

## 🔗 Dependencies

- **Depends on**: 049
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/068-document-and-test-support-policy.md)"$'\n\nExecute this task in the current project.'
```
