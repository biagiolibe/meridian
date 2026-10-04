# Task 170 — Require a declared validation ID for every command that proves a criterion

> **ID**: `170`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: GitHub issue #4 (part 1), 2026-10-05

## Objective

In the Governed SDD blueprint, `## Validation` declares the commands that
`meridian execution validate` may run. Nothing tells the task author that every
command proving an acceptance criterion or an `Evidence needed` item must be
declared there. In one project, nine tasks declared only the standard format,
workspace check, and workspace test IDs, while their criteria required hash
comparisons and repeated captures. Agents then composed those commands
themselves, with `mktemp` paths and compound shell strings, and each one
triggered a permission prompt because a host allowlist cannot match a
composed string.

Fix the problem at its source, which is the blueprint wording the task author
follows. This is part 1 of issue #4. The non-blocking preflight hint
(part 2) is out of scope.

## Acceptance Criteria

- [ ] The `## Validation` guidance in
  `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` states that:
  - every command that proves an acceptance criterion or an `Evidence needed`
    item has its own declared validation ID;
  - one ID holds exactly one command;
  - output paths are fixed and task-scoped, for example `target/<TASK-ID>/`;
  - commands use no `mktemp`, `$(...)`, or time-based paths.
- [ ] The guidance is wording only. `require_named_validation_commands` and
  `validation_commands` do not change what they accept, and existing tasks that
  declare fewer IDs are not an error.
- [ ] The change ships through the `task-blueprint` capability marker.
  Migration 063 already bumps `task-blueprint` to v14 for the unreleased 1.2.9.
  If 1.2.9 is still unreleased when this task starts, extend migration 063's
  `task-blueprint` delta and keep v14. Otherwise, add a migration to the next
  release that bumps the marker version. The marker baselines and
  `migrations/CAPABILITY_MARKERS.md` stay consistent, and `meridian audit`
  reports no drift.
- [ ] The Governed SDD Codex and Claude Code skill assets that describe task
  validation stay in parity, as `CONTRIBUTING.md` requires.
- [ ] `meridian upgrade --check` on copies of the Palimpsest and Fusa manifests
  shows the blueprint update and no `BLOCKED`; the results go in the handoff.
- [ ] One changelog fragment states the change under `Changed` and the author
  guidance under `Upgrade notes`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | `## Validation` guidance (task-blueprint v14). |
| `migrations/063-retire-reasoning-budget-contract.json` or a new migration | Marker delivery. |
| `migrations/CAPABILITY_MARKERS.md`, `migrations/marker-baselines/` | Marker registration. |
| Governed SDD skill assets under `skills/` | Parity of task-validation guidance. |

## Technical Context

- GitHub issue #4 describes the observation and both parts. Its author asked
  whether part 1 could land alone first; this task answers yes.
- Command-exit stops in `docs/ADR_STOPS_AND_DENIALS.md` are reliable only when
  their commands are declared. This task supports that ADR, but it is not
  required by it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

The preflight hint from part 2 of issue #4, Lean Delivery templates, and any
change to what the validation parser accepts.

## Dependencies

- **Depends on**: —
- **Blocks**: none
