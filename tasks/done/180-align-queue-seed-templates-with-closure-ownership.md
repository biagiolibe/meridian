# Task 180 — Align the queue seed templates with closure ownership

> **ID**: `180`
> **Category**: Refactor
> **Priority**: 🟢 P3
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Release planning after 1.2.9, 2026-10-05

## Objective

The queue files that `meridian init` seeds into new projects still describe
the pre-closure lifecycle. A new project therefore starts with a queue that
contradicts its own managed `git-workflow` text:

- `templates/base/tasks/QUEUE.md` tells agents to change `[ ]` to `[/]` when
  starting and to move rows to the archive by hand, while the managed text
  says a task branch never edits the queue and `integrate stage` applies queue
  status and phase archival on the merged candidate tree.
- `templates/workflows/governed-sdd/tasks/QUEUE.md` tells agents to "choose
  the highest-priority queued task", while both workflows forbid autonomous
  task selection, and its `Archiving` paragraph describes a manual move that
  `integrate stage` now performs.

This repository's own `tasks/QUEUE.md` and `tasks/QUEUE_TEMPLATE.md` were
corrected in commit `31f76e2`. Bring the seed templates into line.

Both files are bootstrap-time seed content, not managed or marker-protected
files (see migration `026-bound-the-queue-read`). The change reaches new
projects only; an adopted project's queue is never rewritten.

## Acceptance Criteria

- [x] `templates/base/tasks/QUEUE.md` states that the developer assigns a
  task, that task branches do not edit the queue, that a row keeps `[ ]` until
  `meridian worktree integrate stage` sets `[x]` on the merged candidate, that
  in-progress state is derived from the task branch, registered worktree, and
  unarchived record, that the task branch moves its own task file to
  `tasks/done/`, and that `integrate stage` archives a fully closed phase. The
  wording matches this repository's `tasks/QUEUE.md`.
- [x] `templates/workflows/governed-sdd/tasks/QUEUE.md` no longer instructs an
  agent to choose a task, and its `Archiving` paragraph states that
  `integrate stage` archives closed rows, without changing which statuses
  satisfy dependencies.
- [x] No managed file, capability marker, or marker baseline changes. If the
  release that ships this task has a migration, that migration may list the
  seed files as documentary only, following migration 026; this task adds no
  migration of its own.
- [x] Existing tests that read the seed queues pass unchanged, or are updated
  only where they assert the replaced sentences; `meridian init` into a
  temporary directory still produces a queue that `integrate stage` can parse.
- [x] One changelog fragment is added under `Changed`. It states that existing
  projects are not changed and may copy the new wording by hand.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/base/tasks/QUEUE.md` | Lean Delivery seed queue; changed. |
| `templates/workflows/governed-sdd/tasks/QUEUE.md` | Governed SDD seed queue; changed. |
| `tasks/QUEUE.md` | Reference wording; read only. |
| `migrations/026-bound-the-queue-read.json` | Precedent for seed-only queue changes; read only. |
| `changelog.d/180.md` | Changelog fragment; added. |

## Technical Context

- **Current behavior**: a newly initialized project's queue tells agents to
  edit queue status from a task branch, archive phases by hand, and, in
  Governed SDD, pick the next task.
- **Desired behavior**: the seed queue agrees with the managed `git-workflow`
  text and with what `integrate stage` does.

## Constraints and Considerations

- Release B per the plan in `tasks/QUEUE.md` (Phase 55): ships with 169 and
  176. It does not depend on them and needs no ordering against them.
- Do not touch `templates/workflows/*/PROJECT_WORKFLOW.md`, `AGENTS.md`, or
  `CLAUDE.md`; those are managed and belong to 169 and 176.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/180-align-queue-seed-templates-with-closure-ownership.md)"$'\n\nExecute this task in the current project.'
```
