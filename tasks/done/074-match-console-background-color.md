# Task 074 — Use the terminal background in the project console

> **ID**: `074`
> **Category**: Developer tooling
> **Priority**: 🟢 P3
> **Assigned to**: Codex
> **Session**: Developer feedback on the integrated project console

## Objective

Let the interactive console use its terminal's default background, matching
the native terminal appearance in the Codex agent console reference.

## Acceptance Criteria

- [x] The interactive console uses the terminal's default background when
  default-color support is available, without changing its palette.
- [x] A color terminal without default-color support retains a dark fallback.
- [x] Existing status colors, selection, layout, and interaction remain intact.
- [x] The project baseline checks pass.

## Relevant Files and Context

- `scripts/project_console.py` defines the curses palette.
- The previous fixed 256-color background is color 233.
- Task 073 is integrated; this request changes only background handling.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Interactive terminal smoke check with a 256-color terminal.

## Dependencies

- **Depends on**: 073
- **Blocks**: none
