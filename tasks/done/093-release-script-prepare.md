# Task 093 — Add `scripts/release.py prepare`

> **ID**: `093`
> **Category**: Release tooling
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Developer request for a fast, repeatable release command

## Objective

Replace the manual release preparation with one maintainer command that is local
only. `python3 scripts/release.py prepare` derives the release kind from the
repository, writes the version files, the ledger record, and the changelog
section, validates the result, and creates one local release commit. It never
touches the network and never pushes. Publishing is Task 094.

The script is framework-internal maintainer tooling, like
`scripts/prepare_release.py` and `scripts/check_repository.py`. It is not added
to the adopter-facing `meridian` CLI.

## Acceptance Criteria

- [x] Usage: `release.py prepare (--bump patch|minor|major | --version X.Y.Z)
  [--date YYYY-MM-DD]`. The version is a plain `X.Y.Z`, strictly greater than
  the current `VERSION`. The date defaults to today.
- [x] Preflight, with nothing written and a specific message per failure: the
  current branch is `main`; the working tree is clean; `VERSION`,
  `.claude-plugin/plugin.json`, and the newest `releases/*.json` agree; the new
  tag does not exist locally; `## [Unreleased]` has a non-empty body. The
  command does not fetch and does not contact the remote.
- [x] The release kind is derived, not chosen. Migrations whose `to` is newer
  than the previous ledger record's `workflowBaselineVersion` are introduced by
  this release. None: a CLI-only release (`baselineChanged: false`,
  `migrations: []`, `workflowBaselineVersion` unchanged). Any: a
  template-changing release, which requires the new version to equal every such
  migration's `to` and the `### Upgrade notes` subsection to already be written
  under `## [Unreleased]`. Otherwise the command stops with `BLOCKED` and writes
  nothing. It never creates a migration and never invents upgrade notes.
- [x] `protocolVersion` in the new ledger record is the code's
  `PROTOCOL_VERSION`. If it differs from the previous record's, the command
  stops unless `--protocol-reviewed` is given, and the message names the
  compatibility tests that `CONTRIBUTING.md` requires. When it is unchanged the
  output still states that the manifest comparison is a manual check the
  command does not perform.
- [x] Writes are limited to `VERSION`, the `version` field of
  `.claude-plugin/plugin.json`, a new `releases/<version>.json` with
  `gitTag: v<version>`, and `CHANGELOG.md`. In the changelog an empty
  `## [Unreleased]` heading stays on top and the former body moves under
  `## [<version>]`, whose first line is generated as `CLI-only release: …` or
  `Template-changing release: …`.
- [x] After writing, the command runs `python3 scripts/check_repository.py`,
  `python3 -m unittest discover -s tests`, and
  `python3 scripts/prepare_release.py --tag v<version> --notes-file <temp file>`.
  Any failure restores the four files to `HEAD` and exits non-zero with the
  failing command and its exit code.
- [x] On success the command creates exactly one local commit named
  `Release <version>` containing only those files, prints the commit, the
  derived kind, and the exact next command (`release.py publish`, Task 094),
  and exits zero.
- [x] `--dry-run` performs the preflight and prints the derived kind, the files
  it would write, and the changelog section it would produce, writing nothing.
- [x] Unit tests use temporary Git repositories and cover: each preflight
  failure, CLI-only and template-changing derivation, the missing upgrade notes
  block, the protocol gate, rollback after a failing validation command (with
  that command replaced by a test double), the commit contents, and
  `--dry-run` writing nothing. No test uses the network.
- [x] `CONTRIBUTING.md` release procedure describes the command and states that
  the manual steps remain valid and that the manifest comparison stays manual.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | New maintainer script. |
| `scripts/prepare_release.py` | Existing consistency check that the new script runs and must keep passing unchanged. |
| `tests/test_release.py` | New tests. |
| `CONTRIBUTING.md` | Release procedure. |
| `releases/README.md` | Ledger field rules the script must follow. |

## Technical Context

- **Current process**: a maintainer edits `VERSION`, `plugin.json`, the
  changelog, and the ledger by hand, runs the checks, commits, and tags. Task 067
  made `prepare_release.py` enforce the kind line and upgrade notes in CI, so
  the script generates a section that already satisfies those rules.
- Ledger rules (`releases/README.md`): `baselineChanged` is true iff
  `migrations` is non-empty; each migration must target
  `workflowBaselineVersion`; a past record is never edited.
- Versions compare as integer tuples, so `1.2.1` sorts above `1.2.0`.
- Standard library only. No new dependency.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_release.py'`
- Evidence tier: file contents, exit codes, and the commit are program-computed
  and asserted; no manual evidence is required.

## Out of scope

Pushing, tagging, waiting for CI, creating or editing migrations, writing
changelog prose or upgrade notes, comparing manifests, and changing
`prepare_release.py`.

## Dependencies

- **Depends on**: 067, 089
- **Blocks**: 094
