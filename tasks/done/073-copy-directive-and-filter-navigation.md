# Task 073 — Make directives copyable and restore All filter navigation

> **ID**: `073`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Session**: Developer feedback on the interactive console

## Objective

Make a ready task's launch directive easy to copy from the terminal console
and make `All` straightforward to reach with Tab.

## Acceptance Criteria

- [x] A ready task shows `Proceed with <ID>` as the `Next directive` command.
  Clicking the visible command copies exactly that text to the system clipboard
  and shows short success or failure feedback. Other task states are not
  presented as copyable launch commands.
- [x] `c` copies the selected ready task's launch command when terminal mouse
  events are unavailable. No directive is executed or sent to an agent.
- [x] Tab and Shift+Tab cycle `All` and populated status filters in both
  directions, including returning to `All` after the last populated filter.
  Visible empty filters can still be selected by clicking their tabs.
- [x] Narrow and wide layouts, keyboard navigation, search, refresh, stale
  state, and `--once` continue to work. No new package or network use is added.
- [x] Unit tests and interactive terminal smoke checks cover filter wrap,
  click hit testing, clipboard success and failure, and the project baseline
  checks pass.

## Relevant Files and Context

- `scripts/project_console.py` owns the curses renderer and task directives.
- `tests/test_project_console.py` covers snapshots and renderer helpers.
- Task 072 is integrated and defines the compact console layout.
- Python curses documents mouse event reporting through `mousemask`,
  `KEY_MOUSE`, and `getmouse`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Interactive narrow and wide terminal smoke checks, including a mouse click.

## Dependencies

- **Depends on**: 072
- **Blocks**: none
