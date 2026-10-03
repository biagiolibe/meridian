# Task 129 — Choose the task-identity mode at project setup

> **ID**: `129`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task-identity option review, 2026-10-03

## Objective

The opt-in milestone task identity (`M<milestone>-<WORKSTREAM>-<ordinal>`) is
implemented and selected by `.meridian/task-identity.json`, but nothing creates
that file: no template, `init`, `lock`, `setup`, or `upgrade` writes it, so a
project that wants it must know to create it by hand. Let a project that adopts
Meridian choose `opaque` or `milestone` at the start, and have `meridian setup`
write the declaration with the project's consent. Existing projects and upgrades
are unaffected.

An earlier draft of this task proposed documentation and an activation
procedure. A rehearsal on a copy of the Palimpsest task records (302 IDs: 141
structured, 161 legacy-opaque, no errors) showed the mode already works, so that
scope was dropped.

## Acceptance Criteria

- [ ] `meridian setup` accepts an explicit task-identity choice (for example
  `--task-identity opaque|milestone`). `--check` lists the planned write of
  `.meridian/task-identity.json` with its mode; `--apply` writes it. Without the
  option, `setup` writes nothing, so existing invocations behave as before.
- [ ] The file content is exactly the existing closed schema
  (`{"version": 1, "mode": "<chosen>"}`), written atomically and validated by
  the same parser the resolver uses. An invalid choice is refused before any
  write.
- [ ] An existing declaration is never overwritten. If one exists and differs
  from the requested mode, `setup` reports the difference and leaves the file
  unchanged; an identical one is reported as already set.
- [ ] Recording `opaque` explicitly is allowed at project start and is a
  recorded choice, not an upgrade restating a default. `meridian upgrade`
  continues never to create or modify the file, and absence continues to select
  `opaque`; a test proves both.
- [ ] The `/meridian-init` command (and the skills that bootstrap a project) ask
  the developer to choose `opaque` or `milestone`, explain the one-line
  difference, never choose by default for them, and pass the answer to `setup`.
  The wording states that the choice can be changed later by editing the file.
- [ ] The choice is independent of the workflow mode: both Lean Delivery and
  Governed SDD can select either value, and no behavior is restricted per
  workflow.
- [ ] After `setup` with `milestone`, `meridian task identity check` reports the
  declared mode, and a malformed or conflicting declaration still fails closed.
- [ ] `docs/TASK_IDENTITY_POLICY.md` is corrected from "design proposal" to its
  real implemented status and states that `setup` is the supported way to create
  the declaration; no other behavior of the document changes.
- [ ] Tests cover: no option writes nothing; each valid mode written; invalid
  value refused; existing identical and existing different declarations; the
  `--check` plan text; upgrade never writing the file; and both workflow modes.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `plan_setup`, `apply_setup`, the `setup` parser, and the declaration parser and path constant. |
| `commands/meridian-init.md` | Bootstrap prompt that must ask for the choice. |
| `skills/meridian-*/SKILL.md` | Skills that bootstrap or operate a project, where they mention initialization. |
| `docs/TASK_IDENTITY_POLICY.md` | Status correction. |
| `tests/test_meridian_cli.py` | Setup and identity tests. |

## Technical Context

- The declaration is project-owned and deliberately outside `.meridian/manifest.json`
  and every managed template, so a framework upgrade cannot overwrite a choice
  (`docs/TASK_IDENTITY_POLICY.md`).
- `meridian setup` already plans and applies worktree, Codex, and Claude Code
  configuration with consent. Read `plan_setup` and `apply_setup` first to
  decide whether the choice fits the existing plan structure or needs a small
  dedicated step; record that decision in the handoff.
- A project created with this task's flow gets the file from `setup`; this task
  does not change how an agent proposes IDs for new tasks, which is covered by a
  separate follow-up.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the grammar, resolver, or schema; making `/meridian-task` or any task
creation flow identity-aware (follow-up); migrating or renaming existing
projects' tasks; writing the declaration in any existing project; and publishing
a release.

## Dependencies

- **Depends on**: —
- **Blocks**: none
