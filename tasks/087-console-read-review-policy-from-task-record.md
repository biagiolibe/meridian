# Task 087 — Read the review policy from the task record in the console

> **ID**: `087`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Developer report on F1-FIGURE-001 in the palimpsest project

## Objective

Make the console offer `Review <ID>` for a Governed SDD task in
`ready_for_review` whose task record declares `Review: REQUIRED`, even when the
queue table has no `Review` column. Make the detail pane's `Next action` line
agree with the launch decision and explain a refusal. Today the console shows
only "Awaiting review of the task branch" for such a task, so the developer
cannot see or launch the permitted review directive.

## Acceptance Criteria

- [ ] When the queue table has a `Review` column, its value is still used
  unchanged.
- [ ] When the queue table has no `Review` column, the console reads the
  `Review:` field from the header of the task record. For a task whose
  effective state comes from a branch, it reads the record from that branch.
- [ ] Only the values `REQUIRED` and `NOT REQUIRED` (case-sensitive, after
  trimming) are accepted. A missing, empty, or unrecognized value leaves the
  policy undeclared (`None`), and no review launch is offered.
- [ ] A Governed `ready_for_review` task with `Review: REQUIRED` in its record
  offers `Review <ID>` through `launch_command`, subject to every existing
  refusal (active writer, `MISMATCH`, record problem).
- [ ] The existing mismatch rule that compares `Review` with the queue status
  uses the same resolved value, so a record-declared `Review: REQUIRED` does not
  create a false mismatch and a record-declared `NOT REQUIRED` is treated as it
  is for a queue column.
- [ ] `Task.next_action` returns the review directive whenever `launch_command`
  returns one, as `If assigned: Review <ID>`, matching the `todo` case.
- [ ] When a task is `ready_for_review` and no launch is offered,
  `Next action` states the specific reason: active writer, `MISMATCH`, record
  problem, `Review: NOT REQUIRED`, or review policy not declared. The generic
  "Awaiting review of the task branch" remains only when no specific reason
  applies.
- [ ] Lean Delivery behavior is unchanged: `Review <ID>` for `ready_for_review`
  without reading any `Review` field.
- [ ] The console still never writes project files itself.

## Relevant Files

| File | Role |
|------|------|
| `scripts/console_workflow.py` | Queue parsing (`review` from the table column), effective-state mismatch rule that reads `row.review`. |
| `scripts/project_console.py` | `Task.launch_command`, `Task.next_action`, and `load_snapshot`, where `review=row.review` is assigned. |
| `tests/test_project_console.py` | Fixtures, queue parsing, effective-state, and launch tests (the only console test module). |

## Technical Context

- **Current behavior**: `review` comes only from the queue row, and only when
  the table has a `Review` column (`console_workflow.py`, `parse_queue`:
  `None` otherwise, with the comment that no policy is declared). A Governed
  `ready_for_review` task with `review is None` has no `launch_command`, and
  `next_action` returns the fixed text "Awaiting review of the task branch".
- **Observed case**: palimpsest `F1-FIGURE-001`. Its queue table has the columns
  `#`, `ID`, `Priority`, `Status`, `Dependencies`, `Estimate`. On the task
  branch its record header reads `Status: READY_FOR_REVIEW` and
  `Review: REQUIRED`. The console computed `review = None`,
  `launch_command = None`, `active_writer = False`, `mismatch = None`.
- **Desired behavior**: the record header is the fallback source of the review
  policy, and `next_action` is derived from the same decision as
  `launch_command`.
- Task 077 specified the launch for Governed `ready_for_review` with
  `Review: REQUIRED`; this task makes that rule reachable for projects that
  declare the policy in the task record.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Unit tests cover: queue column present (each value), column absent with
  `REQUIRED`, `NOT REQUIRED`, missing, empty, and unrecognized record values;
  the record read from the branch; the mismatch rule with a record-declared
  value; each `Next action` refusal reason; and unchanged Lean Delivery
  behavior.
- Evidence tier: the launch decision and `Next action` text are program-computed
  and asserted directly; no manual evidence is required.

## Out of scope

Adding a `Review` column to adopter queues, changing any lifecycle document, the
iTerm2 launch mechanism (Task 086), and `Accept` or `Run lifecycle` offers.

## Dependencies

- **Depends on**: 077
- **Blocks**: none
- **Note**: Task 086 also edits `scripts/project_console.py` (the AppleScript
  payload and launch messages). The edits are in different functions; integrate
  them one at a time.
