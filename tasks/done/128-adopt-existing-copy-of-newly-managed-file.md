# Task 128 — Upgrade a newly managed file that the project already has

> **ID**: `128`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Upgrade rehearsal for release 1.2.6, 2026-10-03

## Objective

When a release makes a file managed for the first time, a project that already
holds a copy of it has no recorded baseline, so the upgrade planner marks the
file `CONFLICT: managed baseline is missing`
(`scripts/meridian.py`, the `base.is_file()` branch of the upgrade plan). Because
`upgrade --apply` applies nothing when any file conflicts, one such file blocks
the whole upgrade. Task 127 made Lean Delivery's `docs/WORKTREE_LIFECYCLE.md`
managed, and a Lean project created from the template already has that file, so
the 1.2.6 upgrade would fail for it. Let the upgrade adopt an existing copy of a
newly managed, framework-owned file without a blocking conflict and without a
silent overwrite.

## Acceptance Criteria

- [x] A migration can declare which of its managed paths are framework-owned
  files that a project may already hold without a baseline (for example an
  `adoptExistingPaths` list). The field is validated by the repository check and
  documented in `migrations/README.md`. Paths not declared keep today's
  `conflict` behavior.
- [x] For a declared path whose baseline is missing and whose local copy exists:
  - a copy identical to the target template is kept as is and its baseline is
    recorded;
  - a differing copy is replaced by the target template, and the previous copy
    is first preserved next to it under a documented, collision-safe name; the
    plan lists the replacement and the backup path, and the apply output repeats
    them, so no overwrite is silent.
- [x] After `upgrade --apply`, the baseline for the adopted file is recorded, so
  later upgrades use the ordinary three-way merge with no repeated adoption or
  backup.
- [x] `upgrade --check` reports the adoption as a planned, non-conflicting item
  and exits as it does for any clean plan; `--apply` stays all-or-nothing.
- [x] A declared path with no local copy still plans `ADD`, and
  `--owner-reconciled` still touches no managed file.
- [x] Migration `060-unattended-closure-command-policy` declares Lean
  `docs/WORKTREE_LIFECYCLE.md`, and nothing else, as adoptable. 1.2.6 is
  unpublished, so extend 060 (confirm no tag from `v1.2.6` on exists on `origin`
  first). Its `delta`, the 1.2.6 changelog section, and a new changelog fragment
  state that an existing copy is backed up and replaced.
- [x] Governed SDD upgrades are unaffected: its managed documents already have
  baselines, and a test proves its plan is unchanged.
- [x] Tests cover: identical existing copy; differing existing copy with backup
  created and reported; no local copy; a second upgrade after adoption is a
  no-op; an undeclared path with a missing baseline still conflicts; backup name
  collision; and the malformed-declaration case in the repository check.
- [x] A rehearsal is recorded in the handoff: lock a Lean project at the 1.2.5
  baseline with its original `docs/WORKTREE_LIFECYCLE.md` present, run
  `meridian upgrade --apply` from the current tree, and confirm the document
  equals the template and the backup holds the old copy.
- [x] `python3 scripts/check_repository.py` and the unit tests pass, including
  `test_oldest_published_release_upgrades_to_current_in_one_apply`.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Upgrade planner (missing-baseline branch) and apply. |
| `scripts/check_repository.py` | Migration field validation. |
| `migrations/060-unattended-closure-command-policy.json` | Declares the adoptable path. |
| `migrations/README.md` | Documents the new field. |
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | Upgrade behavior and release-note contract. |
| `CHANGELOG.md`, `changelog.d/` | 1.2.6 section and new fragment. |
| `tests/test_meridian_cli.py` | Upgrade planner and apply tests. |

## Technical Context

- The consumer cannot prove that a differing copy is an unmodified old framework
  version: packaged baselines hold no full historical template trees. A backup
  makes replacing it safe and reversible, which is why the task chooses
  backup-and-replace over a conflict.
- The behavior is opt-in per migration so a project-owned file can never be
  replaced this way by accident; the generic missing-baseline conflict remains
  the default.
- Observed by rehearsal on 2026-10-03: a Lean project with the file present
  produced `CONFLICT docs/WORKTREE_LIFECYCLE.md — managed baseline is missing`
  and applied nothing; a project without it produced `ADD`.
- Upgrade never infers or writes project values; this task adds no such behavior.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`
- The recorded rehearsal described above.

## Out of scope

Making additional files managed, changing the content of the lifecycle
documents, resolving conflicts in project-owned files, and publishing the
release.

## Dependencies

- **Depends on**: 127
- **Blocks**: none
