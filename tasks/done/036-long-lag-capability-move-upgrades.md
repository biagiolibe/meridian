# Task 036 — Plan capability moves correctly across long-lag consumer upgrades

> **ID**: `036`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2–3h
> **Assigned to**: unassigned

## Objective

Allow a governed-SDD consumer locked before the additive/retirement router
releases to plan a safe upgrade through those migrations. The current planner
evaluates retirement migration `038-compact-entry-point-routers` source hashes
against a much older installed baseline, so it reports a false conflict before
it can account for intermediate migrations that establish the declared source
marker version. Fusa at framework version `1.1.23` demonstrates the failure
when planning to the current framework release.

## Acceptance Criteria

- A fixture locked to a pre-router baseline with project-owned entry-point
  customization and unmodified protected marker blocks plans the complete
  upgrade without a false capability-move conflict solely because its installed
  baseline predates the retirement move's source version.
- Applying that conflict-free fixture plan preserves all project-owned
  entry-point text, installs the intermediate managed role documents, and
  retains only the target release's intended marker locations.
- A fixture with an actually modified or duplicated protected source marker
  still produces a blocking conflict with no partial write.
- The same regression coverage includes an explicit Claude pointer input when
  the supported pointer semantics apply.
- `python3 -m unittest discover -s tests -v` and
  `python3 scripts/check_repository.py` pass.

## Relevant Files

| File | Role |
|---|---|
| `scripts/meridian.py` | Upgrade planning and capability-move safety checks. |
| `migrations/037-additive-role-procedures.json` | Establishes additive managed role homes. |
| `migrations/038-compact-entry-point-routers.json` | Declares the retirement moves that expose the long-lag planning bug. |
| `tests/test_meridian_cli.py` | Fixture coverage for planning, application, preservation, and blocking conflicts. |

## Technical Context

- Fusa's manifest is locked at `1.1.23`; its entry points carry legitimate
  project-owned text and the installed baseline contains older marker forms.
- A current `meridian upgrade --project /Users/biagioliberto/dev/src/fusa --check`
  reports `CONFLICT AGENTS.md` and `CONFLICT CLAUDE.md` for migration 038's
  source checks before any write.
- The safety invariant is not negotiable: a real local protected-marker edit
  must remain a conflict. The fix may change how the planner derives the
  expected source state across pending migrations, but it must not weaken the
  exact-marker proof or overwrite consumer text.

## Constraints and Considerations

- Do not special-case Fusa paths, names, hashes, or current checkout state.
- Do not hand-copy or reconstruct a consumer's router content as an upgrade
  workaround.
- Preserve existing vanilla, customized-source, and explicit-pointer upgrade
  behavior.
- The task unblocks Fusa's separately governed `TASK-029`; it does not modify
  Fusa or mark any Fusa task complete.

## Dependencies

- **Depends on**: none
- **Blocks**: Fusa `TASK-029` externally.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Completion

After validation, update the matching queue and project-plan records if
applicable, then archive this task according to Lean Delivery.

## Delivery Evidence

- `python3 -m unittest discover -s tests -v` — passed (148 tests).
- `python3 scripts/check_repository.py` — passed.
- `git diff --check` — passed.
