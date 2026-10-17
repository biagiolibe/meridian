# Task 231 — Ship the 1.4.0 template changes through a migration

> **ID**: `231`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: 1.4.0 release dry run, 2026-10-17
> **Origin**: friction

## Objective

Tasks 227, 228, and 229 added text to managed project templates without a
migration:

- `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`: a link to the
  command location table, and the "Budget attempts after worktree retirement"
  section;
- `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md`: the same link;
- `templates/workflows/*/docs/WORKTREE_LIFECYCLE.md`: the "Command locations"
  section and table;
- `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md`: the
  re-delivery instruction after a handoff-only correction.

The skills also changed, but they are user-level files, not project files.

`python3 scripts/release.py prepare --bump minor --dry-run` derives the kind
from migrations only. It therefore prints `CLI-only release: this release
introduces no migration`. `docs/HOW_TO_UPGRADE.md` promises that a CLI-only
release produces no managed-file changes in `upgrade --check`, so adopters may
skip upgrading their projects.

On 2026-10-17, `upgrade --check` from `main` on a copy of a 1.3.0 Governed
project reported three outcomes:

- `MERGE` for `PROJECT_WORKFLOW.md`;
- `REPLACE` for `docs/WORKTREE_LIFECYCLE.md`;
- for `docs/COMPLETION_REPORT_TEMPLATE.md`, a conflicted three-way merge that
  was left untouched because its capability markers already satisfy the
  required versions.

The issue #14 instruction would therefore never reach that project.

Make 1.4.0 a template-changing release that delivers these changes, and stop
`release.py` from labelling a release CLI-only when managed templates changed.

## Acceptance Criteria

- [ ] One migration, `070-…`, from `1.3.0` to `1.4.0`, delivers every managed
  template change listed above to Lean and Governed projects. Each change lands
  in managed text that `upgrade --apply` applies deterministically. Where the
  current text sits outside capability markers, the task adds or extends a
  capability marker with a new capability version, updates the marker
  baselines, and documents it in `migrations/CAPABILITY_MARKERS.md`. The
  migration's `upgradeNotes` name the files and the likely conflicts, and its
  `verification` lists the checks below.
- [ ] A test upgrades a pristine 1.3.0 Lean project and a pristine 1.3.0
  Governed project with the real `migrations/`. After `upgrade --apply`, each
  new paragraph and table is present, and the Governed
  `COMPLETION_REPORT_TEMPLATE.md` contains the re-delivery instruction with no
  conflict.
- [ ] `release.py prepare` and the release preflight refuse to label a release
  CLI-only when any file under `templates/` differs from the previous release
  tag and no migration ships with the release. The refusal names the changed
  template files. A release that changes only non-template files remains
  CLI-only. Tests cover both cases.
- [ ] `release.py prepare --bump minor --dry-run` derives a template-changing
  release for 1.4.0 and lists the migration.
- [ ] The changelog fragment `changelog.d/231.md` has an `Upgrade notes`
  subsection. It says to run `meridian upgrade --apply`, names the changed
  files, and warns about likely conflicts in adapted text. A `Fixed`
  subsection describes the release-kind check.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/*/PROJECT_WORKFLOW.md`, `templates/workflows/*/docs/WORKTREE_LIFECYCLE.md`, `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Changed managed text. |
| `migrations/` | New migration, marker baselines, `CAPABILITY_MARKERS.md`. |
| `scripts/release.py` | Release kind derivation and preflight. |
| `docs/HOW_TO_UPGRADE.md` | CLI-only and template-changing definitions; change only if the wording must follow the new check. |
| `tests/` | Upgrade and release tests. |

## Technical Context

- `migrations/069-lean-task-close.json` is the most recent example of a
  capability-version migration with `managedPaths`, `upgradeNotes`, and
  `verification`.
- `release.py` writes `baselineChanged: bool(migrations)` into
  `releases/<version>.json`; the derived kind follows the same rule.
- `v1.3.0` is the previous release tag. The template diff from `v1.3.0` to
  `main` is 9 files with 88 added lines, 4 of them skills.

## Out of scope

Changing the content of the template text added by tasks 227–229. Cardine.

## Dependencies

- **Depends on**: 227, 228, 229 (integrated)
- **Blocks**: the 1.4.0 release

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/231-migrate-1-4-0-template-changes.md)"$'\n\nExecute this task in the current project.'
```
