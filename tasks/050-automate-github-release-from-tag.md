# Task 050 — Automate the GitHub Release from a version tag

> **ID**: `050`
> **Category**: Infrastructure
> **Priority**: 🟢 P3
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: 2026-09-23 release-management gap review

## 🎯 Objective

Task 021 cuts the first release by hand: tag, GitHub Release, and a
`CHANGELOG.md` section copied as the body. Once that manual procedure is
proven, automate it so every later release is produced the same way from a
`v<version>` tag and cannot be published when the repository is inconsistent.

## 📋 Acceptance Criteria

- [ ] A new workflow `.github/workflows/release.yml` runs on push of tags
      matching `v*`.
- [ ] Before publishing, the workflow fails if any of these is false:
      - the tag equals `v` + the content of `VERSION` at the tagged commit;
      - `releases/<VERSION>.json` exists (task 019);
      - `.claude-plugin/plugin.json`'s `version` equals `VERSION` (task 046);
      - `python3 scripts/check_repository.py` and the unittest suite pass;
      - `CHANGELOG.md` has a `## [<VERSION>]` section.
- [ ] On success, it creates a GitHub Release for the tag whose body is that
      `CHANGELOG.md` section plus a link to `releases/<VERSION>.json`.
- [ ] The extraction logic (changelog section, consistency checks) lives in a
      small stdlib script under `scripts/` with unit tests, not inline shell
      in the workflow.
- [ ] `CONTRIBUTING.md`'s release procedure is updated: the maintainer
      pushes the tag; CI publishes the release.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `.github/workflows/release.yml` | New tag-triggered workflow. |
| `scripts/` | New release-preparation script. |
| `tests/` | Tests for the script. |
| `CONTRIBUTING.md` | Release procedure. |

## 🧩 Technical Context

- **Current behavior**: no tags, no release workflow; task 021 defines the
  first manual release.
- **Desired behavior**: a tag push is the only manual step; everything the
  release claims is verified mechanically first.

## 🔨 Suggested Implementation

1. Write `scripts/prepare_release.py` with `extract_changelog_section()` and
   `check_release_consistency()`; test both.
2. Add `release.yml` using the default `GITHUB_TOKEN` with
   `contents: write` permission and `gh release create`.
3. Update `CONTRIBUTING.md`.

## ⚠️ Constraints and Considerations

- Do not push a real tag to test the workflow without the developer's
  explicit confirmation; a real tag publishes a public release.
- Keep the workflow's permissions to the minimum it needs.

## 🔗 Dependencies

- **Depends on**: 021, 046, 047
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/050-automate-github-release-from-tag.md)"$'\n\nExecute this task in the current project.'
```
