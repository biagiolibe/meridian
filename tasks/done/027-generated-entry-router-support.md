# Task 027 — Add generated shared entry-router support

> **ID**: `027`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Implement the Meridian support specified by
`docs/ADR_SHARED_GENERATED_ENTRY_ROUTERS.md`: one canonical consumer router
source with byte-identical generated `AGENTS.md` and `CLAUDE.md` outputs.

## Acceptance Criteria

- [x] A consumer-owned `docs/workflows/ENTRY_ROUTER.md` can generate both
      entry points without hand-maintained duplicated router text.
- [x] Checks and audit reject output drift and entry points over 2,048 UTF-8
      bytes.
- [x] Legacy explicit and prose Claude pointers remain valid migration inputs
      but are not emitted by the generator.
- [x] Fixture tests cover generated equality, an allowed host overlay, drift,
      budget failure, and pointer compatibility.

## Constraints

- Do not change existing consumer projects.
- Preserve current capability-move and three-way upgrade safety behavior.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Dependencies

- **Depends on**: 025
- **Blocks**: 028, 029
