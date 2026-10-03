# Task 126 — Let the console resume an interrupted task

> **ID**: `126`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Console observation after an interrupted start, 2026-10-03

## Objective

A task that starts and is interrupted soon after (the agent session is closed,
crashes, or is stopped) is shown as working, and the console offers no action
that restarts it. Add an explicit, confirmed resume action for both Lean
Delivery and Governed SDD, without pretending the console knows whether an agent
is still running.

## Acceptance Criteria

- [ ] An `in_progress` task in either workflow that is not blocked by a
  mismatch or record problem offers a Resume action whose directive is
  `Proceed with <ID>`, launched in the primary checkout through the same
  Claude Code or Codex path as an ordinary launch.
- [ ] The Resume action never launches in one step: it first shows that the
  console cannot tell whether an agent is still active and asks for explicit
  confirmation.
- [ ] When the task worktree has uncommitted changes (`active_writer`), the
  warning says so and requires a second, distinct confirmation. The existing
  guard is otherwise unchanged: a plain launch of a `todo` task, `Review`, and
  `Address review` keep their rules.
- [ ] A task in the closing state (integration lease, staged or finalized merge,
  push pending, cleanup pending; task 124) does not offer Resume. It keeps
  showing its `closure-status` resume command, because restarting the
  implementation there would be wrong.
- [ ] The directive is the same string `[copy]` offers, so a manual paste and the
  launch behave identically.
- [ ] Resume is safe to repeat: documented and tested that `Proceed with` on an
  existing branch and worktree selects them without recreating state, preserves
  `started_at` (task 119), and never creates a second worktree.
- [ ] Governed SDD parity: the same rules apply to a Governed `IN_PROGRESS` task;
  a Governed task waiting for review keeps `Review <ID>` and is not offered
  Resume.
- [ ] Revalidation at launch time rechecks the task state, so a task that moved to
  closing or done between selection and confirmation is not launched.
- [ ] Tests cover: Resume offered for `in_progress` in both profiles; not offered
  for `todo`, closing, done, mismatch, or record problem; confirmation required;
  second confirmation when dirty; the directive equals the `[copy]` text; and
  stale-state revalidation.
- [ ] The console documentation explains Resume and states plainly that it is not
  a liveness check.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | `launch_command`, `_launch_request`, and the launch prompt. |
| `scripts/console_workflow.py` | Effective-state derivation. |
| `tests/test_project_console.py` | Launch eligibility and prompt tests. |
| `README.md` | Console actions documentation. |

## Technical Context

- `Task.launch_command` returns a directive only for a ready `todo` task, a
  task awaiting review, and a Governed task with requested changes. A Lean task
  whose branch and worktree exist is derived as `in_progress` and gets none, and
  `active_writer` (a dirty worktree) blocks every launch.
- The `active_writer` guard prevents two writers on one worktree, which the
  workflow forbids. The console has no process or heartbeat information, and
  process supervision is out of scope, so the confirmation and warning carry the
  risk instead of a liveness check.
- Before changing the guard, reproduce the current display for an interrupted
  task and record what `[copy]` offers in that state; this task was written from
  code reading.
- Reuse the launch path and its revalidation in `_launch_request`; do not add a
  second way to start an agent.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Detecting whether an agent is alive, a heartbeat or lease for implementation
work, killing or cleaning up a stale worktree, and changing `Proceed with`
semantics or the integration lifecycle.

## Dependencies

- **Depends on**: 124
- **Blocks**: none
