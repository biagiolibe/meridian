# Task 024 — Add managed role procedures and move-aware upgrade support

> **ID**: `024`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Implement the additive release from task 023: introduce managed role
procedures and let upgrade/audit prove a declared capability move without
losing customized project rules.

## Acceptance Criteria

- [x] Managed implementation, review, remediation, and lifecycle procedure
      documents exist and contain the exact canonical rule blocks assigned by
      the ADR.
- [x] Entry points link to the relevant procedure but retain their existing
      duplicate procedures for this compatibility release.
- [x] Migration records can declare a capability move and `meridian upgrade`
      accepts it only when both protected source/target evidence is exact.
- [x] Locally modified source text produces a blocking conflict; an unmodified
      project upgrades and audits successfully.
- [x] Fixture tests cover vanilla, customized, and explicit Claude-pointer projects.

## Relevant Files

| File | Role |
|---|---|
| `scripts/meridian.py` | Upgrade planning and audit. |
| `templates/workflows/governed-sdd/` | Managed entry points and new procedures. |
| `tests/test_meridian_cli.py` | Upgrade and audit fixtures. |

## Constraints

- Follow task 023's accepted ADR exactly.
- Do not remove existing entry-point procedure text in this task.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Dependencies

- **Depends on**: 023
- **Blocks**: 025
