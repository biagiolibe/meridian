# Task 209 — Verify a clean install from a release tag

> **ID**: `209`
> **Category**: Verification
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

No record shows that someone who has never used Meridian can install it and
close a first task by following the README alone. Run the documented quick
starts from a clean environment, record every step and its result, and list
each point where a newcomer would get stuck. The findings feed tasks 211 and
212.

## Acceptance Criteria

- [x] `docs/CLEAN_INSTALL_VERIFICATION.md` records, for the newest published
  tag, the environment used: OS, Python version, Git version, host versions,
  and a fresh `HOME` or equivalent isolation with no prior Meridian install,
  user configuration, or worktree root.
- [x] It follows the README's Claude Code quick start from the pinned
  marketplace install through `/meridian-init` on a new empty Git project.
  Then it follows one Lean Delivery task from creation to `meridian worktree
  advance` and `cleanup`, against a local bare repository used as `origin`.
- [x] It follows the README's Codex quick start, from the tagged checkout,
  `MERIDIAN_ROOT`, and the skill links, through `meridian self-check`.
- [x] Each step records the exact command, its exit status, and the outcome.
  A step that cannot run non-interactively, such as a Claude Code `/plugin`
  command, is recorded as manual evidence with its exact procedure and is not
  claimed as executed.
- [x] A findings table lists every friction: missing prerequisite, unclear or
  wrong instruction, unexpected prompt, or stop. Each row names the README
  section and a proposed correction. Findings are not fixed in this task.
- [x] No machine-specific absolute path, user name, or credential appears in
  the record.
- [x] `python3 scripts/check_repository.py` and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `README.md` | The quick starts under verification. Not edited here. |
| `docs/CLEAN_INSTALL_VERIFICATION.md` | New verification record. |

## Technical Context

- Use a temporary directory for `HOME`, the worktree root, the project, and
  its bare `origin`. Do not touch the developer's real configuration.
- Documentation-only change: the test suite cannot exercise it and may be
  skipped, recorded per `docs/CONTEXT_BUDGET_POLICY.md`.

## Validation

- `python3 scripts/check_repository.py`
- `git diff --check`

## Out of scope

Changing the README, the CLI, or the templates, and verifying Windows.

## Dependencies

- **Depends on**: —
- **Blocks**: 211

## Completion

Verified release `v1.2.15` in a disposable home and consumer project with a local
bare origin. The record includes 71 executed shell steps, explicit unexecuted
Claude Code procedures, a recovered first-task lifecycle through cleanup, and
15 findings for follow-up tasks. README, CLI, and templates were not changed.

Validation: `python3 scripts/check_repository.py` and `git diff --check` passed.
See `docs/CLEAN_INSTALL_VERIFICATION.md` and `tasks/handoffs/209.md` for evidence
and the limitations of interactive host verification.
