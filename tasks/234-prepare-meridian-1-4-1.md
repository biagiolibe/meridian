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

- [ ] `python3 scripts/release.py prepare --bump patch --dry-run` derives a
  CLI-only release 1.4.1 with no migration. Then `python3 scripts/release.py
  prepare --bump patch` makes the local release commit. It writes `VERSION`,
  `.claude-plugin/plugin.json`, `releases/1.4.1.json`, and `CHANGELOG.md`
  from the fragments of tasks 232 and 233.
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
