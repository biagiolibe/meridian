# Task 217 — Replace the author email in the plugin manifests

> **ID**: `217`
> **Category**: Configuration
> **Priority**: 🟢 P3
> **Estimate**: ~0.5h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` publish the
maintainer's personal email address. Contact goes through GitHub, and
security reports go through private vulnerability reporting. Replace the
email with the maintainer's GitHub profile URL.

## Acceptance Criteria

- [ ] `plugin.json` `author` and `marketplace.json` `owner` have `name` and
  `url: https://github.com/biagiolibe`, and no `email`. The handoff cites the
  Claude Code plugin and marketplace schema to show that `email` is optional
  for both.
- [ ] No tracked file contains a personal email address. Commit trailers and
  Git metadata are out of scope.
- [ ] The existing check that `plugin.json` and `VERSION` agree still passes.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `.claude-plugin/plugin.json` | Plugin manifest. |
| `.claude-plugin/marketplace.json` | Marketplace manifest. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Git author metadata and history.

## Dependencies

- **Depends on**: —
- **Blocks**: none
