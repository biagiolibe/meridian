# Task 234 — Prepare the Meridian 1.4.1 CLI-only release

> **ID**: `234`
> **Category**: Release
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: 1.4.1 blocking fixes, 2026-10-18
> **Origin**: release

## Objective

Prepare Meridian 1.4.1 with the two blocking fixes from tasks 232 and 233.
Cardine ADR decision 10 keeps Meridian 1.4.x for blocking fixes until each
project converts. Cardine's own lifecycle runs on the installed Meridian, so
these fixes remove the stops that it hits most often.
Task 235 lands first so that the repository checks of the release do not
scan host checkouts nested in the primary checkout.

## Acceptance Criteria

- [ ] Prepare CLI-only 1.4.1 manually on `task-234`: update `VERSION`,
  `.claude-plugin/plugin.json`, and `releases/1.4.1.json` with release date
  `2026-10-18`, tag `v1.4.1`, protocol 2, baseline `1.4.0`,
  `baselineChanged: false`, and no migrations. Insert the 1.4.1 CLI-only
  heading and run `python3 scripts/release.py changelog render --version
  1.4.1 --prepared --write` to consume fragments 232 and 233 and match
  the section produced by the original dry-run on main. Commit these
  records in ordinary task-branch commits.
- [ ] The repository checks pass on the release commit.
- [ ] The task does not publish. It never runs `release.py publish`, pushes a
  tag, or pushes `stable`: `Proceed with` does not authorize any of these.
  The handoff gives the developer the exact publish command, `python3
  scripts/release.py publish --confirm v1.4.1`. After publishing, the
  developer updates the installed CLI with `meridian self-update`.
- [ ] Every command under Validation passes.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | Release preparation. |
| `VERSION`, `.claude-plugin/plugin.json`, `releases/`, `CHANGELOG.md`, `changelog.d/` | Release records. |
| `CONTRIBUTING.md` (Release procedure) | Procedure. |

## Technical Context

- Both fixes are CLI-only: they change no template, workflow rule, or
  managed file, so `workflowBaselineVersion` stays at 1.4.0.
- The installed CLI that Cardine and the Governed SDD projects use lives at
  `~/.local/share/meridian` and reports 1.4.0.

## Out of scope

Publishing the release, and any other fix.

## Dependencies

- **Depends on**: 232, 233, 235
- **Blocks**: none

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

- `python3 -m unittest discover -s tests`
- `python3 scripts/prepare_release.py --tag v1.4.1 --notes-file <temporary file>`

## Developer-approved scope change, 2026-10-18

The developer replaced acceptance criterion 1 after `release.py prepare`
refused the required task branch. Use the manual CLI-only procedure from
CONTRIBUTING.md, as task 231 did, rather than running prepare without
`--dry-run`. The ledger must contain exactly the fields written by prepare.
The added release checks above replace prepare's internal validation.
In a disposable clone, merge the task branch into local main and confirm
that `prepare --bump patch --dry-run` reports 1.4.1 already prepared and
names `publish --confirm v1.4.1`.
Do not publish, verify, create or push tags, or push stable. Use the installed
`meridian` CLI for all lifecycle commands. After integration, the developer
runs `python3 -m unittest discover -s tests -v` outside the agent sandbox
(the AppleScript test is skipped inside it), then
`python3 scripts/release.py publish --confirm v1.4.1` from main, then
`meridian self-update`.
