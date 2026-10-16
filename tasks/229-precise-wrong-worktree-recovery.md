# Task 229 — Name the exact directory and command when a task command runs from the wrong place

> **ID**: `229`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~3h (split the current-directory removal out if the inventory is large)
> **Assigned to**: unassigned
> **Session**: Task 227 start stop, 2026-10-16
> **Origin**: friction

## Objective

Agents repeatedly stop with `BLOCKED WRONG_WORKTREE` at `meridian execution
start` (tasks 219 and 227) although the task worktree is ready. Three causes
combine:

- Two `--project` conventions coexist. `meridian worktree prepare`, `check`,
  `advance`, `integrate`, and `cleanup` take `--project <primary-checkout>`
  and run from the primary checkout. `meridian execution ...` and `meridian
  task close` take `--project <task-worktree>`, and `_execution_worktree`
  (`scripts/meridian.py`) also requires the current directory to equal that
  path. An agent that has just run `worktree prepare` from the primary checkout
  carries the wrong directory or the wrong `--project` into `execution start`.
- The stop detail, `execution --project must name the caller's task worktree`,
  names neither the current directory, the `--project` value received, nor the
  expected worktree path.
- The registered resume for `WRONG_WORKTREE` is always `meridian worktree
  prepare {task_id} --project {project} --format json`. For a directory
  mismatch with a ready worktree, that command is not the recovery, and the
  workflow forbids the agent to improvise one.

Remove the current-directory requirement where `--project` already names the
task's canonical worktree, make the remaining stop state the mismatch and the
exact recovery command, and document the two conventions in one place.

## Acceptance Criteria

- [ ] `meridian execution` subcommands and `meridian task close` no longer
  require the current directory to equal `--project` when `--project` names
  the task's canonical registered worktree. Run from any directory, including
  the primary checkout, they act on that worktree with the same result as when
  run from inside it. Every other check stays: the worktree is registered and
  canonical for that task, the branch and lifecycle state match, the worktree
  is clean where required, and no integration is active.
- [ ] Before the change, the handoff records an inventory of every place these
  commands depend on the current directory: `Path.cwd()`, relative paths,
  subprocesses or Git calls without an explicit directory or `-C`, and the
  host hooks they trigger. Each is converted to use the resolved worktree path,
  or recorded with the reason it is safe. The inventory states whether the
  current-directory check protected anything that the `--project` checks do
  not; if it did, the requirement stays for that case and the handoff names it.
- [ ] When `meridian execution` subcommands or `meridian task close` stop
  because `--project` does not name the task's canonical worktree (for example
  the primary checkout, another task's worktree, or a stale path), the detail
  names the current directory, the `--project` value, and the expected worktree
  path. The resume is the exact rerun of the
  same command with `--project` set to that worktree, for example
  `meridian execution start <TASK-ID> --project <task-worktree>`, with the
  original arguments preserved.
- [ ] When the task has no registered worktree, the resume stays `meridian
  worktree prepare <TASK-ID> --project <primary-checkout> --format json`.
- [ ] The rules for when to stop are unchanged: the agent still stops on the
  `BLOCKED` line. Because the resume names the exact command, a later explicit
  Resume needs no developer diagnosis. Apart from the current-directory
  requirement removed above, no safety check is relaxed.
- [ ] The resume template mechanism supports a per-call resume for
  `WRONG_WORKTREE` without changing the resume of other emitters of the same
  code. `capabilities/stop-codes-v1.json` stays consistent with the emitted
  text and its registry tests pass.
- [ ] `docs/WORKTREE_LIFECYCLE.md` contains one table listing, for each
  lifecycle command, where it may run and what `--project` names: primary
  checkout or task worktree. The Lean and Governed workflow text and the host skills
  link that table at the step that switches from `worktree prepare`/`check` to
  `execution start`. If managed text inside capability markers must change,
  the change ships with its migration, and the handoff records that the release
  becomes template-changing; prefer a link outside the markers.
- [ ] Tests cover:
  - `execution start`, `validate`, `deliver`, and `task close` run from the
    primary checkout and from an unrelated directory with `--project` set to
    the task worktree: each succeeds with the same state and commits as a run
    from inside the worktree;
  - `execution start` from the task worktree with `--project` set to the
    primary checkout;
  - `task close` with `--project` set to the primary checkout;
  - `--project` set to another task's worktree;
  - the unchanged resume when no worktree is registered.
  Each test asserts the detail fields and the exact resume command.
- [ ] A changelog fragment `changelog.d/229.md` records the fix under
  `Fixed`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_execution_worktree`, `execution_*`, `delivery_readiness`, `format_stop`, `stop_resume`, `task close`. |
| `capabilities/stop-codes-v1.json` | `WRONG_WORKTREE` registry entry and resume template. |
| `docs/WORKTREE_LIFECYCLE.md` | Command location table. |
| `PROJECT_WORKFLOW.md`, `templates/workflows/*/PROJECT_WORKFLOW.md`, `skills/*/SKILL.md` | Link to the table. |
| `tests/` | Stop detail and resume tests. |

## Technical Context

- `format_stop` already accepts an explicit `resume` argument that overrides
  the registered template; `_execution_worktree` does not pass one today.
- `_execution_worktree` raises `WRONG_WORKTREE` when
  `project_root != Path.cwd()`, before the canonical worktree inspection that
  already verifies registration, branch, and state.
- On 2026-10-16 the task 227 session ran `execution start` with `--project`
  set to the task worktree from the primary checkout and stopped. A recovery
  prompt that set `--project` to the primary checkout would also have
  stopped: both conventions are easy to confuse, including for the developer.

## Out of scope

Unifying the two `--project` conventions into one, so that every command
accepts the primary checkout. Changing when an agent must
stop. Tasks 227 and 228.

## Dependencies

- **Depends on**: none
- **Blocks**: none. Tasks 227 and 228 also edit `scripts/meridian.py`; run
  229 after them.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/229-precise-wrong-worktree-recovery.md)"$'\n\nExecute this task in the current project.'
```
