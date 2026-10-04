# Task 166 — Give codes and actionable messages to the execution and handoff gates

> **ID**: `166`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: ADR stops and denials, 2026-10-05

## Objective

The Governed SDD execution and handoff gates print free-text `BLOCKED`
messages with no code under the prefixes `execution preflight`,
`execution contract`, `execution evidence`, `execution reconcile`, and
`handoff check`. Some messages describe a different problem from the real one.
Issue #5 is one example: a correct "no isolated exploration" statement fails
with a message saying that an exploration was declared. The handoff gates also
compare free text with exact strings. Make these gates meet the
"actionable" property of the gate contract in
`docs/ADR_STOPS_AND_DENIALS.md`.

## Acceptance Criteria

- [ ] Every `BLOCKED` raised by `execution_preflight`, the execution contract,
  evidence and reconcile checks, `verify_execution_evidence`, and
  `check_handoff` is emitted through the registry helper with a registered code.
- [ ] For each gate that compares values, the message names the rule, the field
  or source checked, the accepted values, and the value found.
- [ ] Issue #5: when no investigation is recorded, `Isolated exploration`
  accepts `none` and a value that starts with `none` or `no` followed by text.
  Otherwise the message says that `none` is expected and quotes the value found.
  A `none` value with recorded investigations still fails, with its existing
  meaning.
- [ ] A required handoff field written with text between its name and the
  colon, such as `- Validation (commands):`, is reported as a format problem
  that names the expected form `- <Field>: <value>`, not as a missing field.
- [ ] Existing passing handoffs still pass. The tests cover issue #5's wording,
  the mis-formatted field, and the message of every newly coded gate.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `execution_preflight`, `verify_execution_evidence`, `check_handoff`, and the execution contract and reconcile checks. |
| `capabilities/stop-codes-v1.json` | New `tool` codes. |
| `tests/test_meridian_cli.py` | Gate tests. |

## Technical Context

- Authority: `docs/ADR_STOPS_AND_DENIALS.md`, Decision 2, property 3.
- GitHub issue #5 and the second comment on issue #6 describe the observed
  messages.
- The satisfiability fix for the queue comparison in `execution_preflight` is
  task 167. Here, give that message a code and make it name its sources, but do
  not change what it accepts.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing what the gates accept beyond issue #5, freshness of execution
evidence, and the validation, investigation, and budget gates (task 169).

## Dependencies

- **Depends on**: 162
- **Blocks**: 167, 169
