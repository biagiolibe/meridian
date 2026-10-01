# Task 080 — Fit the task ID column to the IDs in the console list

> **ID**: `080`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: Developer report that Governed SDD task IDs are truncated in the console list

## Objective

Show complete task IDs in the console task list. `_draw_list` in
`scripts/project_console.py` gives the ID a fixed 5-column field starting at
column 3 and starts the title at column 9. Lean Delivery IDs such as `075`
fit, but Governed SDD IDs do not: `TASK-001` has 8 characters, `M37-CAUSE-001`
has 13, and the longest ID in Palimpsest, `M20-EVENT-002-CORR`, has 18.

## Acceptance Criteria

- [ ] The ID column width is computed from the longest task ID in the full open
  task set, not from the currently filtered rows, so it does not change when the
  status filter or search changes.
- [ ] The width is capped at one third of the list pane. An ID longer than the
  cap is shown with a trailing `…` in the list and in full in the task detail.
- [ ] The title starts after the ID column and receives the remaining width,
  keeping the existing status and updated columns; the title never overlaps the
  ID or status columns, and never receives less than its current minimum.
- [ ] The "Tasks" header, the selection marker, and the phase headings stay
  aligned with the computed column.
- [ ] Lean Delivery lists with 3-character IDs look the same as before, except
  for the column width becoming the actual ID width.
- [ ] A layout test asserts the rendered column positions for IDs of 3, 8, 13,
  and 18 characters, for a pane narrower than the capped width, and for a
  filter change.
- [ ] Every other place that assumes the old 5 and 9 column positions is found
  and either updated or recorded in the handoff as unaffected, including the
  detail pane, the header, mouse hit-testing, and the one-shot output.
- [ ] The full task ID is available in the detail view, the copy directive, and
  the one-shot output.
- [ ] No snapshot, refresh, or state behavior changes.

## Relevant Files and Context

- `scripts/project_console.py`: `_draw_list` (ID at column 3 with width 5,
  title at column 9, `title_width` derived from fixed offsets), `_draw_detail`,
  `_draw_header`, `_tab_at`, and `one_shot`.
- Evidence: Palimpsest IDs reach 18 characters and most exceed 5.
- The status and updated columns are right-aligned from the pane edge and must
  keep their current meaning.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Interactive PTY smoke check at a wide and a narrow terminal size against a
  Lean fixture and a Palimpsest-shaped Governed fixture; rendered positions are
  read back from the screen buffer, not judged visually.

## Out of scope

Launching agents (Task 077), record resolution (Task 079), refresh behavior
(Task 078), colors, and any change to workflow parsing.

## Dependencies

- **Depends on**: 076
- **Blocks**: 077
