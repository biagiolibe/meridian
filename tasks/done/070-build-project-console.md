# Task 070 — Build a read-only project console with automatic local refresh

> **ID**: `070`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Session**: Project console design conversation

## Objective

Provide an interactive terminal dashboard that the project owner can keep open
while directing agents elsewhere. It reports verified local project state and
never issues agent instructions or mutates the project.

## Acceptance Criteria

- [x] A standalone Python standard-library console starts from a supplied
  project path without adding a public `meridian` command or dependency.
- [x] It shows every non-terminal canonical queue task, its title, dependency
  readiness, and the selected task's objective, acceptance criteria, worktree,
  and permitted next directive when available. It shows the current checkout
  and Git status. It does not autonomously select or start a task.
- [x] It refreshes local state automatically every two seconds by default,
  supports a configurable interval and manual refresh, and shows the last
  successful refresh time. Failed refreshes keep the last valid snapshot and
  visibly mark it stale.
- [x] Keyboard navigation, search, help, and quit work in a terminal. A
  non-interactive one-shot view is available for accessibility and automation.
- [x] The console performs no Git mutations, network requests, agent control,
  or persistent writes. It does not claim to know agent activity.
- [x] Tests cover queue/dependency parsing, snapshot error behavior, and the
  one-shot output. `python3 scripts/check_repository.py` and the unit test
  suite pass; an interactive smoke check is recorded.

## Relevant Files and Context

- `tasks/QUEUE.md` is the operational queue; `PROJECT_PLAN.md` is the delivery
  record. The queue archive supplies completed dependency states.
- `scripts/meridian.py` already resolves canonical project locations and task
  identity. `hooks/queue-briefing.sh` supplies a compact but incomplete Lean
  queue summary. Avoid presenting queue order as autonomous task selection.
- Add the standalone console and targeted tests without changing existing CLI
  behavior. Missing or ambiguous queue data must be reported, not guessed.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- One-shot output against this repository and an interactive terminal smoke
  check for navigation, refresh, and quit.

## Dependencies

- **Depends on**: 063
- **Blocks**: none
