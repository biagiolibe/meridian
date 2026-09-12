# Task 021 — Ship the first CLI-only release as end-to-end proof

> **ID**: `021`
> **Category**: Release
> **Priority**: 🟢 P3
> **Estimate**: ~30min
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

Prove the whole design (tasks 015-020) works end to end by cutting a real
CLI-only release: bump `VERSION` with no accompanying migration, publish its
`releases/<version>.json` record, tag it, and verify a previously-locked
project sees a non-trivial framework delta with zero baseline changes.

## 📋 Acceptance Criteria

- [ ] `[Unreleased]` in `CHANGELOG.md` moved to a new `## [X.Y.Z]` heading
      describing the CLI-only fix/change.
- [ ] `VERSION` bumped; no new migration record added.
- [ ] `releases/<version>.json` written per task 019's schema, with
      `baselineChanged: false` and `migrations: []`.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.
- [ ] Git tag `v<version>` created; GitHub Release published from the tag
      with the `CHANGELOG.md` section as its body, linking
      `releases/<version>.json`.
- [ ] Manual end-to-end verification against a locked test project (fixture
      or scratch project): `meridian upgrade --check` before this release
      reports `<old> -> <old>`; after pulling the new framework source, it
      reports a non-trivial framework delta and an unchanged, zero-conflict
      baseline plan; `--apply` changes only manifest fields.

## 📁 Relevant Files

| File | Role |
|------|------|
| `CHANGELOG.md` | New version heading. |
| `VERSION` | Bumped. |
| `releases/<version>.json` | New record. |

## 🧩 Technical Context

- **Current behavior**: no release has ever been CLI-only under the old
  single-version model; this is the first one and the practical validation
  that tasks 015-020 actually solved the reported problem.
- **Desired behavior**: matches the ADR's public release procedure exactly,
  skipping the migration step because this release changes no managed
  template.

## 🔨 Suggested Implementation

1. Pick or confirm the CLI-only change this release ships (could be as
   small as a documentation/CLI polish fix already pending, or simply the
   completion of this task series itself framed as a CLI change).
2. Follow the release procedure: changelog entry, `VERSION` bump,
   `releases/<version>.json`, validation, commit, tag, GitHub Release.
3. Run the manual verification against a scratch/fixture project locked to
   the prior version.

## ⚠️ Constraints and Considerations

- This is a real public release — confirm with the user before tagging and
  pushing (destructive/visible action per the session's action-category
  rules).
- Depends on 016, 018, 019, and 020 all landing first, so the release
  reflects the complete, documented design.

## 🔗 Dependencies

- **Depends on**: 016, 018, 019, 020
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/021-first-cli-only-release.md)"$'\n\nExecute this task in the current project.'
```
