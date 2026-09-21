# Task 030 — Generate compact Palimpsest entry routers and retire copies

> **ID**: `030`
> **Category**: Integration
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned

## Objective

After the additive Palimpsest release is accepted, generate compact identical
entry routers and retire only the old copies proven by the route map.

## Acceptance Criteria

- [x] `AGENTS.md` and `CLAUDE.md` are generated from Palimpsest's canonical
      router, are within 2,048 bytes, and contain no role procedure.
- [x] Every retired copy has accepted additive evidence; no unmarked
      project-owned text is removed without its mapped destination.
- [x] Status/design, `Proceed`, and `Review` fixtures read only their routed
      primary documents and preserve all required safeguards.
- [x] Before/after byte counts and a passing audit are recorded.

## Constraints

- Stop on route, marker, generated-file, or consumer-content conflict.
- Do not use a Claude pointer as the final configuration.

## Validation

- `meridian audit --project <palimpsest> --mode governed-sdd`
- Palimpsest route fixtures declared by task 028
- `git diff --check`

## Dependencies

- **Depends on**: 029
- **Blocks**: 031

## Execution record

2026-09-21 — Palimpsest's accepted `WFLOW-006` completed the retirement
release after `WFLOW-005`'s accepted additive evidence. Its independent review
records byte-identical generated `AGENTS.md`, `CLAUDE.md`, and
`docs/workflows/ENTRY_ROUTER.md` at 1,448 bytes; the six-route map; before/after
measurements; and a passing governed-SDD audit. The current clean checkout
again passed `meridian generate-entry-routers --project . --check` and
`meridian audit --project . --mode governed-sdd`.
