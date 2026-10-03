# Task 118 — Show the running framework version and root in the project console

> **ID**: `118`
> **Category**: Feature
> **Priority**: 🟢 P3
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Follow-up found while investigating a console that showed a working task as ready

## Objective

Make the project console identify both the watched project and the Meridian copy
that is running, then make task launch a clear single-choice interaction. Two
framework copies can coexist on one machine, the repository checkout and a
released copy installed by the Claude plugin cache, and they behave
differently: a released console that predates the derived `[/]` state shows an
in-progress task as `READY`, which looks like a lifecycle fault but is a version
difference. The console must make that visible without a diagnosis, and its
launcher must make the selected agent and configured defaults visible before
the user starts it.

## Acceptance Criteria

- [ ] The first line of `python3 scripts/project_console.py --once` and the header of the interactive console include the framework version read from the `VERSION` file next to the running scripts, for example `v1.2.3`.
- [ ] The same output includes the framework root the scripts were loaded from, shortened to a home-relative path when it lies under the home directory.
- [ ] When the `VERSION` file is missing or unreadable, the console shows `version unknown` and keeps working; it never fails to start because of the version lookup.
- [ ] The lookup is read-only, makes no network call, and runs once at startup, not on every refresh.
- [ ] Tests cover a present version, a missing `VERSION` file, and the home-relative root, for both the `--once` output and the header text.
- [ ] While the interactive console is running, its terminal title includes
  `Meridian console` and the watched project name. The title update is safe on
  terminals that do not support it and contains no absolute path.
- [ ] Pressing `l` opens a bordered, visually isolated launch panel that shows
  the selected task, directive, project, both agent choices, and the cancel
  action without leaving underlying console text visually mixed into the panel.
- [ ] The launch flow has one decision after `l`: pressing `1` for Claude Code
  or `2` for Codex revalidates and immediately launches that agent; `Esc`
  cancels. There is no second Enter confirmation.
- [ ] Each agent choice shows the configured default model and reasoning or
  effort level when they can be resolved safely from supported local
  configuration, labelled as a configured default rather than a guaranteed
  effective value. Missing, malformed, ambiguous, or overridden configuration
  displays `unknown` and never prevents launch.
- [ ] Model detection is read-only, reads only the named model and
  reasoning/effort settings, exposes no unrelated configuration or credential,
  makes no network call, and does not add model flags or otherwise override the
  user's agent configuration.
- [ ] Launcher tests cover the bordered panel content, direct `1`/`2` launch,
  cancellation, revalidation failure, known defaults, and graceful `unknown`
  fallbacks.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | `--once` snapshot head and `_draw_header`; add the version and root text. |
| `tests/test_project_console.py` | Console tests to extend. |
| `README.md` | The "Project console" section; document console identity and the launch interaction. |

## Technical Context

- **Current behavior**: the snapshot starts with `MERIDIAN | <project> | <branch> | <state>` and the interactive header with `Project command center  <project>  <branch>`. Neither names the framework copy that rendered them.
- **Observed**: on 2026-10-02 the repository was at `1.2.3` while `~/.claude/plugins/cache/meridian/meridian/1.2.0` held the released copy. Run from the repository, the console showed task 117 as `IN PROGRESS`; run through the plugin copy it showed `READY`, because the derivation added by task 105 is not in 1.2.0.
- **Desired behavior**: both outputs name the version and root, so a mismatch between the console and the repository is visible at a glance.
- **Current launch flow**: `l` opens an agent choice, then a second text-only
  confirmation requires Enter. The panel writes over the existing screen
  without a border or cleared background.
- **Current launch command**: the console starts `claude <directive>` or
  `codex <directive>` without model flags. The displayed settings are therefore
  informative configured defaults only; agent configuration precedence and
  runtime overrides remain authoritative.

## Constraints and Considerations

- Keep the header within its current width budget; truncate the root before the project name or branch.
- All repository text is written in English.
- Add one changelog fragment per `CONTRIBUTING.md`, because the change is user-visible.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Detecting or warning about a newer released version, changing how the plugin
copy is installed or updated, changing the derived task state, overriding the
agent model or reasoning level, provider usage limits, task timing, lifecycle
progress, and token accounting. Task 119 owns task timing and progress.

## Dependencies

- **Depends on**: 105
- **Blocks**: none
