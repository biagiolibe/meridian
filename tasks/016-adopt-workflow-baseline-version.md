# Task 016 — Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption`

> **ID**: `016`
> **Category**: Architecture
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

Extend the `frameworkVersion` / `workflowBaselineVersion` split (task 015) to
the `adopt` and `finalize-adoption` paths, which write a manifest for a
project that was never `lock`ed. `detect_source_version` and
`release-baselines/<v>/` are baseline-semantics (a legacy `1.0.0` project's
"version" has only ever meant its template snapshot); the framework version
at adoption time is whatever `VERSION` currently is, which is not the same
number the moment adoption runs against a newer CLI.

## 📋 Acceptance Criteria

- [ ] `meridian adopt --mode governed-sdd --from 1.0.0 --check`/`--apply`
      writes a manifest with `workflowBaselineVersion: "1.0.0"` and
      `frameworkVersion` equal to the current `VERSION` of the framework
      source used to adopt — independent values, not the same field reused.
- [ ] `finalize_adoption` writes both fields the same way.
- [ ] A test where the adopting framework's `VERSION` is ahead of `1.0.0`
      confirms the two fields differ in the resulting manifest.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `detect_source_version`, `copy_adoption_baseline`, `adopt_project`, `finalize_adoption`. |
| `tests/test_meridian_cli.py` | Add the adoption-manifest scenario. |

## 🧩 Technical Context

- **Current behavior**: adoption writes `manifest["frameworkVersion"]` as
  the only version field, using the packaged baseline version (e.g.
  `1.0.0`) — conflating framework and baseline exactly like `lock` did
  before task 015.
- **Desired behavior**: mirrors task 015's manifest shape —
  `frameworkVersion` (current CLI) and `workflowBaselineVersion` (the
  baseline actually adopted) are independent fields.

## 🔨 Suggested Implementation

1. In `adopt_project`/`finalize_adoption`, keep `detect_source_version` as
   the baseline-version source (feeds `workflowBaselineVersion`), and read
   the framework version separately via `read_version(framework_root)`
   (feeds `frameworkVersion`).
2. Ensure `copy_adoption_baseline` still keys `.meridian/baselines/<v>/` by
   the baseline version, unchanged.
3. Update or add tests asserting the two fields can legitimately differ.

## ⚠️ Constraints and Considerations

- Depends on task 015 landing first (same manifest shape, same fallback
  helper if one was introduced there).
- Do not change `release-baselines/<v>/` semantics — it already names a
  baseline version, not a framework version.

## 🔗 Dependencies

- **Depends on**: 015
- **Blocks**: 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/016-adopt-workflow-baseline-version.md)"$'\n\nExecute this task in the current project.'
```
