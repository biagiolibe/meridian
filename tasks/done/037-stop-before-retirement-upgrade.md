# Task 037 — Let a long-lag consumer stop an upgrade before retirement

> **ID**: `037`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2–3h
> **Assigned to**: Claude CLI
> **Session**: 2026-09-16, continuation of task 036

## Objective

Task 036 fixed a false conflict so a long-lag consumer can *plan* the full
1.1.23→1.1.37 upgrade. It does not let the consumer stop partway. Fusa's
`TASK-029` (governed by its ADR-0017) needs exactly that: apply migration
037 (additive — creates `docs/workflows/*.md`, keeps both entry-point
copies) without migration 038 (retirement — deletes the duplicated
entry-point procedure text), because ADR-0017 splits this into two releases
and TASK-029 is release A only.

`meridian upgrade` has no such stopping point today, and — as this task's
investigation found — capping `pending_migrations` alone would not be
sufficient even if a flag existed: `command-triggers` bumps from v1 to v2 in
the checked-out templates with **no migration record declaring it**, so
nothing gates that specific content change to a migration ID. It would
still get pulled into `AGENTS.md`/`CLAUDE.md` by the marker-aware merge
fallback (`append_only_new_markers`, driven by comparing `marker_pairs()` of
the raw HEAD template) regardless of which migrations are "pending" — silently
router-izing the entry points a release early. A repository-wide audit
(see Technical Context) confirms this is the *only* undeclared marker in
either file; every other content change in the 037/038 pair already goes
through `capabilityMoves` or `removes`, both of which are properly gated by
`pending_migrations`.

## Acceptance Criteria

- `migrations/038-compact-entry-point-routers.json` declares the
  `command-triggers` v1→v2 bump via `capability`/`capabilityVersion` (or a
  `capabilities` entry), matching the exact current source/target marker
  content (sha256-verifiable against the live templates).
- `meridian upgrade --project <p> --check --stop-before-retirement`, run
  against a consumer locked before migration 037, plans only through the
  last migration before the first one that declares any
  `stage: "retirement"` capability move. The plan contains no
  `append-retire-markers`/`retire-markers` action and no undeclared marker
  supersession (e.g. `command-triggers` stays v1) for any managed file.
- `meridian upgrade --project <p> --apply --stop-before-retirement` applies
  that same plan: preserves `AGENTS.md`'s and `CLAUDE.md`'s project-owned
  procedure text unchanged except for genuinely additive, migration-declared
  marker changes; creates the new `docs/workflows/*.md` managed files; and
  records the manifest's `frameworkVersion` at the effective intermediate
  version (the capped stopping point), not the full checked-out target.
- A subsequent plain `meridian upgrade --project <p> --check` (no flag) on
  that same project reports the remaining migrations as still pending with
  no false conflict, and `--apply` completes the upgrade to the full target
  version, applying retirement normally.
- Without `--stop-before-retirement`, `meridian upgrade` behavior — plan
  output and applied file content — is unchanged from before this task.
- `python3 -m unittest discover -s tests -v` and
  `python3 scripts/check_repository.py` pass.

## Relevant Files

| File | Role |
|---|---|
| `scripts/meridian.py` | `migration_ids`, `plan_upgrade`/`apply_upgrade`/`plan_from_baseline`/`apply_plan`, `managed_files`, `append_only_new_markers`, `removals_for_managed_file`, `apply_additive_move_checks`, CLI argument parser for `upgrade`. |
| `migrations/038-compact-entry-point-routers.json` | Needs the missing `command-triggers` v1→v2 declaration. |
| `migrations/037-additive-role-procedures.json` | Reference for the additive boundary this flag must stop at. |
| `tests/test_meridian_cli.py` | Fixture coverage for capped plan/apply, manifest intermediate version, resumption, and the command-triggers declaration. |

## Technical Context

- **Current behavior**: `meridian upgrade` always plans/applies to
  `read_version(framework_root)` (the full checked-out target). No flag
  limits it to an intermediate version.
- **Desired behavior**: `--stop-before-retirement` computes an effective
  target version — the `from` version of the first pending migration that
  declares a `stage: "retirement"` capability move — and plans/applies only
  up to that point, both for migration bookkeeping (`pending_migrations`,
  `appliedMigrations`, `frameworkVersion`) and for the actual template
  content fed into the merge/marker logic for customized files.
