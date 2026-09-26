# Task 052 — Make the upgrade planner aware of generated entry routers

> **ID**: `052`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: 2026-09-26 consumer entry-router drift investigation

## 🎯 Objective

A consumer project that generates `AGENTS.md` and `CLAUDE.md` from
`docs/workflows/ENTRY_ROUTER.md` (for example, Palimpsest) fails
`meridian audit` after an upgrade whose migration manages those two files.
Migration `044-rejected-attempt-restart` (1.1.40 -> 1.1.41) lists `AGENTS.md`
and `CLAUDE.md` in `managedPaths`; `upgrade --apply` merged a
`capability=command-triggers v3` marker block into both generated files. They
then no longer matched the generator output (`FAIL generated entry router
drift`), duplicated the router's own "Command triggers" section, and exceeded
the 2048-byte entry-router budget. The new `Restart rejected <TASK-ID>`
trigger never reached the canonical router source. Make `upgrade` treat
generated entry routers as derived files so this cannot recur on the next
`command-triggers` change.

## 📋 Acceptance Criteria

- [ ] When `docs/workflows/ENTRY_ROUTER.md` exists in the project,
      `upgrade --check` and `--apply` never three-way-merge template content
      into `AGENTS.md` or `CLAUDE.md`. The plan reports them with a distinct
      action (for example `ROUTER`) instead of `KEEP`/`UPDATE`/`MERGE`.
- [ ] If a migration in the plan changes a capability that the entry router
      must expose (at minimum `command-triggers`), `upgrade --check` reports
      each trigger missing from `ENTRY_ROUTER.md` with its target document,
      and `upgrade --apply` returns `BLOCKED` before touching any file until
      the router source covers it (or the operator passes the existing
      owner-reconciled path, if that path fits).
- [ ] The report tells the operator to add a trigger whose target the router
      already names to that route's existing line, not as a new line, because
      `audit_entry_router()` requires each route target to appear exactly
      once in `ENTRY_ROUTER.md`.
- [ ] After a successful `--apply`, the CLI regenerates `AGENTS.md` and
      `CLAUDE.md` from the router (the same output as
      `generate-entry-routers --write`) and runs the entry-router audit;
      a failure is reported as an apply failure, not left for a later audit.
- [ ] The manifest hashes recorded for `AGENTS.md` and `CLAUDE.md` after apply
      are those of the regenerated files, so the next `upgrade --check` is a
      true no-op.
- [ ] Fixture tests in `tests/test_meridian_cli.py` reproduce the 1.1.40 ->
      1.1.41 case: a router project on 1.1.40 upgrades without drift; a
      router source missing `Restart rejected` blocks apply with the
      same-line guidance; a project without `ENTRY_ROUTER.md` keeps today's
      merge behavior unchanged.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `ENTRY_ROUTER_*` constants, `entry_router_outputs`, `audit_entry_router`, `plan_from_baseline`, `plan_upgrade`, `print_plan`, `apply_plan`, `apply_upgrade`. |
| `migrations/044-rejected-attempt-restart.json` | Reference case; do not edit (migrations are append-only). |
| `tests/test_meridian_cli.py` | Router-project upgrade fixtures. |
| `commands/meridian-upgrade.md`, `docs/CONSUMER_ROUTER_ADOPTION_PLAYBOOK.md` | Operator guidance for router projects. |

## 🧩 Technical Context

- **Current behavior**: the planner treats `AGENTS.md` and `CLAUDE.md` as
  ordinary managed template files in every project. `audit` separately
  requires them to equal the router generator's output. The two mechanisms
  contradict each other in router projects, and only `audit` notices.
- **Desired behavior**: in a router project the router source is the only
  editable input; the upgrade either proves the router already covers the
  migration's triggers or stops, and it always leaves the generated files
  byte-identical to generator output.
- **Consumer evidence**: Palimpsest was repaired manually on 2026-09-26 by
  adding `Restart rejected <TASK-ID>` to the router's existing
  `LIFECYCLE.md` line and regenerating both files; `audit`,
  `generate-entry-routers --check`, and `upgrade --check` then passed.

## 🔨 Suggested Implementation

1. Add `project_uses_entry_router(project_root)`; branch on it in the planner
   for the two generated paths.
2. Derive the required triggers from the target template's
   `command-triggers` block, and compare them with the router text to produce
   the missing-trigger report.
3. In apply, after writing all other files, regenerate the routers, record
   their hashes, then run `audit_entry_router`.
4. Update the operator documentation.

## ⚠️ Constraints and Considerations

- This task changes the same planner and apply functions that task 015
  rewrites. It depends on 015 so the two worktrees do not collide; rebase
  the design on 015's manifest shape.
- Do not change `ENTRY_ROUTER_ROUTES`, the 2048-byte budget, or the
  once-per-target audit rule.
- Do not write machine-specific absolute paths in fixtures, docs, or task
  records (see task 053).

## 🔗 Dependencies

- **Depends on**: 015
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/052-router-aware-upgrade-planner.md)"$'\n\nExecute this task in the current project.'
```
