# Task 165 — Install the deny list as host permission rules

> **ID**: `165`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: Claude
> **Session**: ADR stops and denials, 2026-10-05

## Objective

The actions that `Proceed with` never authorizes are force pushes, pushes that
delete or mirror references, tags, history rewrites, and deleting unmerged work.
Today they are denied only in prose. `meridian setup` already writes a
project-local Claude Code allowlist. Decision 5 of
`docs/ADR_STOPS_AND_DENIALS.md` asks it to install matching deny rules where
the host supports them.

## Acceptance Criteria

- [x] `plan_claude_project_allowlist` and `apply_claude_project_allowlist`
  also plan and add `permissions.deny` entries in
  `.claude/settings.local.json` for at least these prefixes:
  - `git push --force`, `git push -f`, `git push --force-with-lease`,
    `git push --mirror`, `git push --delete`;
  - `git tag`;
  - `git rebase`, `git reset --hard`, `git cherry-pick`;
  - `git branch -D`;
  - `git worktree remove --force`.
- [x] Existing user entries are kept. The plan reports which deny entries it
  would add, and `--apply` stays required to write.
- [x] No deny entry blocks a command that the lifecycle needs, including plain
  `git push origin main`, `git push origin <task-branch>`, and `git branch -d`.
  A test proves it against the allowlist.
- [x] The README and the setup output state that prefix rules are defense in
  depth, that a reworded command can evade them, and that the managed denial text
  remains in force.
- [x] Codex support is investigated in the installed Codex CLI documentation
  or rules format. The handoff records whether an equivalent forbidden rule
  exists. If it does, a follow-up task is proposed; Codex config is not changed
  in this task.
- [x] Tests cover adding deny entries, keeping user entries, idempotent
  re-apply, and the lifecycle commands still being allowed.
- [x] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `plan_claude_project_allowlist`, `apply_claude_project_allowlist`, setup output. |
| `README.md` | Setup documentation. |
| `tests/test_meridian_cli.py` | Setup tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decision 5.
- Setup tests must stay isolated from the developer's real home directory, as
  task 147 required.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Writing `~/.claude/settings.json`, changing Codex configuration, and changing
the managed denial text.

## Dependencies

- **Depends on**: —
- **Blocks**: none
