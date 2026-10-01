# Task 074 — Match the console background color

> **ID**: `074`
> **Category**: Developer tooling
> **Priority**: 🟢 P3
> **Assigned to**: Codex
> **Session**: Developer feedback on the integrated project console

## Objective

Set the interactive terminal console's main background to `#1e1e2e` to match
the approved mockup.

## Acceptance Criteria

- [ ] The interactive console uses `#1e1e2e` for its main surface when the
  terminal supports palette color changes or xterm palette controls.
- [ ] The console restores any changed terminal palette color on exit.
- [ ] Existing status colors, selection, layout, and interaction remain intact.
- [ ] The project baseline checks pass.

## Relevant Files and Context

- `scripts/project_console.py` defines the curses palette.
- Color 233 is currently used for the main surface in 256-color terminals.
- Task 073 is integrated; this request changes only the background color.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Interactive terminal smoke check with a 256-color terminal.

## Dependencies

- **Depends on**: 073
- **Blocks**: none
