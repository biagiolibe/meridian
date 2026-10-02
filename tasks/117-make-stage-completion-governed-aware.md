# Task 117 — Make `integrate stage` completion mode-aware for Governed SDD

> **ID**: `117`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up found while reviewing tasks 103 and 104 for Governed SDD

## Objective

Make the queue, plan, queue-link, and phase-archival steps of `integrate stage` work in a Governed SDD project, not only in Lean Delivery. `docs/TASK_CLOSURE_DESIGN.md` Decision 2 says the same closure step maps the integrated outcome to a Governed queue row; tasks 103 and 104 implemented only the Lean row shapes, and task 110 ships only text, capability blocks, and a migration, so no task makes the command itself mode-aware.

Authority: `docs/TASK_CLOSURE_DESIGN.md` (Decision 2, Decision 9).

## Acceptance Criteria

- [ ] `integrate stage` selects the row and plan handling from the project's workflow mode, read from the existing mode lock, and keeps the Lean behavior unchanged.
- [ ] In a Governed project, staging a task with `Review: NOT_REQUIRED` sets its queue row status to `ACCEPTED`, matches the Governed row shape (`| Order | ID | Priority | Status | Review | Dependencies | Task file |`), and rewrites the row's task-file link to the archived path when the task record was archived under `tasks/done/`.
- [ ] A Governed project without `PROJECT_PLAN.md` stages without a plan edit; a missing plan is not an error in that mode.
- [ ] An unrecognized or ambiguous Governed row keeps the existing `unrecognized completion row` block and leaves no lease or merge behind.
- [ ] Phase archival moves only fully accepted rows to `tasks/QUEUE_ARCHIVE.md` in the Governed table shape, and leaves the queue unchanged when any row in the section is open.
- [ ] A task whose `Review` is `REQUIRED` is not set to `ACCEPTED` by `stage`; the task records the decision and its reasoning in the handoff.
- [ ] Regression tests build a Governed fixture from `templates/workflows/governed-sdd` and cover: success, missing plan, unrecognized row, a closed phase, an open phase, and the archive link rewrite.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_apply_task_completion_rows`, `_relink_archived_task_row`, and the phase-archival step called by `stage_task_integration`. |
| `tests/test_task_worktree_isolation.py` | Lifecycle tests to extend with a Governed fixture. |
| `templates/workflows/governed-sdd/tasks/QUEUE.md` | Authoritative Governed row shape. |
| `docs/WORKTREE_LIFECYCLE.md` | Describes the staged edits; update for both modes. |

## Technical Context

Verified on 2026-10-02 against `main` at `7c131be`, with a Governed fixture copied from `templates/workflows/governed-sdd`, one task, a committed change on its task branch, and valid stage evidence:

- **Current behavior**: `stage_task_integration` fails with `[Errno 2] No such file or directory: .../PROJECT_PLAN.md`, because the Governed template ships no plan file. With a plan file added, it fails with `unrecognized completion row for task TASK-001 in .../tasks/QUEUE.md`, because the row pattern only matches the Lean shape `| \`[ ]\` | <id> |`. In both cases the stage is aborted cleanly: no merge in progress and no lease.
- **Desired behavior**: a Governed task integrates through the same command, with Governed statuses and row shape, under the same read-only-to-project-code boundary: the step is deterministic text editing of known row shapes by Meridian's own code and executes no project-provided command.

Review gates stay as Decision 9 defines them: a required independent review stops closure at C3 with `REVIEW_REQUIRED`, and the reviewer-integrator runs C6 to C10 after approval. This task does not change that gate; it only ensures that `stage` cannot mark a `REQUIRED` task accepted.

## Constraints and Considerations

- Keep the Lean path byte-for-byte unchanged in behavior; reuse the Lean tests as the regression guard.
- Do not add a new lifecycle state, role, or acceptance gate.
- All repository text is written in English.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Add one changelog fragment per `CONTRIBUTING.md` when the change is user-visible.

## Out of scope

Shipping the Governed closure rules and migration (task 110), the review-gate procedure text, and any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 103, 104
- **Blocks**: 110
