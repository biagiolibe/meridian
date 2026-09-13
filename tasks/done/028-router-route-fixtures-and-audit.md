# Task 028 — Add routed-read fixtures and adoption audit

> **ID**: `028`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned

## Objective

Provide Meridian fixtures and audit evidence for a consumer's status/design,
implementation, review, remediation, and lifecycle routing map.

## Acceptance Criteria

- [x] A documented consumer map declares one primary document for every
      required command route.
- [x] Fixture tests prove the generated router names only the expected primary
      route and that each role document reaches its required safeguards.
- [x] Audit reports a missing route, stale generated entry point, or retained
      retired framework marker as a failure.
- [x] Fixture output records before/after byte measurements without loading
      unrelated role procedures.

## Constraints

- Do not inspect or rewrite consumer domain prose heuristically.
- Keep route verification deterministic and repository-local.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Dependencies

- **Depends on**: 027
- **Blocks**: 029
