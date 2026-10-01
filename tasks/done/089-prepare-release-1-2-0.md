# Task 089 — Prepare release 1.2.0

> **ID**: `089`
> **Category**: Release
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Developer request to prepare the first release after 1.1.50

## Objective

Prepare the repository for release `1.2.0`: close the changelog, bump the
version, add the ledger record, and classify the release. Pushing the tag
`v1.2.0` is a separate maintainer action and is out of scope.

Release `1.2.0` is chosen over `1.1.54` because it is the first release since
`v1.1.50` that adopters can install, it bundles the unpublished `1.1.51`
through `1.1.53`, adds the opt-in update check and the console launch, and
requires a one-time marketplace migration for existing Claude Code installs.

## Acceptance Criteria

- [x] `VERSION` and `.claude-plugin/plugin.json` `version` are `1.2.0`.
- [x] `CHANGELOG.md` has a `## [1.2.0]` section holding the former
  `[Unreleased]` content, with an empty `## [Unreleased]` left above it. The
  section opens with the release kind line required by Task 067.
- [x] The `1.2.0` section states that `1.1.51`, `1.1.52`, and `1.1.53` were
  never published as tags or GitHub Releases, and that an adopter upgrading
  from `1.1.50` receives migrations `053`, `054`, and `055` in one
  `upgrade --apply`. Existing `1.1.51`–`1.1.53` sections are not rewritten.
- [x] The section carries the Claude Code marketplace migration as upgrade
  notes (uninstall `meridian@meridian-local`, remove `meridian-local`, add
  `biagiolibe/meridian#v1.2.0`, install `meridian@meridian`).
- [x] `releases/1.2.0.json` exists with `gitTag: v1.2.0`, today's
  `releaseDate`, `workflowBaselineVersion: 1.1.53`, `baselineChanged: false`,
  and an empty `migrations` list, unless the classification step below finds a
  changed managed file; in that case the task stops and reports `BLOCKED`
  instead of choosing.
- [x] Classification is evidenced: the diff of managed template and workflow
  files since `1.1.53` is listed and shows no change, and the manifest written
  by the new CLI is compared with the one from `1.1.50`. `PROTOCOL_VERSION` is
  changed only if an older CLI cannot safely read the new manifest; the
  comparison and the decision are recorded in the handoff.
- [x] The README install and update commands name `v1.2.0`-style pins
  consistently with the changelog, and no tracked file contains a
  machine-specific absolute path.
- [x] `python3 scripts/check_repository.py` and
  `python3 -m unittest discover -s tests` pass, and
  `python3 scripts/prepare_release.py --tag v1.2.0 --repository
  biagiolibe/meridian --notes-file <scratch file>` succeeds locally without
  creating a tag or a release.

## Relevant Files

| File | Role |
|------|------|
| `VERSION`, `.claude-plugin/plugin.json` | Release version. |
| `CHANGELOG.md` | Release section, kind line, upgrade notes. |
| `releases/1.2.0.json`, `releases/README.md` | New ledger record; field rules. |
| `scripts/prepare_release.py` | Local dry run of the release consistency check. |
| `CONTRIBUTING.md` | Release procedure, including the manifest comparison. |

## Technical Context

- **Current state**: `VERSION` is `1.1.53`. Published tags are `v1.1.49` and
  `v1.1.50`. The ledger records for `1.1.51`–`1.1.53` name `gitTag` values
  that do not exist. `CHANGELOG.md` has a populated `[Unreleased]` section
  after the `1.1.53` section.
- **Classification**: the ledger defines `baselineChanged` as true only when
  the release itself introduces a migration. `1.2.0` introduces none, so the
  ledger says `false` even though adopters on `1.1.50` cross three migrations.
  The changelog upgrade notes carry that fact for adopters.
- Versions compare as integer tuples in `scripts/meridian.py`, so `1.2.0` sorts
  above `1.1.53`.
- A past ledger record is never edited; the dangling tags are documented in the
  changelog, not corrected in place.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- The local `scripts/prepare_release.py` dry run above.

## Out of scope

Pushing `main`, creating or pushing `v1.2.0`, publishing the GitHub Release,
and the post-release verification of `meridian@meridian`, unpinned
`marketplace update`, and `meridian self-check --check-latest` against the real
release (recorded afterwards in `docs/HOST_CAPABILITY_CONTRACT.md`).

## Dependencies

- **Depends on**: 067, 068, 069
- **Blocks**: none
- **Note**: Run after 067, 068, and 069 are integrated, so the changelog covers
  their user-visible changes and the release check enforces Task 067's rules.
