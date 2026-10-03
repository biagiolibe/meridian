# Task 123 — Allow the task-archive `git mv` in the Codex and Claude Code command policies

> **ID**: `123`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up of the unattended-closure gap observed on 2026-10-03

## Objective

Closing a task archives its record as an exact rename into `tasks/done/`,
usually with `git mv`. Neither shipped command policy allows it, so every
`Proceed with` stops on an approval prompt, defeating hands-off closure (task
100, Decision 1). Add a narrowly scoped allowance for that rename to both host
policies, with Codex as the primary target and Claude Code kept equivalent.

## Acceptance Criteria

- [ ] The Codex rules ship an allow rule for the task-record archive rename and
  nothing broader: `git mv` stays prompting (or forbidden) for any other
  source or destination. Decide and document whether the pattern can restrict
  the destination to `tasks/done/`; if execpolicy prefixes cannot, state the
  limitation and the residual risk.
- [ ] The rule is present in this repository's `.codex/rules/meridian.rules` and
  in both `templates/workflows/*/.codex/rules/meridian.rules`.
- [ ] `meridian codex doctor` probes the new rule with `execpolicy check` and
  reports it as ready or as a named gap, like the existing rules.
- [ ] The Claude Code allowlist offered by `meridian setup` includes the
  equivalent entry, scoped to `tasks/`, and remains consent-based and
  additive.
- [ ] Existing consumer projects receive the rule through the established
  managed-marker migration path without overwriting local rules.
- [ ] No other command becomes allowed, and every existing `forbidden` and
  `prompt` rule is unchanged (`git reset`, `rebase`, `cherry-pick`, force push,
  branch deletion).
- [ ] Tests cover: the rule text in each shipped file, the doctor probe result,
  the allowlist entry, and that an unrelated `git mv` is not allowed.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `.codex/rules/meridian.rules` | Project Codex policy. |
| `templates/workflows/lean-delivery/.codex/rules/meridian.rules` | Shipped Lean policy. |
| `templates/workflows/governed-sdd/.codex/rules/meridian.rules` | Shipped Governed policy. |
| `scripts/meridian.py` | Claude allowlist constant and `codex doctor` execpolicy probes. |
| `docs/WORKTREE_LIFECYCLE.md` | States the archive-rename requirement. |
| `tests/test_meridian_cli.py` | Doctor and setup tests. |

## Technical Context

- `docs/WORKTREE_LIFECYCLE.md` requires an exact 100%-similarity rename from the
  active record path to `tasks/done/` with the same file name.
- Plain `git add` is already allowed, so `mv` plus `git add` would also create
  the rename, but `mv` is not allowed either and would still prompt.
- Codex prefix rules match leading arguments only, so a destination restriction
  may not be expressible; resolve this first and prefer an explicit statement
  of the residual risk over a rule that appears narrower than it is.
- `meridian` lifecycle commands must stay free of project-provided command
  execution; this task only changes host approval policy.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Allowing any other Git command, changing `integrate stage` archive validation,
and relaxing forbidden or prompting rules.

## Dependencies

- **Depends on**: —
- **Blocks**: none
