# Task 122 — Define the bounded gate per integration outcome

> **ID**: `122`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Follow-up of the task 118 efficiency analysis (2026-10-03)

## Objective

The "bounded gate" required after `integrate stage` is named in code and docs
but never defined, so agents default to rerunning the full suite even for a
`REUSE` decision whose candidate code equals the validated code. Define the
candidate validation content for each outcome, aligned with the command check
added by task 121, without weakening any existing gate.

## Acceptance Criteria

- [ ] `docs/WORKTREE_LIFECYCLE.md` defines the candidate validation per outcome:
  - `REUSE`: `check_repository.py`, `git diff --check`, and a proof that every
    non-governance path is unchanged between the validated task commit and the
    staged candidate tree.
  - `BOUNDED`: the `REUSE` gate plus the tests of the modules changed by the
    task and by the advanced `main`.
  - `FULL`: the full test suite plus the `REUSE` gate.
- [ ] The documented proof for `REUSE` names a deterministic command, such as a
  `git diff --name-only` between the two trees, and states that governance
  files (task record, handoff, queue, plan, archive, changelog fragment) are the
  only permitted differences.
- [ ] The Lean Delivery templates and this repository's `PROJECT_WORKFLOW.md`
  point to that definition instead of restating it, and keep their managed
  capability markers consistent.
- [ ] Governed SDD wording is not changed except to cross-reference the same
  definition if it already names a bounded gate.
- [ ] The document states that a stricter gate (the full suite) remains
  permitted at any outcome and is never rejected.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/WORKTREE_LIFECYCLE.md` | Normative definition. |
| `PROJECT_WORKFLOW.md` | Local pointer. |
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md` | Shipped pointer. |
| `docs/TASK_CLOSURE_DESIGN.md` | C7 step and Decision 2 context. |

## Technical Context

- `decide_integration_validation` in `scripts/meridian.py` selects the outcome;
  its `REUSE` and `BOUNDED` comment says both require the mandatory bounded
  gate but does not define it.
- Only `REUSE` has a strong equivalence argument (main equals the validated
  base), so its reduced gate is safe only with the unchanged-paths proof.
- Edits to managed regions follow the capability-marker rules in
  `CONTRIBUTING.md`; a template change may need a release step.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Code changes to `finalize` or `stage`, new decision outcomes, and changes to
Governed SDD gates.

## Dependencies

- **Depends on**: 121
- **Blocks**: none
