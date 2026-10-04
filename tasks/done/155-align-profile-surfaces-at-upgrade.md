# Task 155 — Align capability-profile surfaces at upgrade and keep `upgrade --check` from blocking on them

> **ID**: `155`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Palimpsest and Fusa upgrade check failures after task 153, 2026-10-04

## Objective

Task 153 added `docs/COMPLETION_REPORT_TEMPLATE.md` to the `execution-evidence`
managed surface in `capabilities/catalog-v1.json`. Every project whose manifest
already declares `capabilityProfiles` (Palimpsest and Fusa observed) now fails
`meridian upgrade --check` with `BLOCKED: capabilityProfiles.<profile>.capabilities.execution-evidence.managedSurface
must completely match the catalog surface`.

Two engine properties cause this, and a migration cannot repair either:

1. `load_manifest` validates the project manifest against the *current*
   framework catalog, and `prepare_upgrade_targets` calls it first, so the error
   precedes migration planning.
2. The upgrade path copies `capabilityProfiles` through unchanged;
   only `bootstrap_capability_profile` rebuilds declarations, and it is not part
   of upgrade.

Task 153 is the first change to a documented surface after profiles shipped, so
no mechanism exists. Add one, so that a catalog surface change is applied by
`meridian upgrade` and visible in `--check`, and add a repository gate so the
class of error cannot recur.

## Acceptance Criteria

- [x] `meridian upgrade --check` on a project whose manifest declares a profile
  surface set older than the catalog no longer reports `BLOCKED`. The plan shows
  one row per profile capability whose declared surface differs from the catalog
  (for example `PROFILE-SURFACE governed-sdd-consumer/execution-evidence:
  add docs/COMPLETION_REPORT_TEMPLATE.md`). The check writes nothing.
- [x] `meridian upgrade` on that project installs the missing managed files and
  rewrites each affected declaration from the target catalog using the same
  construction as `bootstrap_capability_profile`: surfaces and forms from the
  catalog, installation evidence with recorded digests, and existing
  `hostActivation` and `verification` snapshots preserved for unchanged
  surfaces. The written manifest validates against the catalog.
- [x] The existing refusal to record a digest over a different recorded one
  (drifted managed copy) is kept; a drifted copy still stops the upgrade.
- [x] Validation of a manifest whose surfaces *differ from the catalog in any
  other way* (a path not in the catalog, an unsupported form, a duplicate path,
  a missing capability, a wrong profile or capability version) still fails with
  today's messages. Only "catalog surface is a superset of the declared surface"
  is deferred to the plan.
- [x] Tests on fixtures prove: the current failure reproduces on an old manifest
  and is gone; `--check` is read-only and prints the row; `upgrade` produces a
  manifest equal to the one a fresh `bootstrap` would write for the same files;
  drift, unknown-path, and version-mismatch cases still fail.
- [x] `scripts/check_repository.py` fails, naming the capability and path, when
  the catalog's managed surface for a capability changes relative to the
  previous release's catalog (`release-baselines` or the latest tag) and no
  migration in the next release lists the added path in `managedPaths`. Tests
  cover the failing and passing cases.
- [x] `meridian upgrade --check` run against copies of the Palimpsest and Fusa
  manifests (read-only, outside their repositories) reports the new row and no
  `BLOCKED`; results are recorded in the handoff.
- [x] One changelog fragment states the fix and, under `Upgrade notes`, that
  projects with `capabilityProfiles` gain the completion report template.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `parse_capability_profiles` (~3969), `load_manifest` (~4125), `bootstrap_capability_profile` (~6131), `prepare_upgrade_targets` (~7080), `plan_upgrade`, `plan_from_baseline`, apply path (~7380). |
| `capabilities/catalog-v1.json` | Source of target surfaces. |
| `scripts/check_repository.py` | New catalog-surface-versus-migration gate. |
| `tests/` | Upgrade-plan, bootstrap, and repository-check tests. |
| `migrations/062-primary-project-declaration-and-review-authority.json` | Candidate carrier for the added path if the gate requires a `managedPaths` entry; content change only if unavoidable. |

## Technical Context

- Observed on 2026-10-04: Palimpsest and Fusa both stop at
  `capabilityProfiles.governed-sdd-consumer.capabilities.execution-evidence.managedSurface
  must completely match the catalog surface` (`scripts/meridian.py:4035`).
- `capabilityProfiles` appears in the upgrade path only as a pass-through
  (`plan_from_baseline`, the apply call); `bootstrap_capability_profile` is
  reachable only from the CLI.
- Decision recorded here: the manifest is not repaired by a migration (it cannot
  run before validation) and the catalog surface is not narrowed (it would undo
  task 153's contract). `--check` defers only the superset case to the plan;
  every other mismatch remains a hard error.
- Target release is 1.2.8, which task 154 prepares; this task must be integrated
  before 1.2.8 is published. Publishing stays the developer's action.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Publishing 1.2.8, changing the `execution-evidence` surface itself, repairing
Palimpsest or Fusa manifests by hand, and reworking profile verification or host
activation states.

## Dependencies

- **Depends on**: 154 (version records at 1.2.8)
- **Blocks**: publication of 1.2.8
