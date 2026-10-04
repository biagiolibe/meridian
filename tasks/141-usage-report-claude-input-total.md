# Task 141 — Count cached input in the Claude Code usage report

> **ID**: `141`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: First real run of `meridian usage report`, 2026-10-04

## Objective

`meridian usage report` (task 135) reads Codex `input_tokens`, which already
includes cached input, and Claude Code `usage.input_tokens`, which does not: the
Claude Code figure excludes the tokens read from cache (`cache_read_input_tokens`)
and written to cache (`cache_creation_input_tokens`). On 2026-10-03 the report
showed Claude sessions with `startup=2`, `mean=2.0`, and a `cache_ratio` above
100000, while the same sessions send tens of thousands of tokens per call. The
startup cost, per-call growth, peak, and `--breakdown` are therefore wrong for
Claude Code, and the two hosts cannot be compared. Make the Claude Code adapter
report the total input of each call so both hosts mean the same thing.

## Acceptance Criteria

- [ ] For Claude Code, the per-call input is `input_tokens +
  cache_read_input_tokens + cache_creation_input_tokens`; a missing field counts as
  zero, and a call with none of the three fields is reported as unavailable, not zero.
- [ ] `cached` for Claude Code is `cache_read_input_tokens` only, and `cache_ratio`
  is `cached / input` and never exceeds 1. Codex output is unchanged.
- [ ] Startup (first call), mean, peak, and the `--breakdown` call use the total
  input, for both text and JSON formats. The JSON field meanings are documented, and
  the report states in one line that input includes cached input for both hosts.
- [ ] The privacy contract is unchanged: counters, timestamps, and session metadata
  only; no message text, tool arguments, file contents, or paths.
- [ ] Tests cover: a Claude fixture with the three fields (total, cached, ratio below
  1); a call with only `input_tokens`; a call with none of the fields; a Codex fixture
  unchanged; and a mixed project report.
- [ ] A recorded run on the real Claude sessions of this project shows a startup near
  the observed 38,000 tokens and a ratio below 1; the handoff records the numbers
  without any session content.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | The usage adapters (Codex around `cached_input_tokens`, Claude around `cache_read_input_tokens`) and the report aggregation. |
| `tests/` | Existing usage report tests and fixtures. |
| `docs/` | The usage report description, if it states field meanings. |

## Technical Context

- Observed on 2026-10-03: twelve Claude sessions of this project reported
  `startup=2` and means of about 2 with `cached` in the tens of millions, against
  Codex sessions that reported `startup=18235` and means of 33,000 to 83,000.
- Earlier manual measurement of the same Claude sessions gave about 38,000 tokens for
  the first call and 65,000 to 115,000 average per call, which the fix should
  reproduce.
- The Claude usage schema may change; keep the adapter's "observed schema" note and
  its date accurate.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`
- The recorded run on real Claude sessions.

## Out of scope

Cost or price estimates, new hosts, changing the Codex adapter, and the `--breakdown`
heuristics beyond using the corrected totals.

## Dependencies

- **Depends on**: —
- **Blocks**: none
