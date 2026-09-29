# Task 067 — Enforce the adopter-facing release-notes contract

> **ID**: `067`
> **Category**: Infrastructure
> **Priority**: 🟢 P3
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 049 distribution and update design

## 🎯 Objective

Mechanically enforce Decision 5: the CHANGELOG section kind line agrees with the ledger and template-changing sections carry Upgrade notes, and the GitHub Release body reuses them.

## 📋 Acceptance Criteria

- [ ] The release script from task 050 fails when a section's kind line disagrees with `baselineChanged` in `releases/<version>.json`.
- [ ] A template-changing section without an `Upgrade notes` subsection fails validation.
- [ ] `CONTRIBUTING.md` release procedure describes both requirements.
- [ ] Unit tests cover both failures and both passing kinds.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## 📁 Relevant Files

`scripts/prepare_release.py`, `tests/`, `CONTRIBUTING.md`, `CHANGELOG.md`

## 🧩 Technical Context

Authority: `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`. Do not publish tags, releases, or marketplace listings unless the developer authorizes it separately.

## 🔗 Dependencies

- **Depends on**: 049, 050
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/067-enforce-release-notes-contract.md)"$'\n\nExecute this task in the current project.'
```
