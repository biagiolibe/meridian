# Task 066 — Add `meridian self-check --check-latest`

> **ID**: `066`
> **Category**: Feature
> **Priority**: 🟢 P3
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 049 distribution and update design

## 🎯 Objective

Implement the opt-in update-discovery command specified in Decision 3 of `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`.

## 📋 Acceptance Criteria

- [ ] Network access happens only with `--check-latest`; no other command gains a network dependency.
- [ ] Standard library only, short timeout, no credentials, no state or cache file.
- [ ] Offline, rate-limited, or malformed responses report `UNKNOWN` with a reason and a documented exit code distinct from update-available.
- [ ] Unit tests cover up-to-date, update-available, offline, and malformed-response paths without real network access.
- [ ] Governed SDD is used for this task (new network dependency and public CLI surface).
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## 📁 Relevant Files

`scripts/meridian.py`, `bin/meridian`, `tests/`, `README.md`, `CHANGELOG.md`

## 🧩 Technical Context

Authority: `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`. Do not publish tags, releases, or marketplace listings unless the developer authorizes it separately.

## 🔗 Dependencies

- **Depends on**: 049, 050, 065
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/066-add-self-check-latest-command.md)"$'\n\nExecute this task in the current project.'
```
