# Task 081 — Group console tasks by their queue headings in Governed SDD projects

> **ID**: `081`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: Developer report that Governed SDD tasks are not grouped by milestone

## Objective

Group tasks in the console list by the heading that introduces their queue
table, whatever its level. `parse_queue` in `scripts/console_workflow.py`
records a section only for `### ` headings. Palimpsest's queue
(`docs/TASK_QUEUE.md`) introduces each milestone with `## M37 Queue — Reactions,
First Layer` and has 41 `##` headings and no `###`, so every task has an empty
section and the list is flat.

## Acceptance Criteria

- [ ] A task's group is the nearest heading above its table, at any level from
  `##` to `######`. When headings of two levels enclose a table, both are kept
  and shown in file order, outer first.
- [ ] A heading with no queue table beneath it produces no group and no empty
  heading line (for example `## Rules` and `## Priority` in Palimpsest).
- [ ] Group labels are cleaned for display: a trailing `Queue` word and its
  separator are dropped, so `M37 Queue — Reactions, First Layer` shows as
  `M37 — Reactions, First Layer`. The raw heading is kept for matching.
- [ ] Row order inside a group, and group order, follow the file.
- [ ] A group whose tasks are all terminal does not appear in the open-task
  list; the done count is unaffected.
- [ ] Search matches the group label as well as the ID and title.
- [ ] Lean Delivery `### Phase N — …` lists look and behave as before.
- [ ] Tasks read from a task branch use the same grouping as the primary
  checkout, so a task does not jump groups when its effective state changes.
- [ ] A Palimpsest-shaped fixture (many `##` milestone headings, no `###`,
  non-table `##` headings, an `F0` track) and a two-level fixture pass, with
  assertions on the rendered list, not only the parsed rows.

## Relevant Files and Context

- `scripts/console_workflow.py`: `parse_queue` (the `### ` check) and
  `QueueRow.section`.
- `scripts/project_console.py`: `Task.phase`, the phase heading rendering in
  `_draw_list`, `_visible_tasks`.
- Evidence: Palimpsest has milestones `M01`…`M37` and the `F0` and `F1`
  presentation tracks as `##` sections. Its queue has no column and no heading
  below milestone level, and no `.meridian/task-identity.json`, so a milestone
  cannot be derived from IDs.
- Tasks 076 and 079 were written against this repository's and the template's
  queue formats; this task removes the remaining heading-level assumption.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Run against a local copy of Palimpsest or the equivalent fixture and record
  the command, the group count, and the number of rows per group.

## Out of scope

The detail pane (Task 082), column layout (Task 080), launch (Task 077), and
inferring groups from task IDs.

## Dependencies

- **Depends on**: 076
- **Blocks**: 077
