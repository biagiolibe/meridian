# Task 082 — Fix detail pane scrolling, Governed objective, and dependency order

> **ID**: `082`
> **Category**: Developer tooling
> **Priority**: 🔴 P1
> **Assigned to**: unassigned
> **Session**: Developer report of detail pane defects in the console

## Objective

Make the task detail reachable and useful at any terminal size, and show the
information the developer needs first. Reported defects:

1. The side detail pane is cut off after the terminal is resized, and the way
   to scroll it is not discoverable.
2. In the opened detail view, scrolling works only with PageUp and PageDown
   (fn+arrow on a Mac keyboard), one line at a time; arrows, `j`/`k`, and the
   mouse wheel do nothing. The developer confirmed the PageUp/PageDown path
   works.
3. Objective is always "Unavailable" for Governed SDD tasks.
4. Dependencies appear after the objective, so they are hidden when the
   console is short.

Code evidence (from reading, not from a reproduced run): `run_terminal`
increments `detail_offset` without a bound (clamping happens only inside
`_draw_detail`), so scrolling past the end builds a hidden offset that must be
undone one keypress at a time; in the opened detail view `j`, `k`, and the
arrow keys are ignored; PageUp and PageDown move one line; the mouse mask
accepts only left-button clicks, so the wheel does nothing; the `[`/`]` hint
appears only in the opened view. The side-pane cut-off after a resize is not
reproduced; the task must reproduce it first. `_section(text,
"Objective")` matches only a heading containing "Objective", while Governed SDD
task records, including Palimpsest's and the template's, use `## Goal`.

## Acceptance Criteria

- [ ] The detail offset is clamped to the scrollable range every frame and on
  every key, so it never exceeds the last visible position and one opposite
  keypress always moves back.
- [ ] In the opened detail view, `j`/`k`, the arrow keys, PageUp/PageDown, and
  the mouse wheel scroll it; PageUp and PageDown move by a page. The existing
  PageUp/PageDown path keeps working.
- [ ] The side pane scrolls with the same keys and the wheel when the pointer
  or focus is on it, without changing the selected task; the list keeps its own
  selection keys.
- [ ] The side-pane cut-off after a resize is reproduced in a test or recorded
  with exact steps before it is fixed.
- [ ] Resizing the terminal re-clamps the offset and re-wraps the text; no
  content is lost, and a "more above / more below" indicator shows whether
  content is hidden.
- [ ] A scroll hint is visible in every view that scrolls.
- [ ] The Objective section recognizes `Objective` and `Goal` headings, with or
  without a leading emoji, and shows the first match; when none exists the
  detail says which headings were searched instead of a bare "Unavailable".
- [ ] Acceptance criteria are read with the same tolerance for the heading
  names used by both workflows.
- [ ] Dependencies are the first content block under the task title and state,
  before objective and criteria, so they are visible at the smallest supported
  height; each shows its own state when the project snapshot knows it.
- [ ] The minimum-size message and the compact detail layout still apply, and
  the copy directive stays reachable by key and by click at any scroll
  position.
- [ ] Tests drive the detail renderer at several heights and widths, scroll to
  both ends, resize between frames, and assert the visible lines and the
  offset values read from the screen buffer.

## Relevant Files and Context

- `scripts/project_console.py`: `_detail_lines`, `_draw_detail`, `_section`,
  `run_terminal` (key and mouse handling, `curses.mousemask`), the footer hints.
- Governed task headings: `## Goal`, `## Acceptance criteria`,
  `## Validation` in `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md`
  and in Palimpsest's `docs/tasks/M37/M37-CAUSE-001.md`.
- The mouse wheel needs additional button masks; terminals that do not report
  them must still scroll by key.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Interactive PTY smoke check: open the detail, scroll to the end and back,
  resize while scrolled, in a Lean fixture and a Palimpsest-shaped fixture.

## Out of scope

Grouping (Task 081), column fitting (Task 080), launching agents (Task 077),
and changing task record formats.

## Dependencies

- **Depends on**: 076, 079
- **Blocks**: 077
