# Task 131 — Verify the latest release without the removed `isLatest` field

> **ID**: `131`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Publication of release 1.2.6, 2026-10-03

## Objective

`scripts/release.py publish` and `verify` check the published GitHub Release with
`gh release view v<version> --json isDraft,isPrerelease,isLatest,url`. With `gh`
2.98.0 the `isLatest` field no longer exists, so the command fails with `Unknown
JSON field: "isLatest"` and reports `release publish failed` after main and the
tag were already pushed and the `Publish release` workflow had succeeded. The
release itself was correct (the release was published, stable, and returned by
the `releases/latest` API as `v1.2.6`), but the final verification, the
self-check, and the adopter steps did not run. Replace the unsupported field with
a supported check, and make a verification failure after a completed push
impossible to mistake for a failed publication.

## Acceptance Criteria

- [ ] The release verification no longer requests `isLatest`. It reads the draft
  and prerelease state and URL from `gh release view` using only fields the
  current `gh` supports, and determines whether the release is the latest by
  comparing the tag returned by `gh api repos/<owner>/<repo>/releases/latest`
  with `v<version>`.
- [ ] The repository is resolved the same way the workflow lookup already does
  (`--repo` when known), so the `gh api` call targets the right repository.
- [ ] A release that is a draft, a prerelease, or not the latest still fails with
  the same clear message as today.
- [ ] If a `gh` call fails or returns an unexpected shape after the push steps
  completed, the error says so explicitly: it states that `main` and the tag were
  pushed, that nothing was retried or moved, that publication was not confirmed
  by this command, and prints the exact `release.py verify --version X.Y.Z`,
  `gh run list`, and `gh release view` commands to continue. It never uses the
  bare `release publish failed` wording for that case.
- [ ] `release.py verify` uses the same corrected check, so a read-only
  re-verification of an existing tag works and prints the self-check result and
  the adopter steps as before.
- [ ] A guard test fails if the `--json` field list passed to `gh release view`
  ever contains a field outside an explicit allowlist (`isDraft`,
  `isPrerelease`, `url`, and the other fields the code needs), so the same drift
  cannot recur silently. The fake `gh` in `tests/test_release.py` stops returning
  a field the real tool lacks.
- [ ] Tests cover: latest release accepted; the latest release being a different
  tag rejected; draft and prerelease rejected; a `gh api` failure after a
  completed push producing the explicit continuation message; and `verify`
  succeeding on an existing tag.
- [ ] The release procedure in `CONTRIBUTING.md` records the minimum supported
  `gh` behavior in one sentence and no longer implies a field that does not
  exist.
- [ ] No release, tag, or push is made by this task; it is validated with the
  fake `gh` only.
- [ ] One changelog fragment is added per `CONTRIBUTING.md` (CLI-only fix, no
  migration).
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `wait_for_publication`, the `gh release view` call, and the failure messages. |
| `tests/test_release.py` | Fake `gh` and release verification tests. |
| `CONTRIBUTING.md` | Release procedure wording. |

## Technical Context

- Observed on 2026-10-03 for release 1.2.6: the tag `v1.2.6` was on `origin`, the
  `Publish release` and `Validate repository` runs had succeeded, `gh release
  view` listed `isDraft:false, isPrerelease:false`, and `gh api
  repos/<owner>/<repo>/releases/latest` returned `v1.2.6`. `bin/meridian
  self-check --check-latest` reported `UP_TO_DATE`.
- The fields `gh release view` supported in that version are: `apiUrl`,
  `assets`, `author`, `body`, `createdAt`, `databaseId`, `id`, `isDraft`,
  `isImmutable`, `isPrerelease`, `name`, `publishedAt`, `tagName`, `tarballUrl`,
  `targetCommitish`, `uploadUrl`, `url`, `zipballUrl`.
- `publish` pushes main, creates the tag, and pushes it before verification, so a
  verification failure must never read as a failed publish; the procedure
  already forbids moving or deleting a tag.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Publishing or moving any tag, changing the release workflow, replacing `gh` with
another client, and changing which commits `publish` pushes.

## Dependencies

- **Depends on**: —
- **Blocks**: none
