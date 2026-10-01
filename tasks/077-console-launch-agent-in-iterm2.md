# Task 077 — Launch Claude Code or Codex from the console in an iTerm2 tab

> **ID**: `077`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: unassigned
> **Session**: Developer request for agent launch from the project console

## Objective

Let the developer start `claude` or `codex` in a new iTerm2 tab, in the primary
checkout, with the task directive for the selected task already supplied as the
initial prompt. This is the console's first action with side effects, so it is
explicit, confirmed, and limited to the directives the active workflow permits
for the task's effective state.

## Acceptance Criteria

- [ ] Launch is offered only from the effective phase produced by Task 076:
  - `todo` with dependencies satisfied: `Proceed with <ID>` in both modes.
  - Lean `ready_for_review`: `Review <ID>`.
  - Governed `ready_for_review` with `Review: REQUIRED`: `Review <ID>`.
  - Governed `in_progress` whose latest review attempt is
    `CHANGES_REQUESTED`: `Address review <ID>`.
  - Every other phase, and every `MISMATCH` task, offers no launch.
- [ ] `Accept` and `Run lifecycle` are never offered; the task records why
  (owner acceptance and whole-loop orchestration are not one-key actions).
- [ ] The developer chooses the agent (`claude` or `codex`) and confirms the
  exact directive and working directory before anything starts. A single
  keypress never launches.
- [ ] The agent starts in the primary checkout. The console does not run
  `meridian worktree prepare`; the directive does.
- [ ] A task whose worktree has uncommitted changes, or whose state is
  `MISMATCH`, is never launched. `Review` is also refused while the branch
  shows an active writer.
- [ ] The command is built as an argument vector and quoted with `shlex.quote`
  before reaching iTerm2. The task ID is revalidated against the profile's ID
  rules immediately before launch, and any ID that is not matched is refused.
- [ ] The prompt is passed as the positional prompt argument documented by
  `claude --help` (`claude [options] [prompt]`) and `codex --help`
  (`codex [OPTIONS] [PROMPT]`). No flag that weakens permissions or sandboxing
  is added.
- [ ] iTerm2 is driven through AppleScript (`osascript`) only. No iTerm2 Python
  API and no new dependency. The first-run macOS automation prompt is
  documented.
- [ ] Off macOS, without iTerm2, when the agent executable is missing, or when
  `osascript` fails or times out, the launch fails with a specific message and
  the existing `[copy]` directive remains the fallback.
- [ ] Documentation states that launching starts an agent that may modify the
  project, and that the launch counts as the developer's assignment of that
  task.
- [ ] The console still never writes project files itself.

## Relevant Files and Context

- `scripts/project_console.py`: `Task.launch_command`, `_copy_to_clipboard`,
  the detail view, the key and mouse handling in `run_terminal`.
- Task 076 output: effective phase, `MISMATCH`, active-writer indicator.
- Directive triggers: `CLAUDE.md` and
  `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`.
- In Governed SDD the reviewer-integrator integrates from the primary
  checkout, so `Review` there is correctly launched in it; the implementer
  never edits there.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Unit tests cover the permitted-directive matrix for both modes, every
  refusal above, quoting of hostile IDs, and each failure mode, with `osascript`
  and the agent executable replaced by test doubles.
- Manual smoke check in iTerm2 with one agent, recorded as the only manual
  evidence, since a rendered terminal tab cannot be read back programmatically.

## Out of scope

Preparing or removing worktrees, `Accept` and `Run lifecycle`, other terminals
or multiplexers, embedded terminals, and any change to the lifecycle documents.

## Dependencies

- **Depends on**: 076, 078
- **Blocks**: none
