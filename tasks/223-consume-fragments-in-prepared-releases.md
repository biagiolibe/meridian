# Task 223 — Consume changelog fragments in prepared releases

> **ID**: `223`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Release 1.3.0 preparation, 2026-10-15
> **Origin**: friction

## Objective

A template-changing release is prepared by the task that adds its migration:
that task bumps `VERSION`, `.claude-plugin/plugin.json`, the release ledger,
and writes a `## [X.Y.Z]` section in `CHANGELOG.md`. From then on
`python3 scripts/release.py prepare` refuses with `release X.Y.Z is already
prepared; run python3 scripts/release.py publish --confirm vX.Y.Z`.

Changelog fragments that later tasks add to `changelog.d/` before the release
is published are never consumed on that path. `publish` and
`scripts/prepare_release.py` accept the release, so its `CHANGELOG.md` section
and GitHub Release body omit those changes, and the fragments would be
attributed to the next release. Release 1.3.0 hit this with seven fragments
(tasks 210, 213, 214, 218, 219, 221, 222); they were folded into the 1.3.0
section by hand in commit `61c67f7`.

Make the already-prepared path handle pending fragments so a release cannot be
published with unconsumed changelog entries.

## Acceptance Criteria

- [x] For an already-prepared release with pending fragments in `changelog.d/`,
  the tooling either renders them into the existing `## [X.Y.Z]` section
  (keeping its kind line first and merging any `### Upgrade notes` without
  duplicating them) and removes the consumed fragments, or `publish` preflight
  stops with a message that names the pending fragments and the command that
  consumes them. The handoff records which behavior was chosen and why.
- [x] `publish --confirm vX.Y.Z` never pushes a release while fragments remain
  in `changelog.d/` (other than `README.md`).
- [x] The prepared release with no pending fragments behaves as today.
- [x] Regression tests in `tests/` cover the pending-fragment path and the
  clean path.
- [x] `CONTRIBUTING.md` (Changelog fragments and Release procedure) describes
  the behavior for template-changing releases.
- [x] A changelog fragment `changelog.d/223.md` describes the fix.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `prepare`, `ensure_not_already_prepared`, `changelog render`, `publish_preflight`. |
| `scripts/prepare_release.py` | Release consistency check run by `release.yml`. |
| `changelog.d/README.md` | Fragment format. |
| `CONTRIBUTING.md` | Release procedure and changelog fragment rules. |
| `tests/` | Release script tests. |

## Technical Context

- **Current behavior**: `prepare` stops on an already-prepared release;
  `changelog render --write` writes fragments into `[Unreleased]`, not into the
  prepared `## [X.Y.Z]` section; `publish_preflight` does not look at
  `changelog.d/`.
- **Desired behavior**: pending fragments are either merged into the prepared
  section or block `publish` with a precise remedy.

## Suggested Implementation

1. Add a pending-fragment check to `publish_preflight` (and, if useful, to
   `prepare_release.py`).
2. Decide whether `changelog render` gains a mode that writes into the
   prepared release section, or whether `prepare` on an already-prepared
   release consumes fragments instead of refusing.
3. Add tests for both paths and update `CONTRIBUTING.md`.

## Constraints and Considerations

- The release command never creates or moves tags as part of this change;
  only its preflight and changelog handling change.
- Keep the fragment order and headings identical to `prepare`'s rendering.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## Validation

```bash
python3 scripts/check_repository.py
python3 scripts/run_tests.py --parallel
```

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/223-consume-fragments-in-prepared-releases.md)"$'\n\nExecute this task in the current project.'
```

## Completion

Implemented the explicit publication guard and `changelog render --prepared`
remedy. Pending fragments stop both already-prepared `prepare` and `publish`
with file names and the exact consumption command. The renderer preserves the
release preamble, groups existing and new subsections in canonical order, merges
Upgrade notes under one heading, and consumes fragments only with `--write`.
No-fragment prepared rendering is a byte-preserving no-op.

Validation: repository checks passed; the complete parallel suite passed all
1062 tests with no failures, errors, or skips. See `tasks/handoffs/223.md`.
