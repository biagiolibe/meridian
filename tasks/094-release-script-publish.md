# Task 094 — Add `scripts/release.py publish`

> **ID**: `094`
> **Category**: Release tooling
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Developer request for a fast, repeatable release command

## Objective

Add the outward-facing half of the release command. After
`release.py prepare` (Task 093) has created the local release commit,
`python3 scripts/release.py publish` pushes `main`, creates and pushes the tag
`v<version>`, waits for the release workflow, and verifies the published
release. It acts only after the maintainer types the exact version, because
pushing the tag publishes the release to adopters.

## Acceptance Criteria

- [ ] Usage: `release.py publish --confirm v<version> [--no-wait]`. Without
  `--confirm` the command prints the summary and exits non-zero with nothing
  pushed. A `--confirm` value that is not exactly `v` plus the current
  `VERSION` is refused.
- [ ] Preconditions, each with a specific message and nothing pushed on failure:
  the branch is `main`; the working tree is clean; `HEAD` is the commit named
  `Release <version>` made by `prepare` (its parent is the previous `main`
  tip, and it touches only the four release files); the tag does not exist
  locally or on `origin`; `origin/main` is an ancestor of `HEAD`; and the three
  validation commands of Task 093 pass again on `HEAD`.
- [ ] The summary shows the version, the release kind from the ledger, the
  commits that will be pushed, and the destination remote and repository,
  before any push.
- [ ] Push order: `git push origin main`, then `git tag v<version>`, then
  `git push origin v<version>`. A rejected push stops the command at that step
  and says which steps completed. The command never uses `--force`,
  `--force-with-lease`, or `--delete`, and never moves or deletes a tag.
- [ ] Unless `--no-wait` is given and when `gh` is available, the command waits
  for the `Publish release` workflow run for the tag, then checks that the
  GitHub Release exists, is neither a draft nor a prerelease, and is the latest,
  and then runs `bin/meridian self-check --check-latest`, reporting each result.
  A workflow failure is reported with the run URL, states that nothing was
  published, and does not retry or move the tag.
- [ ] Without `gh`, or with `--no-wait`, the command prints the workflow and
  release URLs and the manual verification command, and exits zero when the
  pushes succeeded.
- [ ] After a successful publish the command prints, as text only, the
  adopter update steps from `README.md` (Claude Code pin move, Codex checkout
  move) and does not run them.
- [ ] Unit tests use a temporary repository with a local bare repository as
  `origin` and replace `gh` and `self-check` with test doubles. They cover: the
  missing and wrong `--confirm`, each precondition failure, the push order, a
  rejected push of `main`, an existing remote tag, the absence of any forbidden
  flag in every recorded Git invocation, the workflow failure path, and the
  `--no-wait` and missing-`gh` paths. No test uses the network.
- [ ] `CONTRIBUTING.md` release procedure describes the command, the
  confirmation, and what to do after a failed workflow.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | The `publish` subcommand, next to `prepare`. |
| `tests/test_release.py` | Publish tests with a bare local remote. |
| `CONTRIBUTING.md` | Release procedure and failure handling. |
| `.github/workflows/release.yml` | The workflow the command waits for; unchanged. |

## Technical Context

- **Why a typed confirmation**: the tag push is the only step that publishes.
  `release.yml` then verifies consistency and creates the GitHub Release. A
  published release cannot be quietly withdrawn: adopters may already have
  moved their pins.
- A failed workflow publishes nothing; the existing procedure says to fix the
  cause and move the tag only if no release exists for it. This command reports
  the state and leaves that decision to the maintainer.
- `bin/meridian self-check --check-latest` already compares the installed
  version with the latest public release and reports `UP_TO_DATE`,
  `UPDATE_AVAILABLE`, or `UNKNOWN`.
- Standard library only; `gh` is optional and only used for waiting and
  verifying.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_release.py'`
- Evidence tier: Git invocations, ordering, and messages are program-computed
  and asserted against recorded test doubles. The first real publish is
  recorded by the maintainer in the handoff and is the only manual evidence.

## Out of scope

Creating the release commit (Task 093), editing the workflow, deleting or
moving tags, publishing to any channel other than the Git tag and GitHub
Release, and updating adopter machines.

## Dependencies

- **Depends on**: 093
- **Blocks**: none
