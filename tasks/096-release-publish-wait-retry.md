# Task 096 — Retry the workflow lookup in `release.py publish` and add `verify`

> **ID**: `096`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: First real run of `release.py publish` for v1.2.1

## Objective

`release.py publish` looks up the `Publish release` workflow run immediately
after pushing the tag. GitHub had not created the run yet, so the lookup
returned an empty list and the command failed with
`workflow lookup returned no Publish release run for v1.2.1: list index out of
range`, although `main` and the tag were already pushed and the release
published about a minute later. Make the lookup wait for the run to appear,
identify the right run exactly, fail with a clear state message when it never
appears, and give the maintainer a read-only way to resume verification after
the tag exists.

## Acceptance Criteria

- [ ] After the tag push, the command polls `gh run list` for the run until it
  appears or a timeout elapses (default: every 5 seconds for up to 120 seconds).
  The interval and timeout are named constants in `scripts/release.py`.
- [ ] The run is identified by its `headSha` equalling the commit the tag
  points to and by the `push` event, using a limit large enough to see recent
  runs (not `--limit 1`). A run for another commit or event is ignored.
- [ ] A failing `gh run list` call or invalid JSON during the polling window is
  treated as transient and retried; the last error is reported only if the
  timeout elapses.
- [ ] If no matching run appears before the timeout, the command exits non-zero
  with a message that states: the push of `main` and of the tag completed, the
  workflow run was not observed, nothing was retried or moved, and the exact
  manual commands to continue (`gh run list`, `gh release view`, and the
  `verify` command below). The message never contains a raw Python exception
  text such as `list index out of range`.
- [ ] A new `release.py verify --version X.Y.Z` performs only the waiting and
  verification half of `publish`: it requires that the tag exists on `origin`,
  runs the same polling, workflow watch, release checks, and `self-check`, and
  runs no `git push`, `git tag`, or any other write. It exits non-zero when the
  workflow fails or the release is not published, stable, and latest.
- [ ] The existing behavior is unchanged: the workflow-failure path never
  moves or deletes the tag, `--no-wait` and the missing-`gh` paths still print
  the manual URLs, and every recorded Git invocation still contains no
  `--force`, `--force-with-lease`, or `--delete`.
- [ ] Tests replace `gh`, the clock, and `sleep`, so none waits in real time or
  uses the network. They cover: the run appearing on the third poll, a run for
  another commit being ignored, a transient `gh` error followed by success,
  timeout with the state message and no raw exception text, `verify` succeeding,
  `verify` with a missing remote tag, `verify` issuing no write command, and
  the unchanged failure path.
- [ ] `CONTRIBUTING.md` describes the wait, the timeout message, and `verify`,
  and `release.py --help` lists `verify` as read-only.
- [ ] `CHANGELOG.md` records the fix under `[Unreleased]`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `wait_for_publication`, `main` dispatch, new `verify`. |
| `tests/test_release.py` | Existing publish tests and new polling tests. |
| `CONTRIBUTING.md` | Release procedure and failure handling. |
| `CHANGELOG.md` | `[Unreleased]` entry. |

## Technical Context

- **Observed on 2026-10-01**: after `publish --confirm v1.2.1` pushed the
  commit and the tag, the lookup ran at once and found nothing. The run
  `Publish release` for `v1.2.1` was in progress 36 seconds later and succeeded;
  the release was `Latest` and not a draft. The command had reported failure for
  a release that was fine.
- **Current code**: `wait_for_publication` calls
  `gh run list --workflow "Publish release" --branch v<version> --limit 1
  --json databaseId,url` once and reads `entries[0]`; an empty list raises
  `IndexError`, which becomes the message above.
- `publish` refuses to run again once the tag exists locally or on `origin`, so
  without `verify` the maintainer has no command to resume the verification and
  has to run `gh` by hand.
- Lean Delivery applies: maintainer tooling, no change to the adopter-facing
  `meridian` CLI.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_release.py'`
- Evidence tier: polling order, the selected run, messages, and the absence of
  write commands are program-computed and asserted against recorded test
  doubles; no manual evidence is required.

## Out of scope

Changing what `publish` pushes or in which order, moving or deleting tags,
updating the GitHub Actions versions or runner images used by `release.yml`,
and re-running a failed workflow.

## Dependencies

- **Depends on**: 094, 095
- **Blocks**: none
