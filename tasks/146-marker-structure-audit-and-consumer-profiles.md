# Task 146 — Restructure inline markers, audit managed copies, and add consumer profiles

> **ID**: `146`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D10, D12, P2, P4, UNVERIFIED row, design approved 2026-10-04

## Objective

- **D10** Inline markers inside prose force a project to quote framework text.
  `docs/CODE_REVIEW_PROMPT.md` carries three inline markers
  (`task-worktree-review` v4, `ci-verified-validation` v1,
  `manual-verification-review-check` v1); `IMPLEMENTATION.md` carries a
  sentence-fragment `validation-scoping` marker and `CONTEXT_BUDGET_POLICY.md` an
  inline `read-guard` marker.
- **P2/P4** Projects need a supported place for their own review checklist and
  audit checks next to the managed blocks.
- **D12** `docs/WORKTREE_LIFECYCLE.md` and the unmarked sections of
  `docs/PULL_REQUEST_POLICY.md` hold normative rules but `meridian audit` checks
  only markers, not whole-file managed-copy digests.
- **UNVERIFIED** A legacy protocol v2 manifest without `capabilityProfiles` audits
  as `UNVERIFIED`, and no catalog profile exists for a consumer project, so
  `meridian profile bootstrap` offers no migration path.

## Acceptance Criteria

- [ ] `docs/CODE_REVIEW_PROMPT.md` (Governed) is one standalone managed block
  `code-review-prompt` v1 containing the whole prompt; it replaces the three inline
  markers in that file and tells the reviewer to apply the project's
  `## Project review checklist` section, placed after the block, when present.
- [ ] `validation-scoping` in `IMPLEMENTATION.md` and `read-guard` in
  `CONTEXT_BUDGET_POLICY.md` become standalone blocks with complete sentences;
  `read-guard` v2 states that the active task comes from the verified worktree and
  the router read set is exempt (behavior from task 143).
- [ ] `audit-prompt` gains the instruction to run a `## Project-specific checks`
  section after the block, each check citing an accepted ADR (combined with the
  v3 text of task 145, without a second bump).
- [ ] Upgrade of a project whose inline markers are surrounded by project prose
  keeps that prose in a collision-safe adjacent backup and reports it; it never
  silently drops text.
- [ ] `docs/WORKTREE_LIFECYCLE.md` is a whole-file managed capability
  `worktree-lifecycle` v1 in both modes; the unmarked "Remote task-branch cleanup"
  section of `PULL_REQUEST_POLICY.md` becomes `remote-branch-cleanup` v1 and the
  unmarked duplicate of the reviewer identity rule is removed.
- [ ] `meridian audit` reports a FAIL row for every whole-file managed copy whose
  digest differs from `managedFiles`, reusing the comparison task 139 ships (or the
  profile doctor's, if 139 is not integrated) rather than a third implementation.
- [ ] The catalog gains `governed-sdd-consumer` v1 and `lean-delivery-consumer` v1
  profiles listing their capabilities; `meridian profile bootstrap <id> --check`
  then `--apply` turns the legacy `UNVERIFIED` declaration row into declared
  profiles with installation evidence, leaving host activation `UNVERIFIED` until a
  probe exists. The procedure is documented for consumers.
- [ ] All changes join the single unreleased template-changing migration used by
  task 145; marker baselines and digests are refreshed.
- [ ] Tests cover: the new blocks parse and audit as PASS; prose around a
  retired inline marker is preserved on upgrade; a drifted managed copy fails the
  audit; bootstrap of each consumer profile on a legacy fixture.
- [ ] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md`, `docs/workflows/IMPLEMENTATION.md`, `docs/CONTEXT_BUDGET_POLICY.md`, `docs/PULL_REQUEST_POLICY.md`, `docs/AUDIT_PROMPT_READ_ONLY.md` | Marker restructuring. |
| `templates/workflows/*/docs/WORKTREE_LIFECYCLE.md` | New whole-file capability. |
| `capabilities/catalog-v1.json` | Consumer profiles. |
| `scripts/meridian.py` | Audit managed-copy rows, `profile bootstrap`, upgrade handling of retired inline markers. |
| `migrations/` | Shared migration. |
| `tests/` | Audit, upgrade, and profile tests. |

## Technical Context

- `bootstrap_capability_profile` accepts only catalog profiles; today the catalog
  holds `meridian-self-hosting` only.
- Task 139 adds a digest-drift check for this repository; reuse its comparison.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Lifecycle wording (task 145), host activation probes for consumer profiles, and
tagging or publishing the release (the developer's action).

## Dependencies

- **Depends on**: 145
- **Blocks**: none
