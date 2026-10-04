# Task 164 — State the stop and denial rules in the managed workflow text

> **ID**: `164`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

Agents read stop conditions from the managed `git-workflow` block. That block
lets prose add stops that no command backs (tasks 159 and 161). It also does
not say what to do when a gate contradicts another rule. Put Decisions 1 and 4
of `docs/ADR_STOPS_AND_DENIALS.md` into the managed text of both workflows.

## Acceptance Criteria

- [ ] The managed `git-workflow` block in the Lean Delivery and Governed SDD
  templates, the Lean router copies, and this repository's own copies:
  - keeps the deny list as it is;
  - states that a stop is valid only when it is backed by a `BLOCKED <CODE>`
    line from a Meridian command, a non-zero exit of a required command, or an
    acceptance criterion the agent can name as unmet;
  - states that an agent never satisfies a gate by writing false state, and
    stops and reports both rules when a gate contradicts another rule;
  - states that when a Meridian command accepted a state that the text appears
    to forbid, the agent follows the command and records the difference under
    `Rule discrepancies:`, except for actions on the deny list.
- [ ] The long list of closure stop codes in prose is replaced by a reference
  to `capabilities/stop-codes-v1.json` and to `meridian worktree
  closure-status`. The step order of the closure stays stated.
- [ ] `docs/COMPLETION_REPORT_TEMPLATE.md` and its template copies gain an
  optional `Rule discrepancies:` line (`none | rule, command result, and what
  was followed`). `handoff-check` accepts a report with or without it.
- [ ] The capability marker version of the block is bumped once in the
  unreleased 1.2.9 release. If task 161 has already bumped the `git-workflow`
  marker in an unreleased 1.2.9 migration, this task extends that migration and
  marker version and does not add a second bump. Otherwise it adds a migration
  whose `to` is 1.2.9.
- [ ] `meridian upgrade --check` on copies of the Palimpsest and Fusa manifests
  shows the block update and no `BLOCKED`; the results go in the handoff.
- [ ] `VERSION` is not bumped again; it is already the unreleased 1.2.9.
- [ ] One changelog fragment states the rule under `Changed` and the action
  under `Upgrade notes`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/lean-delivery/{PROJECT_WORKFLOW,AGENTS,CLAUDE}.md` | Lean block and router copies. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Governed block. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | This repository's copies. |
| `docs/COMPLETION_REPORT_TEMPLATE.md` and template copies | `Rule discrepancies:` line. |
| `migrations/`, `migrations/CAPABILITY_MARKERS.md`, `migrations/marker-baselines/` | Marker version and migration. |
| `scripts/meridian.py` | `check_handoff` optional field. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decisions 1 and 4.
- Task 159 already moved `VERSION` to 1.2.9 with migration 063. Task 161
  changes a sentence of the same block. Read its migration, if integrated,
  before writing this one.
- Keep the Codex and Claude Code skill assets for each mode in parity, as
  `CONTRIBUTING.md` requires.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Shrinking the routers, introducing `meridian worktree advance`, and changing any
stop code.

## Dependencies

- **Depends on**: 161, 163
- **Blocks**: none
