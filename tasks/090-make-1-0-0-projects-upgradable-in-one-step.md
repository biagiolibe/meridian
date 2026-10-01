# Task 090 — Make a 1.0.0 project reach the current release in one step

> **ID**: `090`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h (investigate first; split if the fix is larger)
> **Assigned to**: unassigned
> **Session**: Task 068 evidence gathering

## Objective

Decision 6 in `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` originally promised that
every release from the `1.0.0` baseline forward reaches the newest release in a
single `upgrade --apply`. Task 068 found that a pristine `1.0.0` Governed SDD
project cannot be adopted onto the current framework without conflicts, and
narrowed the window to `v1.1.49` forward. Make `1.0.0` projects adoptable
again and, if so, widen the window back, or keep the narrower window.

## Acceptance Criteria

- [ ] The cause of the conflicts below is identified and recorded.
- [ ] A `1.0.0` project reaches the current release without conflicts (adopt
  followed by upgrade, or the documented equivalent), proved by a test that
  uses the unmodified `release-baselines/1.0.0` templates and the real
  `migrations/`; then Decision 6, README, and CONTRIBUTING are widened to
  `1.0.0`. Otherwise the developer confirms the narrower window stays.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Technical Context

Reproduction (framework root = this repository, no test fixtures):

```bash
cp -R release-baselines/1.0.0/templates/workflows/governed-sdd/. "$PROJECT"
python3 scripts/meridian.py adopt --mode governed-sdd --from 1.0.0 --check --project "$PROJECT"
```

Result: `BLOCKED: 3 conflict(s)`:

- `AGENTS.md` and `CLAUDE.md` — capability move
  `038-compact-entry-point-routers` source does not match the installed
  baseline.
- `docs/workflows/REVIEW.md` — the same move's target file is missing.

With migrations capped at `037` (`VERSION` `1.1.34`), `adopt --from 1.0.0
--apply` already conflicts: `037-additive-role-procedures` reports the
`AGENTS.md` and `CLAUDE.md` move sources as not matching the installed
baseline. The existing test `test_adopt_applies_packaged_legacy_migrations`
passes only because its framework stops at `1.1.0`.

## Dependencies

- **Depends on**: 068 (evidence), 049
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/090-make-1-0-0-projects-upgradable-in-one-step.md)"$'\n\nExecute this task in the current project.'
```
