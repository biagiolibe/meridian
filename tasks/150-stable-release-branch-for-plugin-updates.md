# Task 150 — Publish a `stable` branch so the Claude Code plugin follows releases

> **ID**: `150`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Plugin update after release 1.2.7, 2026-10-04

## Objective

A Claude Code installation that declares the Meridian marketplace in
`extraKnownMarketplaces` with `"ref": "v<version>"` never sees a newer release:
after 1.2.7 was published, the developer's plugin stayed at 1.2.6 until the ref
in `~/.claude/settings.json` was edited by hand, and the README documents that
manual step for every release. Give users a ref that always names the latest
published release, so updating needs only `/plugin marketplace update meridian`,
while exact tags stay available for pinning and rollback.

## Acceptance Criteria

- [ ] `python3 scripts/release.py publish --confirm v<VERSION>` also updates the
  remote branch `stable` to the release commit, after the `main` and tag pushes
  succeed, with a plain fast-forward push (`git push origin <release-commit>:refs/heads/stable`).
  It never force-pushes, deletes, or moves a tag. If `stable` is not an ancestor of
  the release commit, publish stops before that push with a message naming both
  commits and leaves the tag and `main` as published.
- [ ] When the remote branch `stable` does not exist, the first publish creates it
  at the release commit.
- [ ] `release.py verify --version X.Y.Z` also checks, read-only, that remote
  `stable` points to the `v<X.Y.Z>` tag commit, and reports a mismatch without
  changing anything.
- [ ] `stable` only ever points to a commit that carries a `v<VERSION>` release
  tag; publish refuses to advance it otherwise. A test or check proves that the
  tagged commit's `.claude-plugin/plugin.json` version equals the tag.
- [ ] `meridian self-check` reports the plugin marketplace ref it can read from
  user settings (`extraKnownMarketplaces.meridian.source.ref`): `stable`, a tag
  that is the latest release, or a tag older than the latest release with the
  one-line remedy (switch to `stable` or to the new tag). Missing settings or an
  unreadable file are reported as unknown, never as an error. It never writes
  settings.
- [ ] The README update procedure recommends `"ref": "stable"` once, explains how
  to read the installed version (`/plugin`, `installed_plugins.json`,
  `self-check --check-latest`), and keeps exact tags as the documented way to pin
  or roll back. The `extraKnownMarketplaces` refusal note stays accurate.
- [ ] Tests cover: the publish command sequence including the `stable` push; first
  creation of `stable`; a non-fast-forward `stable` blocked before the push; verify
  with matching and mismatching `stable`; and `self-check` with `stable`, a current
  tag, an old tag, and no settings.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change and needs no migration.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `publish_main` push sequence (around the `main` and tag pushes) and `verify`. |
| `scripts/meridian.py` | `self-check` and `--check-latest` reporting. |
| `README.md` | Plugin install and update procedure. |
| `CONTRIBUTING.md` | Release procedure description of `publish`. |
| `tests/` | Release and self-check tests. |

## Technical Context

- Observed on 2026-10-04: `~/.claude/settings.json` pinned `ref` `v1.2.6`, and
  `installed_plugins.json` stayed at 1.2.6 after `v1.2.7` was published.
- The installed version remains visible with `stable`: Claude Code records the
  plugin's `version` and `gitCommitSha` in `installed_plugins.json`, and the
  version comes from `.claude-plugin/plugin.json`.
- Whether Claude Code refreshes third-party marketplaces automatically is
  unverified; the documentation must not claim it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Writing `~/.claude/settings.json` from any Meridian command, pointing users at
`main`, moving or deleting tags, and changing Codex skill distribution.

## Dependencies

- **Depends on**: —
- **Blocks**: none
