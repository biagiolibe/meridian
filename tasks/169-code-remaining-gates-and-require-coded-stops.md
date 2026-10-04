# Task 169 — Code the remaining gates and require every stop to carry a code

> **ID**: `169`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

After tasks 162 and 166, the validation, investigation, budget, and remaining
generic `BLOCKED` messages still have no codes. Managed text may still tell
agents to return a bare `BLOCKED`. Finish the gate audit in
`docs/ADR_STOPS_AND_DENIALS.md` and make an uncoded stop impossible to add.

## Acceptance Criteria

- [ ] Every remaining `BLOCKED` in `scripts/meridian.py` is emitted through the
  registry helper with a registered code. These include `validation`,
  `investigation`, `budget spend`, `return`, and the unprefixed messages.
- [ ] Each of these gates is checked against the four properties of the gate
  contract. The handoff lists each gate with its code and any gate found not
  satisfiable. A gate that is not satisfiable is reported as a proposed
  follow-up task and is not silently changed.
- [ ] Every managed-text line that tells an agent to stop or return `BLOCKED`
  names a registered code, including workflow-unreadable and authority-conflict
  stops, which get `judgment` codes. `check_repository.py` (the check from task
  163) now fails on an uncoded `BLOCKED` in managed text or in the CLI.
- [ ] If managed text changes, it ships through the existing capability marker
  mechanism with a migration to the next release, and `upgrade --check` on
  copies of the Palimpsest and Fusa manifests is recorded in the handoff.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Remaining `BLOCKED` messages. |
| `scripts/check_repository.py` | Uncoded-stop check. |
| `capabilities/stop-codes-v1.json` | New codes. |
| `templates/workflows/*/` and this repository's copies | Uncoded `BLOCKED` lines. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decisions 2 and 3.
- On 2026-10-05 the CLI had about 36 free-text `BLOCKED` messages under ten
  prefixes.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Renaming existing codes and redesigning a gate found not satisfiable.

## Dependencies

- **Depends on**: 163, 166
- **Blocks**: none
