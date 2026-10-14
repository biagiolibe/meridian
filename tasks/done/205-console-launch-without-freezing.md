# Task 205 — Launch an agent from the console without freezing the interface

> **ID**: `205`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: GitHub issue #13 triage, 2026-10-13
> **Origin**: friction

## Objective

Fix the user-visible part of [issue #13](https://github.com/biagiolibe/meridian/issues/13):
pressing `1` (Claude Code) or `2` (Codex) freezes the console for seconds and
shows nothing. The key handler calls `_launch_selected`
(`scripts/project_console.py`), which runs two blocking steps on the UI
thread:
- a full `state.refresh()`, which takes about 2 s warm on Meridian and 4 s on
  consumer project A, and up to 60 s cold;
- `osascript`, with a 10 s timeout.

The notice appears only after both return.

## Acceptance Criteria

- [x] Pressing `1` or `2` redraws a `Launching…` notice for the selected task
  at once. The key handler returns without calling `load_snapshot` or
  `osascript` synchronously; a test asserts it with a fixture whose snapshot
  takes more than 1 s.
- [x] Before launching, the console revalidates only the selected task: its
  launch directive, resume state, and active-writer state. It does not load a
  full project snapshot. The revalidation and `osascript` run off the UI
  thread, with at most one launch in flight. A second key press while a launch
  is pending is refused with a notice.
- [x] When the work finishes, the console shows success, or a failure with its
  reason. A launch is still refused when the directive, resume state, or
  active-writer state changed since it was displayed. The existing
  revalidation tests keep passing.
- [x] A failure or timeout of `osascript` or of a Git call during the launch
  never freezes or crashes the console.
- [x] One changelog fragment states the fix under `Fixed`; this is a CLI-only
  change.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | Key handler, `_launch_selected`, `ConsoleState`, `start_refresh`. |
| `tests/test_project_console.py` | Launch tests. |

## Technical Context

- The periodic refresh already runs in a background thread (`start_refresh`).
  Reuse that pattern rather than adding a second threading model.
- Snapshot cost is reduced separately by task 206. This task removes the
  freeze even when a snapshot stays slow.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Making `load_snapshot` cheaper (task 206), and changing the iTerm2 launch
command.

## Dependencies

- **Depends on**: —
- **Blocks**: 206
