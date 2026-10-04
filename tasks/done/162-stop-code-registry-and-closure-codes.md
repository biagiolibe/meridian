# Task 162 — Add the stop-code registry and emit closure stops through it

> **ID**: `162`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

`docs/ADR_STOPS_AND_DENIALS.md` (Decision 3) requires one registry of stop
codes for both workflows and one emission path in the CLI. Today the managed
text lists thirteen closure stop codes. `closure_status` reports six of them
through a structured field. Integration conflicts, evidence mismatches, and
blocked cleanups are raised as generic errors without their codes. The CLI
also emits `UNDECLARED_VALIDATION_COMMANDS`, which no document lists.

Add the registry and the helper, and make every closure stop the CLI detects
print its registered code.

## Acceptance Criteria

- [ ] `capabilities/stop-codes-v1.json` lists every closure stop code named
  in the managed `git-workflow` block (`ACCEPTANCE_UNMET` through
  `CLEANUP_BLOCKED`), plus `PUSH_PENDING` and `UNDECLARED_VALIDATION_COMMANDS`.
  Each entry has `code`, `class` (`tool`, `command-exit`, or `judgment`),
  `workflows`, `step` when applicable, `emitter`, `human_decision`, and
  `resume`. A schema in `schemas/` validates the file.
- [ ] One CLI helper formats every stop as `BLOCKED <CODE>: <detail>; resume:
  <command>`. It accepts only registered codes and raises an internal error for
  any other code.
- [ ] `integrate stage` reports `INTEGRATION_CONFLICT`, `integrate finalize`
  reports `EVIDENCE_MISMATCH`, and `cleanup` reports `CLEANUP_BLOCKED` through
  the helper, at the existing failure paths. The exit status stays `2` and the
  current detail text is kept after the code.
- [ ] `closure_status` takes its codes and resume templates from the registry.
  Its JSON output is unchanged.
- [ ] `UNDECLARED_VALIDATION_COMMANDS` is emitted through the helper.
- [ ] Tests trigger each `tool`-class closure code that the CLI emits and
  assert the exact output line. Each entry records the test name that proves it
  in a `test` field.
- [ ] No existing code name changes. The execution, handoff, validation,
  investigation, and budget messages are left for task 166.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change with no migration.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `capabilities/stop-codes-v1.json` | New registry. |
| `schemas/` | Registry schema. |
| `scripts/meridian.py` | `closure_status`, stage, finalize, cleanup failure paths, and the `UNDECLARED_VALIDATION_COMMANDS` message. |
| `tests/test_meridian_cli.py` | Output-line tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decisions 2 and 3. Do not start
  this task until the ADR is `Accepted`.
- Classes: `VALIDATION_FAILED`, `CANDIDATE_VALIDATION_FAILED`, and
  `PUSH_REJECTED` are `command-exit`. `ACCEPTANCE_UNMET` and `REVIEW_REQUIRED`
  are `judgment`. `ACCEPTANCE_UNMET` is also reported by `closure_status` when
  the branch has no commits; record that as its `tool` hint without changing
  its class.
- `PUSH_PENDING` is a status, not a failure. Record it with a `kind` of
  `status` so later checks do not treat it as a stop.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Template text, checks over managed text (task 163), and the Governed execution
and handoff gates (task 166).

## Dependencies

- **Depends on**: —
- **Blocks**: 163, 166, 168
