# Task 173 — Detect `BLOCKED` reports that no command emitted

> **ID**: `173`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: Claude Code
> **Session**: Rigidity measurement follow-up to ADR stops and denials, 2026-10-05

## Objective

Under `docs/ADR_STOPS_AND_DENIALS.md`, an agent's `BLOCKED <CODE>` is valid
only when it is backed. An agent that stops on its own reading of the text, as
in task 161, leaves no trace in the journal. Detect those stops in Claude Code,
so that `report flow` can count false stops.

## Acceptance Criteria

- [x] A Claude Code `Stop` hook entry in `hooks/hooks.json` runs `meridian hook
  stop-audit` with a timeout of 5 seconds or less.
- [x] The hook finds `BLOCKED <CODE>` lines in the final assistant message of
  the turn. It reads only that message, from the hook input or the transcript
  path the host provides.
- [x] For each code found, it looks for a matching `blocked` journal line for
  the same code within the session's time window, and for the active task when
  one can be resolved. A code with no match is appended to the journal as
  `result: unbacked_block` with the code only.
- [x] A code that is registered as `command-exit` or `judgment` is recorded as
  `declared_block` instead, because no Meridian command is expected to emit it.
- [x] The hook stores no message text. It always exits 0, never blocks the
  stop, and does nothing outside a Meridian project or when no journal exists.
- [x] The hook input fields are verified against the installed Claude Code
  version. The handoff records which field supplied the final message.
- [x] Codex hook support is investigated. The handoff records whether an
  equivalent exists, and Codex configuration is not changed.
- [x] Tests cover a backed code, an unbacked `tool` code, a `judgment` code, no
  code, a non-Meridian directory, and a malformed hook input.
- [x] One changelog fragment is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `hooks/hooks.json` | Stop hook registration. |
| `scripts/meridian.py` | `hook stop-audit` entry point. |
| `hooks/` | Shell wrapper, if the existing hooks use one. |
| `tests/` | Hook tests. |

## Technical Context

- The existing hooks are `UserPromptSubmit` (queue briefing) and `PreToolUse`
  on `Read` (read guard). Follow their wrapper and timeout conventions.
- Not verified: the exact Stop hook input schema of the installed Claude Code
  version. Read the host documentation before you write the parser.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Blocking or rewriting an agent's reply, Codex configuration, and storing
message content.

## Dependencies

- **Depends on**: 171
- **Blocks**: none
