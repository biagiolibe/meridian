# Task 091 — Record the 1.2.0 marketplace install evidence

> **ID**: `091`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Developer migration from `meridian@meridian-local` to `meridian@meridian` after release 1.2.0

## Objective

Record in `docs/HOST_CAPABILITY_CONTRACT.md` what the real migration to the
published tag `v1.2.0` proved, and keep every claim it did not prove labelled
`unverified`. Task 065 left the `meridian@meridian` name unverified because no
tag carried it; release 1.2.0 is the first.

## Acceptance Criteria

- [x] The contract section "Verified Claude Code marketplace install probe"
  gains a dated subsection for the `v1.2.0` migration. It states the Claude
  Code version used (`claude --version`, captured when the task runs), that
  the run was the developer's real user-scope installation and not an isolated
  `CLAUDE_CONFIG_DIR`, and that the commands were entered in the interactive
  `/plugin` interface.
- [x] The subsection records these results as verified, each with its
  evidence source:
  - `/plugin marketplace add biagiolibe/meridian#v1.2.0` registered the
    marketplace `meridian` with source `github`, repo `biagiolibe/meridian`,
    `ref: v1.2.0` (`known_marketplaces.json`).
  - `/plugin install meridian@meridian` installed version `1.2.0` at the
    commit that the tag `v1.2.0` points to (`installed_plugins.json`,
    `gitCommitSha`, compared with `git ls-remote origin refs/tags/v1.2.0`).
  - The old `meridian@meridian-local` entry and its `enabledPlugins` key were
    gone and `meridian@meridian` was enabled after the migration, without a
    manual `settings.json` edit.
  - The cache holds `bin/meridian` for `1.2.0`, and `self-check` runs and
    prints its usage.
  - The `/plugin` detail view lists the commands, skills, and hooks of
    `1.2.0`.
- [x] The existing "Still unverified" paragraph is rewritten so the
  `meridian@meridian` name against a published tag is no longer listed, while
  these remain explicitly `unverified`: `/plugin marketplace update meridian`
  for an unpinned marketplace moving to a newer release, `${CLAUDE_PLUGIN_ROOT}`
  expansion inside a live Claude session, and everything about Codex.
- [x] A leftover cache directory of the old marketplace
  (`~/.claude/plugins/cache/meridian-local/`) is recorded as an observed
  side effect of the migration, not as a defect, and the migration notes in
  `README.md` and `CHANGELOG.md` mention that the directory can be deleted if
  the README does not already say so.
- [x] If the developer supplies direct evidence that a hook command using
  `${CLAUDE_PLUGIN_ROOT}` ran from the installed plugin in a new session, that
  evidence is recorded and the item moves to verified. Without it the item
  stays `unverified`; the `/plugin` detail view alone is not accepted as proof.
- [x] No tracked file contains a machine-specific absolute path; paths are
  written relative to `~` or to the plugin cache root.
- [x] `python3 scripts/check_repository.py` passes.

## Relevant Files

| File | Role |
|------|------|
| `docs/HOST_CAPABILITY_CONTRACT.md` | Probe results and the "Still unverified" paragraph. |
| `README.md`, `CHANGELOG.md` | Migration notes; only the leftover-cache sentence, if missing. |

## Technical Context

- **Evidence gathered on 2026-10-01** (read-only inspection after the
  developer ran the four migration commands): `installed_plugins.json` lists
  `meridian@meridian` version `1.2.0` with `gitCommitSha` equal to the commit
  of `v1.2.0`; `known_marketplaces.json` lists the marketplace `meridian` with
  `ref: v1.2.0` and no `meridian-local`; `enabledPlugins` holds
  `meridian@meridian: true` and no `meridian@meridian-local`; the cache
  directory `cache/meridian/meridian/1.2.0/bin/meridian` exists.
- The implementer must re-read those files at task time rather than trust this
  summary, and record only what is still true.
- This is a documentation-only change; unit tests are not required to exercise
  it, and that skip is recorded in the handoff.

## Validation

- `python3 scripts/check_repository.py`
- Documentation-only: build and unit-test commands are skipped and the skip is
  recorded.

## Out of scope

Verifying unpinned `marketplace update`, Codex plugin behavior, any change to
the CLI or the plugin, and deleting the leftover cache directory.

## Dependencies

- **Depends on**: 065, 089
- **Blocks**: none
