# Task 135 — Report measured token usage of agent sessions

> **ID**: `135`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Context-cost analysis of Palimpsest and Meridian, 2026-10-03

## Objective

The static read-set size (task 134) says what a role is told to read, not what a
session costs. Local logs of both hosts record per-call token counts, and on
2026-10-03 they showed that the start is not the dominant cost: first-call input
was about 18,000 tokens in Codex and 38,000 in Claude Code on Meridian, but
sessions of 40 to 70 calls re-sent an accumulated context averaging 65,000 to
115,000 tokens, with 94 to 98 percent served from cache. Add a read-only report
over those logs so a developer can see where the cost of a task comes from.

## Acceptance Criteria

- [ ] `meridian usage report [--host codex|claude] [--project <path>] [--since
  <date>] --format json|text` reads the host's local session logs and prints one
  row per session: start time, project directory name, model when recorded,
  number of model calls, first-call input tokens, mean and peak per-call input
  tokens, cumulative input, cached input, output, and the cache ratio.
- [ ] It reads token counters and timestamps only. It never prints, stores, or
  transmits message text, tool arguments, file contents, or paths other than the
  project directory name. The report states this boundary in its output.
- [ ] It is local and read-only: no network, no writes, no dependency on a host
  being installed. A missing or unrecognised log format yields a clear message
  and `unsupported`, never a traceback or a guess.
- [ ] Log locations and field names are isolated in one small adapter per host,
  with a version note, because both are private formats that can change.
- [ ] A summary line separates fixed startup cost (first call) from growth over
  the session, so the two are never conflated.
- [ ] Optional `--breakdown` reports, from counters alone, the call count and the
  step in each session where per-call input grew most, to point at large tool
  outputs without reading them.
- [ ] Output is deterministic for a given set of logs and sorted by start time.
- [ ] Tests use synthetic log fixtures for each host, including a truncated file
  and an unknown format, and assert that no text from the fixtures' messages
  appears in the output.
- [ ] A recorded rehearsal on this machine reproduces the 2026-10-03 figures in
  the handoff, with project names generalised.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | New `usage` subcommand and the host adapters. |
| `tests/` | Fixtures and tests. |
| `README.md` | Short command description and privacy boundary. |

## Technical Context

- Observed 2026-10-03, Codex (cwd Meridian, Lean Delivery): first-call input 18,235
  tokens (13,100 in an empty project, so the Meridian-specific part is about
  5,000); sessions of 29 to 69 calls totalled 1.7 to 5.1 million input tokens with
  95 to 98 percent cached; output was 14,000 to 27,000. In Palimpsest the first call
  was 29,058.
- Observed 2026-10-03, Claude Code: first-call context about 38,000 on both
  projects; typical sessions 30 to 55 calls with a per-call context of 65,000 to
  115,000 tokens.
- Codex logs are under `~/.codex/sessions/<year>/<month>/<day>/rollout-*.jsonl`
  with `token_count` events; Claude Code logs are under `~/.claude/projects/` with
  a `usage` object per assistant message. These are host internals; verify them
  at implementation time.
- Accounting differs between hosts (cached input is counted in Codex totals), so
  the report must not present a cross-host total as a like-for-like cost.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Billing or price estimates, comparing hosts as a ranking, reading message
content, and changing any workflow text.

## Dependencies

- **Depends on**: —
- **Blocks**: 136
