# Task 015 — Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner

> **ID**: `015`
> **Category**: Architecture
> **Priority**: 🔴 P1
> **Estimate**: ~2-3h
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

Introduce `workflowBaselineVersion` as an independent, derived version axis
(the last migration's `to` field), separate from `frameworkVersion`
(`VERSION`). This is the core change from the approved ADR splitting
`frameworkVersion` / `workflowBaselineVersion` / `protocolVersion`: it lets a
CLI-only release ship without a fake migration, and makes `meridian upgrade
--check` correctly report a framework-only delta instead of a misleading
`X -> X` no-op.

## 📋 Acceptance Criteria

- [x] A fixture scenario where the framework `VERSION` advances with no new
      migration record: `upgrade --check` reports the baseline plan as
      all-`keep`/zero-conflict **and** shows a non-trivial framework-version
      delta line; `upgrade --apply` changes only `manifest.frameworkVersion`
      and `manifest.protocolVersion` (`workflowBaselineVersion` and the
      baseline snapshot directory unchanged); a second `--check` run
      afterward is a true no-op. This is the regression guard for the
      "baseline snapshot is missing" failure mode.
- [x] A fixture scenario where a new migration is added: both
      `frameworkVersion` and `workflowBaselineVersion` advance together, the
      baseline snapshot directory is re-keyed to the new baseline version,
      and the old one is pruned.
- [x] A fixture scenario with a legacy manifest (only `frameworkVersion`, no
      `workflowBaselineVersion` key): `upgrade --check`/`--apply` still work
      correctly via the fallback, and the manifest written after apply has
      the explicit `workflowBaselineVersion` field.
- [x] `python3 scripts/check_repository.py` passes.
- [x] `python3 -m unittest discover -s tests -v` passes.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `read_version`, `version_key`, `lock_project`, `plan_from_baseline`, `plan_upgrade`, `print_plan`, `apply_plan`, `apply_upgrade` (roughly lines 81-260 and 1203-1593). |
| `tests/test_meridian_cli.py` | Add the fixture scenarios below. |

## 🧩 Technical Context

- **Current behavior**: `VERSION` is the single source of truth for both the
  public CLI release and the governed template baseline. `manifest.json`
  only carries `frameworkVersion`, which doubles as the baseline-snapshot
  directory name (`.meridian/baselines/<frameworkVersion>/`) and as the
  bound fed to `migration_ids(...)`. A CLI-only release cannot be reflected
  without either a fake migration or `upgrade --check` reporting a
  misleading no-op.
- **Desired behavior**: `workflowBaselineVersion` is derived mechanically as
  the greatest migration `to` value `<= frameworkVersion` — not a second
  hand-maintained file. `frameworkVersion` bumps on every release;
  `workflowBaselineVersion` only bumps when a real migration lands.

## 🔨 Suggested Implementation

1. Add `latest_migration_to(framework_root, upto=None)`: the greatest
   migration `to` value `<= upto` (default: `read_version(framework_root)`).
2. `lock_project`: write both `manifest["frameworkVersion"]` (from
   `VERSION`) and `manifest["workflowBaselineVersion"]` (from
   `latest_migration_to`). `copy_baseline` keyed by
   `workflowBaselineVersion`.
3. `plan_from_baseline`/`plan_upgrade`: fix the "framework source is older
   than the project lockfile" guard (currently ~line 1272) to compare
   baseline-version-to-baseline-version, not framework-to-baseline. Read the
   installed baseline version via
   `manifest.get("workflowBaselineVersion", manifest["frameworkVersion"])`
   (legacy fallback: old manifests never had the field, and their
   `frameworkVersion` doubled as the baseline version). `migration_ids(...)`
   bounds must be baseline versions.
4. `apply_plan`/`apply_upgrade`: fix `copy_baseline(...)` and
   `prune_stale_baselines(...)` (currently ~lines 1568-1569) to key off the
   *target baseline version*, not the target framework version — today they
   use `target_version` (the framework version), which orphans/loses the
   baseline snapshot on the next check once a CLI-only release lands. On
   apply, always write `manifest["frameworkVersion"]`,
   `manifest["protocolVersion"]`, and `manifest["workflowBaselineVersion"]`,
   even when the baseline plan is a no-op (all `keep`).
5. `print_plan`: add an informational line showing the framework-version
   delta (e.g. `Framework: 1.1.30 -> 1.1.31 (CLI-only; no baseline
   change)`), separate from the existing baseline/migration plan output,
   always printed even when the baseline plan is empty.

## ⚠️ Constraints and Considerations

- Do not touch `version_key()`'s parsing — prerelease/build handling is a
  separate task (018), scoped as a persistence-time guard, not a comparator
  rewrite.
- Out of scope (separate tasks): `adopt`/`finalize_adoption` changes (016),
  relaxing `check_repository.py`'s `check_migrations()` `VERSION` equality
  (017), the `releases/` ledger (019), the prerelease guard (018), docs
  (020).

## 🔗 Dependencies

- **Depends on**: 054
- **Blocks**: 016

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/015-split-workflow-baseline-version.md)"$'\n\nExecute this task in the current project.'
```

## Completion

Completed on 2026-09-26. Upgrade manifests now track the public framework
release independently from the migration-derived workflow baseline, retain a
legacy-manifest fallback, and report both deltas. Regression coverage verifies
CLI-only releases, migration releases, and legacy manifests. Adoption and
finalize-adoption propagation remains scoped to task 016.

Task 054 was added to `main` as a prerequisite after this task had already
started from commit `30a2cb8`. The developer explicitly authorized resolving
the resulting integration conflict while preserving Task 054 and its new queue
dependencies.

Validation:

- `python3 scripts/check_repository.py` (exit 0)
- `python3 -m unittest discover -s tests -v` (exit 0, 175 tests)
- `git diff --check` (exit 0)
