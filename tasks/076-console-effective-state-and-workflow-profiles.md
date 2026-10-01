# Task 076 — Show effective task state across workflow modes in the console

> **ID**: `076`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: Developer request for agent launch from the project console

## Objective

Make the read-only project console report each task's real state in both
supported workflow modes. Today it reads only the primary checkout's queue and
rejects every project that is not `LEAN_DELIVERY`, so a task reserved or
advanced on its task branch still looks unstarted, and Governed SDD projects
cannot be opened at all.

## Acceptance Criteria

- [ ] The console selects a workflow profile from `PROJECT_WORKFLOW.md` using
  the same mode lock as `detect_mode` in `scripts/meridian.py`
  (`LEAN_DELIVERY` or `GOVERNED_SDD`); a missing, unknown, or doubly-locked
  mode is an explicit console error.
- [ ] A profile defines queue parsing, the status vocabulary, the terminal
  state that satisfies a dependency, and the derived phase. The list, detail,
  filter, and one-shot views consume only the normalized phases `todo`,
  `in_progress`, `ready_for_review`, and `done`.
- [ ] Lean Delivery keeps its current queue format and behavior for tasks with
  no task branch.
- [ ] Governed SDD parses the single queue table
  (`Order|ID|Priority|Status|Review|Dependencies|Task file`) and maps
  `QUEUED`, `IN_PROGRESS`, `READY_FOR_REVIEW`, and `ACCEPTED`. Dependencies are
  satisfied only by `ACCEPTED`; the `ANSWERED` rule for spike tasks follows
  `PROJECT_WORKFLOW.md`. An unrecognized status is an explicit error, never a
  guess.
- [ ] For a task whose branch exists, the console reads the queue row, task
  record, handoff, and (Governed SDD) `tasks/reviews/<ID>.md` from that branch
  without touching the worktree and without writing, locking, or fetching.
- [ ] The branch name is obtained from the shared task-identity resolver, not
  rebuilt locally, so `milestone` identity projects resolve correctly.
- [ ] When the branch state is ahead of the primary checkout's state it is
  shown as the effective state with its source. When the two disagree in a way
  the lifecycle does not produce, the task shows a distinct `MISMATCH` state
  naming both values and offers no launch directive.
- [ ] Lean Delivery has no `READY_FOR_REVIEW` status. A Lean task is shown as
  ready for review only when all hold: its branch queue row is `[x]`, its
  handoff reports `Status: DONE`, the branch is ahead of `main`, and its
  worktree is clean. The console never writes this state anywhere.
- [ ] A Governed task is shown as ready for review only when the task record
  and the queue row both say `READY_FOR_REVIEW` and `Review: REQUIRED`;
  disagreement between them is `MISMATCH`.
- [ ] A Governed task whose latest review attempt is `CHANGES_REQUESTED` is
  shown as in progress with a "changes requested" marker.
- [ ] A task with uncommitted worktree changes shows an "active writer"
  indicator. The indicator is advisory and never changes the lifecycle state.
- [ ] Task 075's `meridian console` command, `--project` option, and refresh
  interval are unchanged.

## Relevant Files and Context

- `scripts/project_console.py`: `STATUS`, `_queue_rows`, `load_snapshot`,
  `Task`, `_state_label`, the filter helpers, and `one_shot`.
- `scripts/meridian.py`: `detect_mode`, `resolve_project_locations`,
  `resolve_task_identity`, and the worktree path and check commands.
- Governed queue and review formats:
  `templates/workflows/governed-sdd/tasks/QUEUE.md`,
  `templates/workflows/governed-sdd/docs/REVIEW_RECORD_TEMPLATE.md`
  (`## Attempt <N> — <CHANGES_REQUESTED | APPROVE | BLOCKED>`), and
  `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`.
- Lifecycle edits for both modes are committed on the task branch, so the
  primary checkout lags until integration.
- `PROJECT_WORKFLOW.md` forbids Governed states in Lean projects; the
  ready-for-review state here is a display derivation, not a lifecycle state.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- New tests build throwaway Git repositories for each mode with: a task with
  no branch, a reserved task, a completed task, a mismatch, a Governed
  `READY_FOR_REVIEW` task, a `CHANGES_REQUESTED` review, a dirty worktree, and
  a `milestone` identity project.
- Interactive PTY smoke check against one Lean and one Governed fixture.

## Out of scope

Launching any agent or process (Task 077), changing the lifecycle or any
workflow document, and writing to the project or its worktrees.

## Dependencies

- **Depends on**: 075
- **Blocks**: 077
