# Task 020 — Update docs for the version split

> **ID**: `020`
> **Category**: Documentation
> **Priority**: 🟢 P3
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

Update every document that currently states or implies `frameworkVersion`
and the governed template baseline are the same number, now that tasks
015-019 have split them into `frameworkVersion` / `workflowBaselineVersion`
/ `protocolVersion`.

## 📋 Acceptance Criteria

- [ ] `README.md`'s "Framework upgrades" section describes the three axes
      and how a CLI-only release differs from a template-changing release.
- [ ] `CONTRIBUTING.md` reflects the new release procedure (see below) and
      the "no fake migrations" rule now has a concrete alternative to point
      to (a CLI-only release).
- [ ] `migrations/README.md`'s line "Only the snapshot matching the
      manifest's current `frameworkVersion` is ever read again" is corrected
      to say `workflowBaselineVersion`.
- [ ] `CHANGELOG.md`'s header note ("version numbers follow the
      `frameworkVersion` tracked in generated projects' `.meridian/manifest.json`,
      not a separate release cadence") is rewritten — under the new design
      this is exactly backwards: `frameworkVersion` now *is* the release
      cadence, and it is `workflowBaselineVersion` that follows a separate,
      slower cadence.
- [ ] `python3 scripts/check_repository.py` passes (in particular
      `check_local_markdown_links()` — verify no links break from any
      rewording).

## 📁 Relevant Files

| File | Role |
|------|------|
| `README.md` | Framework upgrades section. |
| `CONTRIBUTING.md` | Migrations/release guidance. |
| `migrations/README.md` | Baseline-snapshot pruning description. |
| `CHANGELOG.md` | Header note above `## [Unreleased]`. |

## 🧩 Technical Context

- **Current behavior**: all four documents describe a single version number
  serving both roles.
- **Desired behavior**: each document accurately describes the three-axis
  model landed in tasks 015-019, in plain prose (no code changes in this
  task).

## 🔨 Suggested Implementation

1. Read each file's current wording end to end (per `CONTRIBUTING.md`'s own
   "read the relevant document end to end" rule).
2. Rewrite only the passages that state or imply the single-version model;
   avoid unrelated formatting changes (`CONTRIBUTING.md` explicitly asks
   for this).
3. Cross-check against the ADR (design session 2026-09-12/13) for exact
   terminology (`frameworkVersion`, `workflowBaselineVersion`,
   `protocolVersion`).

## ⚠️ Constraints and Considerations

- Repository text is English-only (`CONTRIBUTING.md`'s language invariant).
- Depends on 015, 017, and 019 landing first so the documentation describes
  shipped behavior, not the design intent alone.

## 🔗 Dependencies

- **Depends on**: 015, 017, 019
- **Blocks**: 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/020-docs-version-split.md)"$'\n\nExecute this task in the current project.'
```
