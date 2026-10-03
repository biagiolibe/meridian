# Task 134 — Add `meridian context size` to measure the startup read set

> **ID**: `134`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Context-cost analysis of Palimpsest and Meridian, 2026-10-03

## Objective

Meridian has context-budget rules but nothing measures what its workflow files
cost an agent at the start of a role. A static estimate on 2026-10-03 put an
implementer in a Governed SDD project at about 35,000 to 41,000 tokens before any
code (133 KB across 13 files in Palimpsest), against about 5,000 to 6,000 for a
Lean Delivery project, and no command could have shown growth or reported it.
Add a read-only command that reports the size of the files a role is instructed
to read, so growth is visible and can be gated.

## Acceptance Criteria

- [ ] `meridian context size --role <role> [--task <ID>] [--project <path>]
  --format json|text` reports, for the project's workflow mode, each file in the
  role's read set with its bytes, lines, and estimated tokens, plus a total.
  Roles cover at least the entry-router triggers of the workflow: status or
  design, implementation, review, remediation, and lifecycle (Governed SDD), and
  implementation and review (Lean Delivery).
- [ ] The read set is derived from the project's own router and workflow
  documents (the entry router or `AGENTS.md`/`CLAUDE.md`, the routed workflow
  document, and the documents it cites by path) and from the always-read files
  (`PROJECT_WORKFLOW.md`, `LANGUAGE_POLICY.md`). It uses the project's resolved
  locations, not hard-coded paths. A cited path that does not exist is reported
  as missing, not skipped.
- [ ] With `--task`, the task record and the Authority excerpts resolved by
  `meridian context authority` are included and labelled separately from the
  fixed files.
- [ ] Token estimates are reported as an explicit range (bytes divided by 4 and by
  3.3) and labelled as estimates; the command never claims tokenizer accuracy.
- [ ] The output marks files above a configurable size and the two known
  unbounded documents when present: the queue and the ADR log, with their size
  and the note that the routed workflow reads them only through the queue
  briefing and `meridian context authority`.
- [ ] The command writes nothing and runs no project command. It works for
  `opaque` and `milestone` task identity.
- [ ] A threshold can be set in a project file or by option; when exceeded the
  command exits non-zero with the file list responsible. The default is
  advisory (exit zero) so existing projects are not broken.
- [ ] `check_repository.py` checks the shipped Lean Delivery and Governed SDD
  template read sets against a stated ceiling per role, so a template change
  that grows the startup cost fails with the numbers. The ceilings are recorded
  in a documented, versioned place.
- [ ] Tests cover: both workflows, each role, a missing cited file, a milestone
  project, `--task`, the range labelling, the threshold exit code, and that
  nothing is written.
- [ ] A rehearsal on a scratch copy of a real Governed project reproduces the
  2026-10-03 figures within rounding and is recorded in the handoff.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `context` subcommands and location resolution. |
| `docs/CONTEXT_BUDGET_POLICY.md` and its templates | Where the ceilings are documented. |
| `scripts/check_repository.py` | Template ceiling check. |
| `tests/test_meridian_cli.py` | Command tests. |

## Technical Context

- Measured on 2026-10-03 from file sizes of the documents a role is told to read
  (Palimpsest, Governed SDD): implementer 133 KB (13 files), reviewer 134 KB,
  remediation 107 KB, status 62 KB. Largest items: `PROJECT_WORKFLOW.md` 38 KB,
  the active milestone specification 19 KB, `CODE_ORGANIZATION.md` 15 KB,
  `IMPLEMENTATION.md` 13 KB, `CONTEXT_BUDGET_POLICY.md` 13 KB,
  `EXECUTION_EVIDENCE_PROFILE.md` 12 KB.
- The queue was 87 KB (about 22,000 to 27,000 tokens) and the ADR log 921 KB
  (about 236,000 to 286,000 tokens); neither is on the default read path.
- The estimate does not measure what an agent actually loaded; task 135 covers
  measured usage.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Reducing any file, measuring real sessions (task 135), per-phase loading
(task 136), and a tokenizer dependency.

## Dependencies

- **Depends on**: —
- **Blocks**: 136
