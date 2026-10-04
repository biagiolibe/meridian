# Task 160 — Give the Claude Code allowlist parity with the Codex execution-command rules

> **ID**: `160`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Palimpsest permission prompts during task execution, 2026-10-04

## Objective

Agents in Palimpsest are asked to authorize many commands during task
execution. Meridian's consented Claude Code allowlist
(`CLAUDE_PROJECT_ALLOWLIST`, `scripts/meridian.py` ~2528, written to
`.claude/settings.local.json` by `meridian setup --apply`) covers `git`,
`meridian worktree …`, repository checks, and read-only shell utilities, but no
`meridian execution …` command. The Codex rules shipped in the same templates
already allow `meridian execution` `validate`, `ready-check`, `handoff-check`,
`preflight`, `evidence`, `contract`, and `investigate`
(`templates/workflows/governed-sdd/.codex/rules/meridian.rules`, line 59) and
keep `reconcile` on approval because it changes state. The two hosts therefore
differ for the commands that every governed task uses.

`meridian execution validate` runs the task-declared literal command in a shell
(`run_validation`, ~9300), so one allow rule for it covers every declared
validation of every project and language; the host never sees the inner command.
Add the same execution commands to the Claude allowlist.

## Acceptance Criteria

- [ ] `CLAUDE_PROJECT_ALLOWLIST` gains one `Bash(meridian execution <sub>:*)`
  entry, and the matching `Bash(python3 scripts/meridian.py execution <sub>:*)`
  entry, for each of `validate`, `ready-check`, `handoff-check`, `preflight`,
  `evidence`, `contract`, and `investigate`, mirroring the Codex rule. `execution
  reconcile` is not allowed.
- [ ] A test fails if the sets of execution subcommands in the Codex rule and in
  the Claude allowlist differ, so the two cannot drift again.
- [ ] `test_claude_allowlist_covers_only_the_declared_command_surface` asserts the
  new entries are present and that `reconcile` and a bare `Bash(meridian:*)` are
  absent; the existing forbidden-fragment checks still pass.
- [ ] `meridian setup --check` still never writes the allowlist; `setup --apply`
  adds only the missing entries to an existing file, preserving unrelated
  entries, and a second run is a no-op. Existing project tests for those
  properties keep passing.
- [ ] `codex doctor` and the README paragraph about the allowlist do not claim a
  command surface that no longer matches; update the text only where it lists
  commands.
- [ ] README states, in one sentence, that the allowlist runs whatever a task's
  `## Validation` declares, so declared commands are reviewed in the task file,
  not at the permission prompt.
- [ ] One changelog fragment states the change under `Changed` and, under
  `Upgrade notes`, that existing projects receive the new entries with
  `meridian setup --apply`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `CLAUDE_PROJECT_ALLOWLIST` (~2528), `plan_claude_project_allowlist` (~2575). |
| `templates/workflows/governed-sdd/.codex/rules/meridian.rules` | Source of truth for the allowed subcommands (line 59); read, not changed. |
| `templates/workflows/lean-delivery/.codex/rules/meridian.rules` | Check whether it carries the same line; read, not changed. |
| `tests/test_meridian_cli.py` | Allowlist tests (~5491, ~5591) and the new parity test. |
| `README.md` | Allowlist paragraph (~393). |

## Technical Context

- Trade-off, recorded here: allowing `execution validate` lets any command that
  appears in a task's `## Validation` run without a prompt, and task files are
  written by agents. The permission therefore moves review of those commands from
  the prompt to the task file and its review. Codex already accepts this for the
  same subcommands.
- Validation commands are literal; a command that contains a random temporary
  path cannot be declared reusably. That is a project concern and not changed
  here.
- Observed in Palimpsest on 2026-10-04: `.claude/settings.local.json` holds 43
  entries, none for `meridian execution`, `cargo`, `mktemp`, or `mkdir`.
- Allowlist content is user-owned once written; this task changes only what
  `setup --apply` proposes.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Allowing `execution reconcile`, adding project-specific commands such as `cargo`,
changing how `execution validate` runs commands, and writing any settings file
without consent.

## Dependencies

- **Depends on**: —
- **Blocks**: none
