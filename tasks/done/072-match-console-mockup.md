# Task 072 — Match the approved console mockup in the terminal renderer

> **ID**: `072`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Session**: Developer feedback on the integrated task 071 console

## Objective

Correct the visual differences between the integrated terminal console and the
approved compact shell mockup. Keep the existing read-only data and controls.

## Acceptance Criteria

- [x] The top line places the title, project, and branch on the left and the
  Git summary and refresh age at the right edge in wide terminals.
- [x] The active status tab, including `All` on launch, has an obvious selected
  treatment with a blue underline; the filter shortcut hint sits at the right
  side of the tab row when space permits.
- [x] Header, list, phase, row, footer, and right-pane spacing follow the
  approved compact shell mockup, including a roughly 68/32 wide split.
- [x] The right pane shows the selected task title and state, objective,
  dependencies, a divider, and `Next directive`; it does not show acceptance
  criteria. The narrow full detail view follows the same content hierarchy.
- [x] List ID, title, state, updated age, filters, search, navigation, refresh,
  stale-state behavior, and one-shot output continue to work. No new package,
  network access, persistent write, or agent control is introduced.
- [x] Wide and narrow interactive smoke checks and the repository baseline
  checks pass.

## Relevant Files and Context

- `scripts/project_console.py` owns the curses renderer and local snapshot.
- `tests/test_project_console.py` covers snapshot and one-shot behavior.
- Approved visual reference: the compact shell mockup from the design session.
- Task 071 is integrated; this task corrects the developer-reported mismatch.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Interactive narrow and wide terminal smoke checks.

## Dependencies

- **Depends on**: 071
- **Blocks**: none