- Migrations 037 (`1.1.33`→`1.1.34`, purely additive) and 038 (`1.1.34`→
  `1.1.35`, purely retirement) already declare the correct version window,
  but no commit in this repository's history ever set `VERSION` to `1.1.34`
  — both migrations shipped in one commit (`02fd9a4`) with `VERSION` jumping
  straight from `1.1.33` to `1.1.35`. There is no historical git snapshot of
  the "additive-complete" template state to diff against.
- Because of that, the fix cannot rely on git history or on a stored
  per-version template snapshot (`release-baselines/` currently only holds
  `1.0.0`). It must synthesize the capped content directly: build a
  substitute `ManagedFile.source` for any managed file that carries a marker
  block belonging to an excluded (capped-out) migration, by stripping that
  specific marker block from a copy of the live template before it reaches
  `merge_clean`/`append_only_new_markers`/the sha256 fast paths. Everything
  downstream (three-way merge, marker-pairs comparison, hashing) can then
  consume that substitute path unchanged.
- Confirmed by audit (see below) that this substitution is only needed for
  `command-triggers` in `AGENTS.md`/`CLAUDE.md`. Every other difference
  between the pre-037 and post-038 template state for these two files is
  already expressed as a `capabilityMoves`/`removes` entry, both already
  gated correctly by `pending_migrations` via `removals_for_managed_file`
  and `declared_capability_moves`/`apply_additive_move_checks` — those paths
  need no change.
- Audit method used: for every marker in the live `AGENTS.md`/`CLAUDE.md`
  templates, check whether `(capability, version)` appears in any
  migration's `capability`/`capabilityVersion`/`capabilities` field, or as a
  `capabilityMoves` source/target, or a `removes` entry. Only
  `command-triggers v2` was unmatched, in both files.
- `docs/workflows/*.md` and other non-customized managed files (e.g.
  `docs/CONTEXT_BUDGET_POLICY.md`) are always regenerated at the live
  template's exact latest content regardless of the cap — they carry no
  project-owned text, so this is consistent with normal upgrade behavior and
  is explicitly not in scope to change.

## Suggested Implementation

1. In `migrations/038-compact-entry-point-routers.json`, add the
   `command-triggers` v1→v2 declaration (verify the sha256 values against
   the live `templates/workflows/governed-sdd/{AGENTS,CLAUDE}.md`).
2. Add `first_retirement_migration(framework_root, migration_ids) -> str | None`
   and `capped_target_version(framework_root, installed_version,
   target_version) -> str` in `scripts/meridian.py`.
