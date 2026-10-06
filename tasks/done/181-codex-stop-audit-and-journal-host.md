# Task 181 — Run the stop audit on Codex and record the host on audit lines

> **ID**: `181`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up to task 173, 2026-10-05
> **Origin**: capability

## Objective

Task 173 adds a Claude Code `Stop` hook that runs `meridian hook stop-audit`
and records `BLOCKED <CODE>` reports that no command emitted. It is
registered for Claude Code only, and Codex configuration was out of scope.

When Codex does the work, an unbacked stop leaves no trace. Journal lines
do not name the host, so `report flow` cannot tell "no unbacked stops" from
"this host was not audited", and its false-stop count is biased toward
Claude Code sessions.

Task 173's investigation found that Codex documents a `Stop` event that also
carries `last_assistant_message`. Register the same audit for Codex and
record which host produced each audit line.

## Acceptance Criteria

- [x] `templates/workflows/lean-delivery/.codex/hooks.json` and
  `templates/workflows/governed-sdd/.codex/hooks.json` register a `Stop` hook
  that runs `meridian hook stop-audit --host codex` with a timeout of 5
  seconds or less. The existing `PreToolUse` read-guard entry is unchanged.
  This repository's `.codex/hooks.json` gets the same entry as the template,
  copied by hand, and its manifest digest is refreshed with `python3
  scripts/check_repository.py --write-managed-digests`, following task 176.
  Amended by the developer before closure: `meridian upgrade` is blocked on
  this repository by its 1.1.49 self-hosting baseline.
- [x] `meridian hook stop-audit` accepts `--host claude|codex`, defaulting to
  `claude` so the Claude Code entry from task 173 keeps working unchanged.
- [x] The Codex `Stop` hook input fields are verified against the installed
  Codex CLI version. The handoff records that version, the top-level keys
  observed, and which field supplied the final message. If the final message
  is not available from the input, the transcript fallback is verified the
  same way.
- [x] Every `unbacked_block` and `declared_block` journal line carries
  `host: "claude"` or `host: "codex"`. Lines written before this task, which
  have no `host`, are read as `claude`. Journal lines written by lifecycle
  commands are unchanged.
- [x] `meridian report flow` reports unbacked and declared blocks per host.
- [x] The hook keeps every task 173 guarantee on Codex: no message text is
  stored, it always exits 0, never blocks the stop, and does nothing outside a
  Meridian project or when no journal exists.
- [x] The managed `.codex/hooks.json` change ships through a migration to the
  next template-changing release, shared with 169 and 176 if they ship
  together. `upgrade --check` on copies of the Palimpsest and Fusa manifests
  is recorded in the handoff.
- [x] Tests cover a Codex hook input with a backed code, an unbacked code, a
  malformed input, a `host` value on each written line, a pre-181 line
  without `host`, and the per-host `report flow` totals.
- [x] One changelog fragment is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and
  `python3 scripts/run_tests.py --parallel` pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/*/.codex/hooks.json` | Managed Codex hook templates; changed. |
| `.codex/hooks.json` | This repository's installed copy; updated by `meridian upgrade`. |
| `scripts/stop_audit.py` | Stop audit from task 173; gains the host. |
| `scripts/meridian.py` | `hook stop-audit` arguments and `report flow` totals. |
| `migrations/` | New migration for the managed Codex hook change. |
| `migrations/042-codex-read-guard-hook.json` | Precedent for a managed `.codex/hooks.json` change; read only. |
| `docs/WORKTREE_LIFECYCLE.md` | Lifecycle journal and stop audit documentation. |
| `tests/test_stop_audit.py` | Stop audit tests from task 173. |

## Technical Context

- **Current behavior**: after task 173, only Claude Code runs the stop
  audit. Audit lines hold `stop_code` and `task` only.
- **Desired behavior**: both hosts run the audit, and every audit line names
  its host, so a host that was not audited is visible in `report flow`.
- The parser from task 173 reads `last_assistant_message` first and falls
  back to the last assistant entry at `transcript_path`. Codex is documented
  to carry `last_assistant_message`; its transcript format is not verified.
- The read guard already runs on both hosts through `--host codex`; follow
  that convention.

<!-- TODO: add relevant code snippets and file paths -->

## Suggested Implementation

<!-- TODO: add relevant code snippets and file paths -->

## Constraints and Considerations

- Release B per the plan in `tasks/QUEUE.md` (Phase 55), because the managed
  `.codex/hooks.json` needs a migration.
- Do not change Codex user or global configuration, and do not touch
  `templates/workflows/*/PROJECT_WORKFLOW.md`, `AGENTS.md`, or `CLAUDE.md`;
  those belong to 169 and 176.
- Out of scope: blocking or rewriting a reply, storing message content, and
  adding `host` to lifecycle command lines.

## Dependencies

- **Depends on**: 173
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/181-codex-stop-audit-and-journal-host.md)"$'\n\nExecute this task in the current project.'
```
