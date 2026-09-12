# Task 018 — Persist-time SemVer guard for prerelease `frameworkVersion`

> **ID**: `018`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

A prerelease `frameworkVersion` (e.g. `1.2.0-rc.1`) must never be written
into a project manifest or become a migration's `to`/a release record. Add a
rejection check at the two points where a version value becomes durable
(`lock`, `upgrade --apply`), without rewriting the shared `version_key()`
comparator used across upgrade planning. Also add full SemVer parsing for
display purposes (`meridian --version`).

## 📋 Acceptance Criteria

- [ ] `meridian lock --project <path> --mode <mode>` fails with a clear
      error when the framework source's `VERSION` carries a `-PRERELEASE`
      suffix.
- [ ] `meridian upgrade --apply` fails the same way when the target
      framework `VERSION` carries a `-PRERELEASE` suffix (before any file is
      touched).
- [ ] `version_key()` itself is unchanged — the rejection is a separate,
      isolated check at the two call sites above, not a rewrite of the
      shared comparator.
- [ ] `meridian --version` (or equivalent CLI surface) parses and displays
      full SemVer, including prerelease and build metadata when present.
- [ ] Build metadata (`+BUILD`) is accepted in `VERSION` for local/dev use,
      ignored for precedence, and never propagated into a manifest,
      migration record, or release record.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass, including new tests
      for the rejection paths.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `read_version`, `version_key`, `lock_project`, `apply_plan`/`apply_upgrade`, CLI argument parsing (`main()`). |
| `tests/test_meridian_cli.py` | Add prerelease-rejection fixtures. |

## 🧩 Technical Context

- **Current behavior**: `version_key()` splits `VERSION` on `.` and
  `int()`s each part; a prerelease suffix like `1.2.0-rc.1` would already
  raise `MeridianError("invalid framework version: ...")` today, but only
  as an incidental parse failure with a generic message, not a deliberate,
  documented policy.
- **Desired behavior**: a small, separate SemVer-aware parser (only for
  display) recognizes `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`; the
  persistence call sites (`lock`, `upgrade --apply`) explicitly check for
  and reject a prerelease suffix with a purpose-built error message, rather
  than relying on `version_key()`'s incidental failure mode.

## 🔨 Suggested Implementation

1. Add a small SemVer parser (e.g. `parse_semver(value: str) -> SemVer`)
   returning major/minor/patch/prerelease/build, used only for `--version`
   display and the new guard — not wired into `version_key()`.
2. In `lock_project` and `apply_plan`/`apply_upgrade`, call the parser on
   the target framework version and raise `MeridianError` with a clear
   message if `prerelease` is non-empty.
3. Wire `meridian --version` (add the flag if it doesn't exist) to print
   the parsed, human-readable SemVer string.

## ⚠️ Constraints and Considerations

- Do not change `version_key()`'s behavior or signature — every upgrade
  planning code path built on it (task 015) must stay untouched.
- Depends on task 015 for the manifest shape the guard protects.

## 🔗 Dependencies

- **Depends on**: 015
- **Blocks**: 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/018-prerelease-version-guard.md)"$'\n\nExecute this task in the current project.'
```
