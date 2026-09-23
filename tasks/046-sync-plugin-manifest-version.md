# Task 046 — Keep `.claude-plugin/plugin.json` version in sync with `VERSION`

> **ID**: `046`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~45min
> **Assigned to**: unassigned
> **Session**: 2026-09-23 release-management gap review

## 🎯 Objective

`.claude-plugin/plugin.json` declares `"version": "1.1.39"` while `VERSION`
is `1.1.41`. Claude Code adopters see the plugin version, so the drift makes
the public release number wrong for them. Realign the field and add a
repository check so the two values can never diverge again, before the first
public release (task 021) is cut.

## 📋 Acceptance Criteria

- [ ] `.claude-plugin/plugin.json`'s `version` equals the content of
      `VERSION` at the time this task lands.
- [ ] A new `check_plugin_version()` in `scripts/check_repository.py` fails
      when `plugin.json`'s `version` differs from `VERSION`, and is called
      from `main()`.
- [ ] Test fixtures in `tests/test_check_repository.py`: matching versions
      pass; a mismatched `plugin.json` version fails with a message naming
      both values.
- [ ] `CONTRIBUTING.md` (or the release procedure written by task 020, if it
      has landed) lists the `plugin.json` bump as a release step.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `.claude-plugin/plugin.json` | Plugin manifest with the drifted `version`. |
| `VERSION` | Source of truth for `frameworkVersion`. |
| `scripts/check_repository.py` | Add `check_plugin_version()`, wire into `main()`. |
| `tests/test_check_repository.py` | Add passing/failing fixtures. |
| `CONTRIBUTING.md` | Release-step note. |

## 🧩 Technical Context

- **Current behavior**: `check_required_files()` only checks that
  `plugin.json` exists and `check_json()` only checks that it parses; no
  check compares its `version` with `VERSION`, and it has drifted two
  releases behind.
- **Desired behavior**: `VERSION` stays the single source of truth for
  `frameworkVersion`; `plugin.json` mirrors it and the repository check
  enforces the mirror.

## 🔨 Suggested Implementation

1. Set `plugin.json`'s `version` to the current `VERSION`.
2. Implement `check_plugin_version(root: Path = ROOT)` with a `root`
   parameter so tests can point it at a fixture directory (same pattern as
   `check_capability_marker_baselines`).
3. Add the fixtures and the release-step note.

## ⚠️ Constraints and Considerations

- Do not generate `plugin.json` from `VERSION` at build time; Meridian has no
  build step and the plugin is installed straight from the checkout.
- A prerelease `VERSION` is out of scope here (task 018 governs it); compare
  the raw strings.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/046-sync-plugin-manifest-version.md)"$'\n\nExecute this task in the current project.'
```
