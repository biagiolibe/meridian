# Task 156 — Stop `release.py` passing `--repo` to `gh api`

> **ID**: `156`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Publication of 1.2.8, 2026-10-04

## Objective

`python3 scripts/release.py publish` and `release.py verify` end with
`publication verification could not be completed` and `unknown flag: --repo`
when the installed GitHub CLI is 2.98.0. The latest-release check in
`scripts/release.py` (~line 600) runs
`gh api repos/<repository>/releases/latest --repo <repository>`, but `gh api`
has no `--repo` flag; the endpoint already names the repository. As a result
the last verification steps never run: the check that the release is published,
stable, and the latest, and the `self-check --check-latest` that follows it. On
1.2.8 the pushes, the workflow, and the GitHub Release were fine; only the
automatic verification failed, so a maintainer must verify by hand.

The unit tests did not catch it: `tests/test_release.py` fakes `gh` and asserts
the argument list that contains `--repo` (~line 520), so they pin the defect.

## Acceptance Criteria

- [ ] The latest-release check calls `gh api repos/<repository>/releases/latest`
  with no `--repo` argument, and `release.py publish` and `verify` complete the
  check and run `bin/meridian self-check --check-latest` on a real `gh`
  2.98.0 (proved once by running `release.py verify --version 1.2.8`
  read-only against the published release).
- [ ] The other `gh` calls that take `--repo` (`gh release view`, `gh run
  list`, `gh run watch`) are unchanged, because those subcommands accept it.
- [ ] The tests assert the corrected argument list and add a guard that fails if
  a `gh api` invocation in `scripts/release.py` carries `--repo`, for example a
  fake `gh` that rejects flags `gh api` does not define, so the mock can no longer
  hide an invalid flag.
- [ ] `release.py` failure messages are unchanged for genuine `gh api` errors
  (non-zero exit, invalid JSON, unexpected shape).
- [ ] One changelog fragment states the fix.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `gh api` call in the post-push verification (~line 600). |
| `tests/test_release.py` | Fake `gh` and the asserted argument list (~lines 354, 519–575). |
| `CONTRIBUTING.md` | Release procedure; change only if it names the flag. |

## Technical Context

- Observed on 2026-10-04 with `gh version 2.98.0`: `publish` printed
  `unknown flag: --repo` after the pushes, then the manual-continue commands;
  `release.py verify --version 1.2.8` failed the same way. `gh run list`
  and `gh release view v1.2.8` showed a successful workflow and a published,
  non-draft release.
- `{owner}/{repo}` placeholders in a `gh api` endpoint resolve from the current
  directory or `GH_REPO`; the explicit `repos/<repository>/…` form needs neither.
- Fixes land only in the newest release; no tag is moved or created by this task.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Publishing a release, moving or creating a tag, and changing the verification
policy or the other `gh` commands.

## Dependencies

- **Depends on**: —
- **Blocks**: none
