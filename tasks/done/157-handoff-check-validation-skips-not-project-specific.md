# Task 157 — Stop `handoff-check` requiring one hard-coded Meridian test as the only valid skip

> **ID**: `157`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Fusa task closure blocked by `Validation skips`, 2026-10-04

## Objective

`meridian execution handoff-check` accepts the handoff field `Validation skips`
only as `none` or as a text that contains one fixed test name and one fixed
reason from a past Meridian task (`TASK_099_SKIP_TEST` and
`TASK_099_SKIP_REASON`, `scripts/meridian.py` ~line 8922). The test,
`AgentLaunchTest.test_split_payload_compiles_as_applescript`, belongs to
Meridian's own suite. A consumer project cannot declare a skip of its own, and
the error text names Meridian's test, which led a Fusa agent to look for it in a
repository where it does not exist. The workflow documents and
`docs/COMPLETION_REPORT_TEMPLATE.md` describe a general rule (test name,
test-reported reason, reporting command), so the code is stricter and narrower
than the contract.

Remove the comparison against the fixed test and reason. Keep the checks that
catch contradictions the code can see.

## Acceptance Criteria

- [ ] `verify_validation_skips` no longer references a fixed test name or reason;
  `TASK_099_SKIP_TEST` and `TASK_099_SKIP_REASON` are removed.
- [ ] A handoff whose `Validation skips` value is any non-empty text other than
  `none` passes this check when the `Validation` field has no failing exit
  status, whatever the text names. No format is enforced by the code.
- [ ] `none` together with a failing validation (a `Validation` field containing
  `exit` followed by a non-zero number) is still rejected, with the existing
  message wording that a failing validation needs a named skip.
- [ ] A non-`none` skip together with a failing validation is still rejected with
  the existing message that a named skip does not make a failing validation pass.
- [ ] A missing or empty `Validation skips` field is still rejected by the
  existing `HANDOFF_FIELDS` presence check, unchanged.
- [ ] No error message produced by `handoff-check` names a test of another
  project.
- [ ] The tests cover: `none` with exit 0 (pass); a skip naming a test that does
  not exist in Meridian, written in the documented form (pass); a free-text skip
  with exit 0 (pass); `none` with exit 1 (fail); a skip with exit 1 (fail); an
  absent field (fail). The existing Task 099 test is rewritten, not deleted.
- [ ] The workflow and template text that describes `Validation skips` is read
  and, if it implies the code enforces the documented form, adjusted to say the
  form is guidance; `scripts/check_repository.py` managed-copy digests stay
  consistent.
- [ ] One changelog fragment states the fix.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `verify_validation_skips` (~9138), the two constants (~8922), the caller (~9227). |
| `tests/test_meridian_cli.py` | `test_handoff_accepts_task_099_named_skip_and_rejects_an_unnamed_failure` (~4054) and handoff fixtures using `Validation skips: none`. |
| `docs/COMPLETION_REPORT_TEMPLATE.md`, `templates/workflows/*/docs/COMPLETION_REPORT_TEMPLATE.md` | Field description; change only if it implies enforcement. |
| `templates/workflows/*/PROJECT_WORKFLOW.md`, `docs/workflows/*.md` | The "named sandbox skip" sentence; change only if it implies enforcement. |

## Technical Context

- Observed on Fusa on 2026-10-04: `handoff-check` blocked a handoff with a
  message naming `AgentLaunchTest.test_split_payload_compiles_as_applescript`;
  the task's own validation had passed with exit 0 and no test was skipped. What
  Fusa's report contained in the field was not seen.
- The fixed test lives in `tests/test_project_console.py` and is Meridian's own.
- Decision recorded here: no per-project allow-list and no format check. The name
  of a skipped test was never evidence; the durable execution evidence and the
  reviewer are. A format check can be added later if free-text skips cause a
  concrete problem.
- Changing the managed-copy text, if needed, makes the release template-changing
  and needs a migration; prefer leaving the text unchanged when it does not imply
  enforcement.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

A per-project allow-list in `.meridian/project.json`, a format check for the
field, recording skipped-test output in the durable execution evidence, and
changing the `HANDOFF_FIELDS` list.

## Dependencies

- **Depends on**: —
- **Blocks**: none
