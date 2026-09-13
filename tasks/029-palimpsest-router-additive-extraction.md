# Task 029 — Map and additively extract Palimpsest router procedures

> **ID**: `029`
> **Category**: Integration
> **Priority**: 🟡 P2
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Create Palimpsest's accepted rule-to-route map and copy its project-owned
entry-point rules into the role documents required by the shared-router ADR.

## Acceptance Criteria

- [ ] A Palimpsest ADR maps every current `AGENTS.md` section to its final
      canonical route or document, with a rationale for each always-loaded rule.
- [ ] `STATUS_DESIGN.md`, implementation, review, remediation, and lifecycle
      documents contain verbatim mapped rules without removing old copies.
- [ ] Framework marker moves use exact capability evidence; unmarked local
      text is copied only through the approved map.
- [ ] A clean upgraded checkout passes the additive audit and route fixtures.

## Constraints

- Do not retire or compact Palimpsest entry points in this task.
- Do not alter lifecycle, review, validation, evidence, Git, or domain
  semantics while relocating prose.

## Validation

- `meridian upgrade --project <palimpsest> --check`
- `meridian audit --project <palimpsest> --mode governed-sdd`
- Palimpsest route fixtures declared by task 028
- `git diff --check`

## Dependencies

- **Depends on**: 026, 028
- **Blocks**: 030
