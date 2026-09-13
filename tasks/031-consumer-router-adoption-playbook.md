# Task 031 — Publish the consumer router-adoption playbook

> **ID**: `031`
> **Category**: Documentation
> **Priority**: 🟢 P3
> **Estimate**: ~2h
> **Assigned to**: unassigned

## Objective

Turn the accepted Palimpsest pilot evidence into a repeatable, safe adoption
playbook for other Meridian consumer projects.

## Acceptance Criteria

- [ ] The playbook specifies inventory, ADR mapping, additive extraction,
      route evidence, retirement, audit, and rollback boundaries.
- [ ] It distinguishes Meridian-managed markers from unmarked consumer rules
      and prohibits heuristic deletion of the latter.
- [ ] It gives measurable byte and route-fixture exit criteria.

## Constraints

- Do not claim another consumer has adopted the router without its own ADR,
  migration evidence, and audit.

## Validation

- `python3 scripts/check_repository.py`
- `git diff --check`

## Dependencies

- **Depends on**: 030
- **Blocks**: none
