# Task 029 — Map and additively extract consumer project A router procedures

> **ID**: `029`
> **Category**: Integration
> **Priority**: 🟡 P2
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Create consumer project A's accepted rule-to-route map and copy its project-owned
entry-point rules into the role documents required by the shared-router ADR.

## Acceptance Criteria

- [x] A consumer project A ADR maps every current `AGENTS.md` section to its final
      canonical route or document, with a rationale for each always-loaded rule.
- [x] `STATUS_DESIGN.md`, implementation, review, remediation, and lifecycle
      documents contain verbatim mapped rules without removing old copies.
- [x] Framework marker moves use exact capability evidence; unmarked local
      text is copied only through the approved map.
- [x] A clean upgraded checkout passes the additive audit and route fixtures.

## Constraints

- Do not retire or compact consumer project A entry points in this task.
- Do not alter lifecycle, review, validation, evidence, Git, or domain
  semantics while relocating prose.

## Validation

- `meridian upgrade --project <consumer-a> --check`
- `meridian audit --project <consumer-a> --mode governed-sdd`
- Consumer project A route fixtures declared by task 028
- `git diff --check`

## Dependencies

- **Depends on**: 026, 028
- **Blocks**: 030

## Execution record

2026-09-21 — consumer project A's accepted `WFLOW-004` supplied the complete
ADR-0054 rule-to-route map; accepted `WFLOW-005` supplied the additive,
verbatim route-document copies while retaining the old entry points. Their
independent review records document a passing governed-SDD audit and exact
protected-marker evidence. On the current clean consumer project A checkout,
`meridian upgrade --project . --check` reported only `KEEP` actions and
`meridian audit --project . --mode governed-sdd` passed.
