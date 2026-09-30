# Task 071 — Apply the compact dark shell design to the project console

> **ID**: `071`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Session**: Approved project console visual design

## Objective

Replace the first console's cramped, terminal-default presentation with the
approved compact shell interface. Keep the existing read-only project monitor
and make its state easy to scan in a dark terminal.

## Acceptance Criteria

- [x] The terminal application explicitly paints a very dark background and
  legible foreground rather than inheriting a light terminal theme. Ready,
  in-progress, blocked, unknown, and stale states have distinct colors and
  readable text labels; monochrome terminals remain usable.
- [x] In a wide terminal, a compact header and status filters sit above the
  task list, with task details in a right pane. The selected row is clearly
  highlighted. The header above the filters is slightly taller than the
  filters and task rows, matching the approved design.
- [x] A narrow terminal uses a full-width list and opens task details with
  Enter. Task titles and detail text do not overlap or break unexpectedly.
- [x] The list retains task ID, title, state, and available last-change
  information. The details retain objective, acceptance criteria,
  dependencies, worktree, and a concise `Next directive`.
- [x] Search, keyboard navigation, manual refresh, two-second automatic
  refresh, stale-state behavior, quit, and `--once` continue to work. No new
  package, public CLI command, network access, persistent write, or agent
  control is introduced.
- [x] Interactive smoke checks cover narrow and wide terminals, including
  colors, filters, detail navigation, search, refresh, and quit. Repository
  checks and the unit test suite pass.

## Relevant Files and Context

- `scripts/project_console.py` owns the current curses renderer and snapshot.
- `tests/test_project_console.py` covers the snapshot and one-shot output.
- The approved visual design is a dark, compact, two-pane shell presentation
  with a full-width list fallback for narrow terminals.
- Task 070 established read-only behavior and local refresh; preserve those
  contracts.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Interactive narrow and wide terminal smoke checks.

## Dependencies

- **Depends on**: 070
- **Blocks**: none
