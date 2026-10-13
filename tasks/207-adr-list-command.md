# Task 207 — Add a read-only `meridian adr list`

> **ID**: `207`
> **Category**: Feature
> **Priority**: 🟢 P3
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: GitHub issue #3 triage, 2026-10-13
> **Origin**: capability

## Objective

Implement [issue #3](https://github.com/biagiolibe/meridian/issues/3).
`meridian adr` has only `show`, which needs a known ID. Agents that must
discover which ADR governs a question open the whole log. In one Governed
project, that log holds 112 ADRs in about 947 KB. Add a list command that
prints one line per ADR without loading the log into an agent's context.

## Acceptance Criteria

- [ ] `meridian adr list [--project <path>] [--status <value>] [--format
  text|json]` resolves the ADR log through `meridian locations`. It prints one
  line per ADR with its ID, title, and status. JSON output is a list of
  objects with `id`, `title`, and `status`.
- [ ] `--status` filters, case-insensitively, on the value of each entry's
  `Status` field. An entry without a status is listed with `status: null` and
  is excluded by any `--status` filter.
- [ ] The command is read-only. A missing log, or an entry it cannot parse, is
  reported with a registered stop code or a per-entry warning. It never
  silently drops an entry.
- [ ] It reuses the entry-boundary rules of `adr show`, so `list` and `show`
  agree on which entries exist.
- [ ] Tests cover a multi-entry log, the status filter, an entry without a
  status, a malformed entry, a missing log, and JSON output.
- [ ] `docs/CONTEXT_BUDGET_POLICY.md` and the Governed SDD guidance name
  `adr list` as the way to discover ADRs, if that guidance is managed text,
  through the existing marker mechanism. Otherwise only the README is
  updated, and the handoff records which applies.
- [ ] One changelog fragment states the command under `Added`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `adr` parser and `adr_show`. |
| `tests/` | Command tests. |
| `README.md` | Command documentation. |

## Technical Context

- Structured supersession (`Superseded by ADR-NNNN`) is a format change and
  out of scope, as the issue proposes.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Splitting the ADR log, supersession metadata, and editing ADRs.

## Dependencies

- **Depends on**: —
- **Blocks**: none
