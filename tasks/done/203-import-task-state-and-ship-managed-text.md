# Task 203 — Import task state and ship the managed review, closure, and Accept text

> **ID**: `203`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR machine task state, 2026-10-11
> **Origin**: friction

## Objective

Implement Decision 6 and the managed-text consequences of
`docs/ADR_MACHINE_TASK_STATE.md`. Adopted projects create state files for
their open tasks through an explicit command. The managed procedures tell
agents to change state and record verdicts only through the commands.

## Acceptance Criteria

- [x] `meridian task state import [<TASK-ID>…] --project <path> [--apply]
  --format json`:
  - for each open task, prints the state file it would write and the queue,
    record, and review evidence it read;
  - writes only with `--apply`, and never overwrites an existing state file;
  - stops with `TASK_STATE_INVALID` for a task whose texts disagree, naming
    both values instead of choosing one.
  Terminal tasks need no file and are skipped.
- [x] The managed Governed SDD review procedure, remediation, closure text, and
  `Accept <TASK-ID>` tell agents to:
  - use `meridian task transition` and `meridian review verdict [--owner]`;
  - never edit a status or verdict by hand.
  The Lean Delivery closure text names `meridian task transition` for `DONE`
  only where closure needs it. The governance-file ownership rule adds the
  task's own state file. The review record template states that its headings
  are human-readable only.
- [x] One migration whose `to` is the next release:
  - delivers the text through the existing capability marker mechanism;
  - lists the affected capabilities and managed paths;
  - has upgrade notes that tell adopters to run `meridian task state import`
    and then `--apply`.
  The marker baselines and `meridian audit` stay consistent.
- [x] `meridian upgrade --check` on copies of the Palimpsest and Fusa
  manifests shows the update and no `BLOCKED`. `task state import` on a copy
  of each project lists its open tasks without error. The results go in the
  handoff.
- [x] `VERSION`, `.claude-plugin/plugin.json`, and the release ledger are bumped
  only if no earlier unreleased task has done so for the same release.
- [x] One changelog fragment states the change under `Changed` and the action
  under `Upgrade notes`.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `task state import`. |
| `templates/workflows/governed-sdd/` | Review procedure, remediation, closure, `Accept`, review record template. |
| `templates/workflows/lean-delivery/` | Closure text and governance ownership. |
| `migrations/`, `migrations/CAPABILITY_MARKERS.md`, `migrations/marker-baselines/` | Migration and markers. |
| `skills/` | Codex and Claude Code skill parity. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decision 6 and Consequences.
- Adoption by Palimpsest and Fusa happens in those projects through `upgrade`
  and `task state import`, outside this repository.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Rewriting historical task, review, or queue records, and authenticating
reviewers.

## Dependencies

- **Depends on**: 201, 202
- **Blocks**: none

## Completion

Implemented explicit preview/apply task-state import, command-owned managed procedures, migration 066, and the next-release 1.2.13 metadata. Required repository validation passed; Palimpsest and Fusa copy checks are recorded in the handoff.
