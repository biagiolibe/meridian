# Task 147 — Isolate setup CLI tests from the developer's real home directory

> **ID**: `147`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Full-suite run in the task-143 worktree, 2026-10-04

## Objective

`test_setup_cli_plans_then_applies_the_requested_task_identity`
(`tests/test_meridian_cli.py`, `WorktreeRootSetupTest`) passes in the primary
checkout and fails in every task worktree. The test overrides only
`XDG_CONFIG_HOME`; `meridian setup` then inspects the developer's real
`~/.agents/skills/<name>` links in `_framework_skill_links`. On this machine those
links point to the primary checkout's `skills/`, so when the suite runs from a
task worktree the framework root differs and setup reports
`BLOCKED: setup is blocked: points to <primary>/skills/meridian-lean-delivery
(expected <worktree>/skills/meridian-lean-delivery)`. The full-suite gate of every
task therefore fails for a reason unrelated to its diff. Make the setup tests
independent of the real home directory.

## Acceptance Criteria

- [ ] Every test in `WorktreeRootSetupTest`, and any other test that runs
  `meridian setup` or reads `~/.agents/skills`, sets `HOME` (and any other
  home-derived location setup reads) to its temporary directory, so no test reads
  or writes the developer's real home.
- [ ] The suite passes when run from a linked task worktree while the real
  `~/.agents/skills` links point to the primary checkout, and when run from the
  primary checkout; the handoff records both runs.
- [ ] No production behavior of `meridian setup` changes; no test is skipped,
  removed, or weakened.
- [ ] A regression test proves isolation: with a fake real-home skill link that
  points elsewhere, the setup tests still pass.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `tests/test_meridian_cli.py` | `WorktreeRootSetupTest` environment (`self.environment`, around line 4739) and the setup tests. |
| `scripts/meridian.py` | `_framework_skill_links`, read only to confirm which home-derived paths setup uses. |

## Technical Context

- Observed on 2026-10-04: in the task-143 worktree the full suite reported this
  failure among eight; it does not occur on `main` in the primary checkout.
- This blocks the full-suite gate of tasks 143–146 and any later task, so it
  should be integrated first.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- The same full suite run from a linked task worktree.
- `git diff --check`

## Out of scope

Changing setup's skill-link logic or messages, and the other test failures of the
task-143 worktree.

## Dependencies

- **Depends on**: —
- **Blocks**: none
