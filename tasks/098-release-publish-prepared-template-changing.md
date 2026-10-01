# Task 098 — Let `release.py publish` release an already-prepared template-changing release

> **ID**: `098`
> **Category**: Release tooling
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Design review of Tasks 093 and 094 while writing Task 097

## Objective

A template-changing release cannot go through `scripts/release.py` today.
`scripts/check_repository.py` forbids a migration that targets a version ahead
of `VERSION`, so the task that adds the migration must also bump `VERSION`,
`.claude-plugin/plugin.json`, the ledger, and the changelog (the precedent of
migration `055`). But `release.py prepare` requires a version strictly greater
than the current `VERSION`, and `release.py publish` requires `HEAD` to be a
`Release <version>` commit created by `prepare` that touches only four files.
Neither precondition can hold for a release that is already fully prepared on
`main`.

Make `publish` (and `verify`, where applicable) work from the repository state
instead of from the shape of one commit, so both release kinds can be published
with the same command, and make `prepare` explain the situation instead of
failing obscurely.

## Acceptance Criteria

- [ ] `release.py publish --confirm v<version>` no longer requires that `HEAD`
  is a commit named `Release <version>`, that it touches only the four release
  files, or that its parent is the previous `origin/main` tip. A release
  prepared by `prepare` still publishes exactly as before.
- [ ] `publish` instead requires, each with a specific message and nothing
  pushed on failure: the branch is `main`; the working tree is clean;
  `origin/main` is an ancestor of `HEAD`; `VERSION`,
  `.claude-plugin/plugin.json`, and the newest `releases/*.json` agree and the
  ledger `gitTag` equals `v<VERSION>`; `CHANGELOG.md` has a `## [<VERSION>]`
  section accepted by `scripts/prepare_release.py`; the tag exists neither
  locally nor on `origin`; and the validation commands of Task 093 pass on
  `HEAD`.
- [ ] A template-changing release is accepted only when its ledger record has
  `baselineChanged: true` and lists migrations that exist and target the
  release version, and a CLI-only release only when it lists none. The kind line
  in the changelog must agree, which `prepare_release.py` already enforces.
- [ ] The summary printed before the confirmation lists every commit that will
  be pushed (`origin/main..HEAD`), the version, the ledger kind, the migration
  ids if any, and the destination, so a multi-commit publish is reviewed rather
  than hidden.
- [ ] `release.py prepare` detects a release that is already prepared (the
  current `VERSION` is newer than the newest published tag, or migrations
  already target the current `VERSION`) and exits non-zero with a message that
  says so and names `publish` as the next command, instead of failing with
  `new version … must be greater`. A normal `prepare` for a CLI-only release is
  unchanged.
- [ ] `release.py verify` and the push order, confirmation, wait, and
  forbidden-flag rules of Tasks 094 and 096 are unchanged.
- [ ] Tests, using temporary Git repositories and a local bare `origin`, cover:
  publishing a release prepared by `prepare`; publishing a template-changing
  release whose files were bumped by an ordinary commit; a multi-commit
  `origin/main..HEAD`; each state precondition failure; a ledger/migration
  mismatch; and the `prepare` message for an already-prepared release. No test
  uses the network.
- [ ] `CONTRIBUTING.md` describes both paths: a CLI-only release goes through
  `prepare` then `publish`, a template-changing release has its version,
  ledger, and changelog bumped by the task that adds the migration and then goes
  straight to `publish`.
- [ ] `CHANGELOG.md` records the change under `[Unreleased]`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `publish_preflight`, `publish_main`, `preflight` and `derive_release` in `prepare`. |
| `tests/test_release.py` | Existing release tests and new state-based cases. |
| `CONTRIBUTING.md` | Release procedure for both kinds. |
| `CHANGELOG.md` | `[Unreleased]` entry. |

## Technical Context

- **Current code**: `publish_preflight` checks `HEAD`'s subject, that the commit
  touches only the four release files, and that its parent is the previous
  `origin/main` tip. `preflight` in `prepare` rejects any version not greater
  than `VERSION`, and `derive_release` requires every introduced migration to
  target the new version, so the template-changing branch of `prepare` can only
  succeed if the migration is committed ahead of `VERSION`, which
  `check_repository.py` rejects.
- Migration `055` shows the working precedent: one task adds the migration and
  bumps `VERSION`, the plugin manifest, the ledger, and the changelog together.
- The safeguards removed from `publish` (single release commit) are replaced by
  state checks, the commit list in the summary, the typed confirmation, and the
  CI workflow's own consistency check in `prepare_release.py`.
- Lean Delivery applies: maintainer tooling, no change to the adopter-facing
  `meridian` CLI.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_release.py'`
- Evidence tier: preconditions, summaries, and push order are program-computed
  and asserted against recorded test doubles; no manual evidence is required.

## Out of scope

Creating migrations, bumping versions for a template-changing release (done by
the migration task), changing `check_repository.py`'s rule on migrations ahead of
`VERSION`, the workflow retry (Task 096), and publishing any release.

## Dependencies

- **Depends on**: 094, 095
- **Blocks**: none
- **Note**: Task 096 edits the same file, `scripts/release.py`, in
  `wait_for_publication` and `main`; integrate the two one at a time.
