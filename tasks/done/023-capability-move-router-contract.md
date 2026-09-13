# Task 023 — Define capability-move and bootstrap-router contract

> **ID**: `023`
> **Category**: Architecture
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned

## Objective

Turn `docs/AGENT_INSTRUCTION_ROUTING_SPIKE.md` into an accepted, implementable
contract for compact agent entry points and safe capability relocation.

## Acceptance Criteria

- [x] An ADR defines the bootstrap byte budget, mandatory always-loaded
      invariants, request-to-role routing map, and the managed role-document
      paths.
- [x] The ADR defines a machine-readable migration declaration for moving a
      capability marker between managed files, including exact-source and
      exact-target checks.
- [x] It specifies that a locally modified source marker blocks the move;
      no upgrade may discard or silently duplicate it.
- [x] It records the additive release, retirement release, rollback boundary,
      and required upgrade/audit fixture scenarios.

## Relevant Files

| File | Role |
|---|---|
| `docs/AGENT_INSTRUCTION_ROUTING_SPIKE.md` | Measured problem and proposed architecture. |
| `scripts/meridian.py` | Migration and audit behavior. |
| `migrations/CAPABILITY_MARKERS.md` | Existing marker contract. |

## Constraints

- Do not alter templates, marker content, upgrader behavior, or consumer projects.
- Repository text and the ADR must be in English.

## Validation

- `git diff --check`
- `python3 scripts/check_repository.py`

## Dependencies

- **Depends on**: none
- **Blocks**: 024
