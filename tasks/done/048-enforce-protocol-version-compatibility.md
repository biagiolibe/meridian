# Task 048 — Enforce `protocolVersion` compatibility in the CLI

> **ID**: `048`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: 2026-09-23 release-management gap review

## 🎯 Objective

`protocolVersion` is one of the three version axes introduced by the
version-split design (tasks 015-021), but `scripts/meridian.py` only ever
writes it (`PROTOCOL_VERSION = 1`) and never reads it back. A CLI that
receives a manifest written by a newer, incompatible protocol would silently
misread it. Define the compatibility rule and enforce it wherever the CLI
loads a project manifest.

## 📋 Acceptance Criteria

- [x] Loading a manifest whose `protocolVersion` is greater than the CLI's
      `PROTOCOL_VERSION` fails before any file is touched, with a message
      telling the adopter to update their Meridian checkout.
- [x] A manifest without `protocolVersion` (legacy) is treated as protocol
      `1` and keeps working.
- [x] A manifest with a lower `protocolVersion` is accepted, and
      `upgrade --apply` rewrites it to the current value (already the case at
      the write site; add a test that proves it).
- [x] The rule for when to bump `PROTOCOL_VERSION` (a change in manifest
      shape or semantics that an older CLI cannot safely read) is
      documented next to the constant and in `CONTRIBUTING.md`'s release
      procedure.
- [x] Tests in `tests/test_meridian_cli.py` cover newer, equal, lower, and
      missing `protocolVersion` for at least `upgrade --check` and one other
      manifest-reading command.
- [x] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `PROTOCOL_VERSION`, `load_manifest`, manifest write sites. |
| `tests/test_meridian_cli.py` | Compatibility fixtures. |
| `CONTRIBUTING.md` | Bump rule. |

## 🧩 Technical Context

- **Current behavior**: `protocolVersion` is written into the manifest on
  lock/adoption and upgrade apply, but no read path checks it.
- **Desired behavior**: `load_manifest` (or one helper it calls) is the
  single enforcement point, so every command that reads a manifest inherits
  the guard.

## 🔨 Suggested Implementation

1. Add `check_protocol_compatibility(manifest)` and call it from
   `load_manifest`.
2. Default a missing field to `1`; reject non-integer values with a clear
   error.
3. Add the tests and documentation.

## ⚠️ Constraints and Considerations

- Do not bump `PROTOCOL_VERSION` in this task. Task 015 adds
  `workflowBaselineVersion` with a legacy fallback, so an older CLI can still
  read the new manifest; confirm this during implementation and record the
  conclusion in the completion note.
- Keep the check independent of `version_key()`; protocol versions are plain
  integers.

## Completion note

Task 015's `workflowBaselineVersion` addition has a safe fallback to
`frameworkVersion` for legacy manifests. Older readers can continue to read
the manifest shape safely, so `PROTOCOL_VERSION` remains at 1.

## 🔗 Dependencies

- **Depends on**: 015
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/048-enforce-protocol-version-compatibility.md)"$'\n\nExecute this task in the current project.'
```
