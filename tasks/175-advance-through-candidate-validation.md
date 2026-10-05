# Task 175 — Let `advance` finalize from supplied candidate validation results

> **ID**: `175`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Closure simplification follow-up to ADR stops and denials, 2026-10-05

## Objective

After task 174, `advance` stops at C7 and asks the agent to run the candidate
validation. Today the agent must then write a candidate-bound evidence file by
hand and call `integrate finalize`, or `integrate abort` on failure. Let
`advance` take the results and perform C8, or the abort, itself.

## Acceptance Criteria

- [ ] `advance` accepts `--candidate-command CMD --candidate-exit-code N`,
  repeatable. With a staged integration at C7, it writes the candidate-bound
  evidence file in the schema that `integrate finalize` requires, bound to the
  staged candidate tree, and runs `integrate finalize`.
- [ ] When any supplied exit code is non-zero, or a required command for the
  stage outcome is missing, `advance` runs `integrate abort` and reports
  `CANDIDATE_VALIDATION_FAILED` or `UNDECLARED_VALIDATION_COMMANDS`, with the
  resume step. It never finalizes on partial evidence.
- [ ] A candidate tree that changed after stage is reported as
  `EVIDENCE_MISMATCH`, with abort and restage as the resume step.
- [ ] After finalize, `advance` returns `action_required: push`.
- [ ] Each step and stop is written to the journal.
- [ ] Tests cover a successful finalize, a failed command, a missing required
  command, a changed candidate tree, and a rerun after an interruption between
  finalize and push.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `advance`, `integrate finalize`, `integrate abort`, candidate evidence schema. |
| `docs/WORKTREE_LIFECYCLE.md` | Candidate evidence and `advance` documentation. |
| `tests/test_meridian_cli.py` | Tests. |

## Technical Context

- The candidate evidence schema and the per-outcome required commands are
  documented in `docs/WORKTREE_LIFECYCLE.md`, and they are enforced by
  finalize. Reuse that validation; do not add a second schema.
- The agent still runs every validation command itself. `advance` only
  records the results the agent supplies.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Running validation commands, pushing, and template text.

## Dependencies

- **Depends on**: 174
- **Blocks**: 176
