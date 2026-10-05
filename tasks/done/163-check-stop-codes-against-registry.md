# Task 163 — Check that managed text and tests agree with the stop-code registry

> **ID**: `163`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

A registry is useful only if the text and the code cannot drift away from it.
Make `scripts/check_repository.py` fail when managed text names an
unregistered stop code, or when a `tool`-class code has no test that proves
its output.

## Acceptance Criteria

- [ ] `check_repository.py` collects every stop-code token used as a stop in
  managed templates and in this repository's own managed copies. A token counts
  when it follows `BLOCKED` or appears in a stop-code list. The check fails, naming
  the file, line, and token, when a token is not in
  `capabilities/stop-codes-v1.json`.
- [ ] It fails when a registry entry of class `tool` has no `test` field, or
  when that test name does not exist in `tests/`.
- [ ] It fails when a registered code is not mentioned in any managed text or
  emitted by the CLI, so that dead entries are removed.
- [ ] The check does not yet require every `BLOCKED` line to carry a code;
  that requirement belongs to task 169.
- [ ] Tests cover an unregistered token, a missing test, a dead entry, and the
  passing repository.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | New check. |
| `capabilities/stop-codes-v1.json` | Registry from task 162. |
| `tests/` | Check tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decision 3.
- The stop-code list is repeated in `tests/test_project_console.py`; read it
  before choosing the token pattern so that the console's list is covered too.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing template wording and assigning codes to gates that have none.

## Dependencies

- **Depends on**: 162
- **Blocks**: 169
