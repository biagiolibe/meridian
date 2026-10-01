# Task 086 — Launch console agents in a horizontal iTerm2 split pane

> **ID**: `086`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Developer request to replace the iTerm2 tab launch with a split pane

## Objective

Change the console's agent launch (Task 077) so that `claude` or `codex` starts
in a horizontal split pane of the console's own iTerm2 session instead of a new
tab. The developer keeps the console visible next to the running agent. Every
other launch rule from Task 077 (eligible phases, confirmation, primary
checkout, quoting, refusals, `[copy]` fallback) is unchanged.

## Acceptance Criteria

- [x] The AppleScript payload splits the console's session with
  `split horizontally with default profile` and writes the quoted command into
  the new pane. It no longer calls `create tab` or `create window`.
- [x] The console's session is identified from `ITERM_SESSION_ID`. The value is
  validated against the documented `w<N>t<N>p<N>:<UUID>` shape before use, and
  only the UUID part reaches AppleScript, quoted for it.
- [x] When `ITERM_SESSION_ID` is missing, malformed, or matches no iTerm2
  session, the launch fails with a specific message and the existing `[copy]`
  directive remains the fallback. There is no silent fallback to a tab or a
  window.
- [x] The command is still built as an argument vector and quoted with
  `shlex.quote`; the task ID is still revalidated immediately before launch; no
  flag that weakens permissions or sandboxing is added.
- [x] iTerm2 is still driven through AppleScript (`osascript`) only, with no new
  dependency and no iTerm2 Python API.
- [x] The success message, the launch hint in the help text, the docstrings, and
  the README paragraph say "split pane" instead of "tab". The first-run macOS
  automation prompt remains documented.
- [x] Repeated launches split the console's own session each time; the
  behavior and its effect on pane sizes are stated in the README.
- [x] The console still never writes project files itself.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | `LaunchRequest`, `_apple_script`, the launch function and its messages, the help text. |
| `tests/test_project_console.py` | Launch tests that replace `osascript` with a test double. |
| `README.md` | Console launch paragraph (currently "start a new tab"). |
| `CHANGELOG.md` | User-visible behavior change. |

## Technical Context

- **Current behavior**: `_apple_script` creates a window when none exists,
  otherwise runs `tell current window to create tab with default profile`, then
  writes the command in the current session. Success reports
  `Started <agent> in a new iTerm2 tab`.
- **Desired behavior**: the script resolves the session whose unique id is the
  UUID from `ITERM_SESSION_ID`, splits it horizontally, and writes the command
  in the new pane. A horizontal split places the new pane below the console.
- The `unique id` lookup and the split direction are iTerm2 behavior that
  cannot be read back programmatically; both are covered by the manual smoke
  check below and recorded as unverified until it is done.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- Unit tests cover the split payload, the session-id validation, each refusal
  above (missing, malformed, unmatched), hostile characters in the command, and
  the `[copy]` fallback, with `osascript` replaced by a test double.
- Manual smoke check in iTerm2 with one agent, recorded as the only manual
  evidence: the new pane appears below the console and the console stays
  usable.

## Manual verification

- 2026-10-01: Earlier attempts opened a tab. Two causes were found: the
  AppleScript contained an invalid `write text ... to newSession` statement
  that does not compile (now `tell newSession to write text`, covered by an
  `osacompile` test), and the developer's `MERIDIAN_ROOT` made
  `meridian console` load the console from another checkout.
- 2026-10-01: Smoke check in iTerm2 using the task-worktree console with
  `MERIDIAN_ROOT` pointed at the worktree: launching an agent opened a split
  pane below the console, and a second launch opened another pane below.
  The console stayed usable.

## Out of scope

Vertical splits or a direction setting, tiling or reusing earlier agent panes,
other terminals or multiplexers, embedded terminals, preparing or removing
worktrees, and any change to the lifecycle documents.

## Dependencies

- **Depends on**: 077
- **Blocks**: none
