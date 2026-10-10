# Task 197 — Ship the 1.2.12 lifecycle documentation through migration 065

> **ID**: `197`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: 1.2.12 release readiness review, 2026-10-10
> **Origin**: friction

## Objective

Tasks 191, 192, and 194 changed lifecycle behavior and documented it only in
this repository's `docs/WORKTREE_LIFECYCLE.md`. The managed copies that
adopted projects receive,
`templates/workflows/{lean-delivery,governed-sdd}/docs/WORKTREE_LIFECYCLE.md`
(`worktree-lifecycle` v2), were not updated. Their managed text directs
agents to that document for diagnosis and manual recovery, yet it does not
describe:
- `meridian worktree repair-base` and the `STALE_WORKTREE_BASE` stop (task 194);
- the canonical `.meridian/execution-evidence.json` ledger allowed in a SPIKE
  task diff (task 192);
- conservative queue-section archival and its warnings (task 191).

Migration `065-spike-blueprint-worktree-closure` targets the unreleased 1.2.12.
Extend it so that the same release delivers this documentation, instead of
adding a second migration.

## Acceptance Criteria

- [x] Both template copies of `docs/WORKTREE_LIFECYCLE.md` gain a concise
  version of the three behaviors above, written for an adopting project:
  - a commit-less fast-forward recovery section that covers when
    `STALE_WORKTREE_BASE` is reported, how to run `repair-base`, what it
    changes, and that validation evidence must be renewed afterwards;
  - the SPIKE ledger path exception;
  - the archival rule that only `###` sections are candidates, that ambiguous
    or open tables retain the whole section with a warning, and that
    terminal states are `[x]` (Lean Delivery) or `ACCEPTED`/`ANSWERED`
    (Governed SDD).
  The SPIKE paragraph goes only into the Governed SDD copy unless the Lean
  copy already describes SPIKE tasks. Wording follows the repository copy
  where it fits, and nothing else in the copies changes.
- [x] The `worktree-lifecycle` marker moves from v2 to v3 in both copies.
  Migration 065 changes from its single `capability` and `capabilityVersion`
  pair to a `capabilities` list and per-mode `capabilityVersions`, following
  migration 064's format. The list keeps `task-blueprint` v16 and adds
  `worktree-lifecycle` v3. `docs/WORKTREE_LIFECYCLE.md` is added to
  `managedPaths`, and the `delta` describes only the added text.
  Migration 065 keeps its `id`, `from`, and `to`.
- [x] `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json`,
  `migrations/CAPABILITY_MARKERS.md`, and this repository's own managed
  baseline under `.meridian/baselines/1.2.12/`, if it carries the file, are
  updated consistently. `meridian audit` reports no drift.
- [x] `meridian upgrade --check` on copies of the Palimpsest and Fusa manifests
  shows both 065 changes and no `BLOCKED`; the results go in the handoff.
- [x] `VERSION` stays 1.2.12 and no new migration file is added.
- [x] One changelog fragment states the documentation under `Documentation`
  and the action under `Upgrade notes`.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/lean-delivery/docs/WORKTREE_LIFECYCLE.md` | Lean managed copy (`worktree-lifecycle` v2). |
| `templates/workflows/governed-sdd/docs/WORKTREE_LIFECYCLE.md` | Governed managed copy (`worktree-lifecycle` v2). |
| `docs/WORKTREE_LIFECYCLE.md` | Source wording from tasks 191, 192, and 194. |
| `migrations/065-spike-blueprint-worktree-closure.json` | Migration to extend. |
| `migrations/064-closure-text-uses-advance.json` | Reference for the multi-capability format. |
| `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json`, `migrations/CAPABILITY_MARKERS.md` | Marker registration. |

## Technical Context

- The repository copy and the template copies have different scope and
  wording. They already differed by about 370 lines at v1.2.11, so this task
  adds only the three behaviors and does not align the documents in bulk.
- An unreleased migration may be extended, as tasks 161 and 170 did with
  migration 063. A released migration is never edited.
- The CLI already prints the `repair-base` resume command with
  `STALE_WORKTREE_BASE`. This task fills the documentation gap and changes no
  behavior.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Bulk alignment of the repository and template copies, CLI changes, and
publishing 1.2.12.

## Dependencies

- **Depends on**: 191, 192, 194
- **Blocks**: publication of 1.2.12

## Completion

Implemented and validated on `task-197`; see `tasks/handoffs/197.md`.
Migration 065 delivers both capabilities without changing VERSION or adding
a migration. Queue and project-plan closure are owned by integration stage.