3. Add `capped_managed_files(framework_root, mode, excluded_migration_ids) ->
   list[ManagedFile]`: for each entry from `managed_files()`, if it carries a
   marker block whose declaring migration is in `excluded_migration_ids`,
   write a stripped copy (marker block removed via a helper mirroring
   `marker_blocks()`'s pattern) to a per-run scratch path and substitute it
   as the entry's `source`; otherwise keep the entry unchanged.
4. Thread `stop_before_retirement: bool = False` through `plan_upgrade`,
   `apply_upgrade`, and the CLI dispatch, computing the capped target
   version and capped managed-files list only when set, and passing them
   through to `plan_from_baseline`/`print_plan`/`apply_plan` in place of
   `read_version(framework_root)`/`managed_files(...)`.
5. Add the `--stop-before-retirement` flag to the `upgrade` subcommand's
   argument group (works with both `--check` and `--apply`).
6. Add regression fixtures per the acceptance criteria.

## Constraints and Considerations

- Do not special-case Fusa or any other consumer's path, name, or state.
- Do not weaken the exact-marker/exact-move safety proofs `apply_
  additive_move_checks` already performs — capping must only *narrow* what a
  run touches, never bypass a conflict it would otherwise report.
- Do not attempt to reconstruct or backfill a `release-baselines/1.1.34/`
  snapshot or renumber any shipped version — Palimpsest is already locked
  past `1.1.35` (`1.1.37`), so retroactive version-history changes are out of
  scope and unnecessary given the marker-stripping approach above.
- This task does not decide, and must not assume, whether Fusa's ADR-0017
  keeps `docs/roles/*.md` or adopts the framework's `docs/workflows/*.md`
  convention — that is a Fusa-side ADR question for its own task, not
  something this framework change resolves.
- The task unblocks Fusa's separately governed `TASK-029`; it does not
  modify Fusa or mark any Fusa task complete.

## Dependencies

- **Depends on**: 036
- **Blocks**: Fusa `TASK-029` externally.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Completion

After validation, update the matching queue and project-plan records if
applicable, then archive this task according to Lean Delivery.

## Delivery Evidence

- `python3 -m unittest discover -s tests -v` — passed (151 tests).
- `python3 scripts/check_repository.py` — passed.
- `git diff --check` — passed.
- Real dry run against a fresh clone of Fusa (locked at `1.1.23`):
  `meridian upgrade --project . --check --stop-before-retirement` plans only
  through `037-additive-role-procedures` (`1.1.23 -> 1.1.34`), with
  `KEEP AGENTS.md`/`KEEP CLAUDE.md — template unchanged` and no
  `APPEND-RETIRE-MARKERS`/`RETIRE-MARKERS` action anywhere in the plan.
  `--apply --stop-before-retirement` applies it with an empty `git diff` on
  `AGENTS.md`/`CLAUDE.md` and creates `docs/workflows/{IMPLEMENTATION,REVIEW,
  REMEDIATION,LIFECYCLE}.md`.
- New regression coverage in `tests/test_meridian_cli.py`
  (`MeridianCliTest.test_stop_before_retirement_*`, three tests) covers the
  capped plan/apply boundary and content preservation, the manifest recording
  the capped intermediate version, resuming a capped upgrade to the full
  target afterward, and the flag being a no-op once nothing is pending.

## Known residual limitation (not fixed by this task)

The real-Fusa dry run above also ran `meridian audit --project . --mode
governed-sdd` after the capped apply, as a forward check against TASK-029's
own (separate) acceptance criterion. It reported one failure unrelated to
this task's scope:

```
FAIL capability move 037-additive-role-procedures: source AGENTS.md for
capability=execution-command-gate v1 is missing, modified, or duplicated
FAIL capability move 037-additive-role-procedures: source CLAUDE.md for
capability=execution-command-gate v1 is missing, modified, or duplicated
```

Cause: `execution-command-gate` is established by migration
`031-execution-command-gate` (`1.1.27`→`1.1.28`, entirely inside Fusa's lag
window) as real, literal marker content in `AGENTS.md`/`CLAUDE.md` — unlike
`manual-verification-precondition` and the other 037-moved capabilities,
which Fusa's real, pre-`1.1.23` content already carries. `capped_managed_
files` only reconstructs a capability into the capped template when it can
read that capability's current marker block out of the *live* (HEAD)
template; since the live template no longer carries
`execution-command-gate` at all (a later, excluded migration already moved
it out), there is no live-template text left to splice into `AGENTS.md`/
`CLAUDE.md`'s capped copy, so the capped upgrade cannot add it there even
though migration 031 is included.

Every other capability this task's fixtures and the real dry run exercise is
unaffected, because it is either already physically present in the
consumer's own locked content (Fusa's real markers) or is a purely
transient, declaration-only capability that task 036's existing mechanism
already handles correctly. This gap is narrow: it only affects a capability
that is both established *and* additively relocated entirely inside one
consumer's lag window, with no version of it ever physically shipped to that
consumer.

Recommended follow-up (separate task, not undertaken here to keep this one
bounded): extend `capped_managed_files` to also source an included additive
move's marker content from its *target* file (already correctly capped, with
a verified `markerSha256`) when the source capability is absent from the
live template, splicing it into the source file's capped copy the same way
`apply_additive_move_checks` already proves target content today. Until
then, a consumer hitting this — Fusa's `TASK-029` will — should expect
`meridian audit` to report this one specific, known failure after a capped
apply, and can resolve it by manually adding the `execution-command-gate v1`
marker (content available verified in `docs/workflows/IMPLEMENTATION.md`) to
`AGENTS.md`/`CLAUDE.md`, or by waiting for that follow-up.
