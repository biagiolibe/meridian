# Task 219 — Close a Lean task with one command

> **ID**: `219`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 209 closure stop, 2026-10-14
> **Origin**: friction

## Objective

Lean closure is two manual steps that must run in order:
`meridian task transition <TASK-ID> DONE`, then archiving the record. Task 209
skipped the first step, and integration stopped with `TASK_STATE_MISSING`.
Replace the pair with one command that cannot leave a task archived without
its state, and make the managed closure text name that command.

## Acceptance Criteria

- [ ] `meridian task close <TASK-ID> [--project <path>] [--format json]` runs
  in the task worktree of a Lean Delivery project. It checks in this order:
  - the worktree is the task's canonical worktree and is clean;
  - the task record is unarchived;
  - the handoff exists and is committed;
  - the transition to `DONE` is allowed by the Lean state machine.
  Each failed check stops with a registered stop code and changes nothing.
- [ ] On success it does two things, then stages the record move and the
  state file, so the agent commits them together with its completion records:
  - writes `.meridian/tasks/<TASK-ID>.json` through the same code path as
    `task transition`, so the state is identical;
  - moves the record to its exact archive path under `tasks/done/`.
  The command does not commit.
- [ ] In a Governed SDD project, or for a task already `DONE`, the command
  stops with a registered stop code and a message that names the correct
  command.
- [ ] The managed Lean closure text in the `git-workflow` capability names
  `meridian task close <TASK-ID>` instead of the transition-then-archive pair.
  It is updated in:
  - `templates/workflows/lean-delivery/` (`AGENTS.md`, `CLAUDE.md`,
    `PROJECT_WORKFLOW.md`);
  - both Lean skills under `skills/`;
  - this repository's managed copies.
  The capability version advances, and a new migration with marker baselines
  carries the change, following `migrations/README.md` and `CONTRIBUTING.md`.
- [ ] `docs/PUBLIC_SURFACE.md`, if task 210 has landed, lists `task close` as
  Stable.
- [ ] Tests cover success, each refusal, the identity of the written state
  with `task transition`'s, and the upgrade of a pristine `1.2.15` Lean project
  through the new migration.
- [ ] One changelog fragment states the command under `Added`, and the
  template change under `Upgrade notes`, with the affected managed paths and
  the required `meridian upgrade --apply`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `task` parser, `transition_task_state`, task identity and archive paths. |
| `templates/workflows/lean-delivery/` | Managed closure text. |
| `skills/meridian-lean-delivery/SKILL.md`, `skills/meridian-lean-delivery-claude-code/SKILL.md` | Skill closure steps. |
| `AGENTS.md`, `CLAUDE.md`, `PROJECT_WORKFLOW.md` | This repository's managed copies. |
| `migrations/`, `capabilities/` | Migration, marker baselines, and capability version. |
| `tests/` | Command and upgrade tests. |

## Technical Context

- Reuse the archived-record resolution added by task 218, so `close` and
  recovery agree on archive paths.
- Template-changing under `docs/ADR_PUBLIC_SURFACE_AND_STABILITY.md`: it
  adds a stable command and a migration, so it ships in a minor release, at
  the earliest `1.3.0`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Governed SDD closure, committing on the agent's behalf, and creating state
at `worktree prepare`.

## Dependencies

- **Depends on**: 218
- **Blocks**: none
