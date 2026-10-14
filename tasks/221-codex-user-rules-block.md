# Task 221 — Manage a Meridian block in the user's Codex rules through setup

> **ID**: `221`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Codex approval review, 2026-10-15
> **Origin**: friction

## Objective

Codex prompts for every escalated command that no execpolicy rule allows.
Meridian's `.codex/rules/meridian.rules` has three gaps:

- it is project-level and applies only in a trusted project;
- Lean Delivery projects never receive it;
- it covers neither read-only `gh` nor safe Git commands such as `git fetch`.

A review of 70 recorded escalation requests found 26 that current rules still
prompt for, 14 of them safe. Let `meridian setup` install a user-level
Meridian rules block, the same way it already manages the Codex permission
profile.

## Acceptance Criteria

- [ ] Before any change, the handoff records a probe of one question: does a
  Codex session started inside a task worktree under the worktree root load
  that worktree's `.codex/rules/`? Only the primary checkout is a trusted
  project. The probe uses an allowed command such as `git mv` and records
  whether it prompted, with the Codex version.
- [ ] `meridian setup --check` plans, and `--apply` writes, one block in
  `~/.codex/rules/default.rules` between `# MERIDIAN:BEGIN codex-user-rules
  v1` and `# MERIDIAN:END codex-user-rules`. The block holds:
  - Meridian read-only and lifecycle commands;
  - `--check` forms of the configuration commands;
  - read-only `gh` commands;
  - plain `git push origin`, with the force, delete, and mirror forms
    forbidden;
  - `git fetch`, `git write-tree`, `git restore --staged`, and `git rm`, with
    `git rm -f` prompting.
  `gh api` and every `--apply` form stay unlisted.
- [ ] Text outside the block is never changed. A block that differs from the
  current version is replaced only through `--apply`, after `--check` shows
  the diff. A damaged marker pair stops with a registered stop code.
- [ ] `setup --check` warns, without changing anything, when the file outside
  the block holds a broad rule that overrides the block's prompts. The cases
  are `["meridian"]` alone and `["git", "push"]` without a remote. The warning
  names the line.
- [ ] `meridian codex doctor` reports the block as `ready`, `missing`, or
  `stale`.
- [ ] Tests cover:
  - plan and apply on a missing file, on a file without the block, and on an
    outdated block;
  - preservation of foreign rules;
  - a damaged marker pair;
  - the broad-rule warning;
  - `codex execpolicy check` decisions for the block, when the `codex` binary
    is available. Without the binary, the test reports a named skip.
- [ ] README's Codex section documents the block, its decisions, and the
  prefix-rule limit: a flag after the refspec is not matched. One changelog
  fragment states the feature under `Added`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `plan_setup`, `apply_setup`, `print_setup_plan`, Codex configuration and doctor. |
| `README.md` | Codex setup and approvals documentation. |
| `tests/` | Setup and doctor tests. |

## Technical Context

- The `maintainer-docs` branch's `MERIDIAN_DEVELOPER_SETUP.md` (step 8,
  "Command approval rules") holds the hand-written version of the block and
  its verification commands. The block content starts from there.
- User-level configuration, not a managed project file: no migration.
- The same file holds rules for other projects, which must survive.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing `.codex/rules/meridian.rules`, trusting worktree paths automatically,
and Claude Code permissions.

## Dependencies

- **Depends on**: —
- **Blocks**: none
