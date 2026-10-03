# Task 119 — Show task elapsed time and lifecycle progress in the project console

> **ID**: `119`
> **Category**: Feature
> **Priority**: 🟢 P3
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Console release-polish design discussion

## Objective

Make the project console show how long an active task has been open since its
canonical worktree was prepared, when its tracked task state last changed, and
which lifecycle gates remain before completion. The display must report
observable lifecycle facts rather than convert the task's original estimate
into an ETA or percentage.

## Acceptance Criteria

- [ ] When `meridian worktree prepare` creates a task branch and worktree, its
  lifecycle state records an ISO-8601 UTC `started_at` value. Repeating
  `prepare` for that existing task preserves the original value exactly.
- [ ] Existing lifecycle-state files without `started_at` remain valid and are
  not assigned a fabricated start time. The console reports elapsed time as
  unavailable for them and keeps working.
- [ ] For an active task with `started_at`, the interactive detail pane shows
  wall-clock elapsed time since preparation and updates it while the console is
  running without requiring a Git refresh.
- [ ] The detail pane keeps the existing last-change age as a separate value,
  so elapsed cycle time is not presented as active agent time.
- [ ] The console shows a deterministic lifecycle progression and the remaining
  gates using repository, worktree, validation-evidence, integration, remote,
  and cleanup facts already owned by Meridian. At minimum it distinguishes:
  ready, working, validation/evidence pending, candidate validation, push
  pending, cleanup pending, and done.
- [ ] Progress is expressed as the current phase and ordered remaining gates,
  never as a percentage, token count, time-to-completion estimate, or a value
  derived from the task record's `Estimate` field.
- [ ] Missing, stale, or unreadable lifecycle timing data degrades to
  `unavailable` without making the console stale or preventing task launch.
- [ ] `--once` output includes the same elapsed-time and lifecycle-progress
  facts for active tasks in a compact text form.
- [ ] Tests cover initial timestamp creation, preservation across repeated
  preparation, compatibility with legacy state, elapsed formatting, live
  elapsed updates, last-activity separation, and every displayed progress
  phase.
- [ ] The project-console documentation explains that elapsed time is wall-clock
  cycle time since worktree preparation and can include idle periods.
- [ ] Add one changelog fragment per `CONTRIBUTING.md` because the change is
  user-visible.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Preserve the lifecycle start timestamp during worktree preparation. |
| `scripts/project_console.py` | Read and render elapsed time, last activity, and lifecycle progress. |
| `tests/test_meridian_cli.py` | Worktree lifecycle-state compatibility and timestamp tests. |
| `tests/test_project_console.py` | Console timing and progress rendering tests. |
| `docs/WORKTREE_LIFECYCLE.md` | Document the lifecycle timestamp and its meaning. |
| `README.md` | Document the console fields. |

## Technical Context

- The version-1 worktree lifecycle state currently records task, branch,
  worktree, project, base, and task commits, but no creation timestamp.
- The console already computes the age of the last committed task-record change;
  that is activity recency, not total elapsed cycle time.
- `meridian worktree closure-status` already derives closure steps and resume
  actions. Reuse its authoritative facts or a shared read-only derivation
  instead of creating a second lifecycle interpretation in the renderer.
- Elapsed time starts at canonical worktree preparation. It is intentionally
  wall-clock time and may include pauses, waiting, or an agent that is no longer
  running.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Provider usage limits, token accounting, process supervision, active-agent
CPU time, parsing Claude or Codex private logs or databases, the task record's
original estimate, percentage completion, and predicted time remaining.

## Dependencies

- **Depends on**: 118
- **Blocks**: none
