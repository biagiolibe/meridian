# Task 125 — Make candidate validation commands project-declared and align the gate docs for both workflows

> **ID**: `125`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Review of task 121 for Governed SDD and consumer projects, 2026-10-03

## Objective

Task 121 made `integrate finalize` require the literal fragments
`scripts/check_repository.py` and `unittest discover` in candidate validation
evidence. Task 122 then documented `python3 scripts/check_repository.py` and
`git diff --check` as the "universal gate" for every outcome, in the shipped
Lean Delivery templates only. Those strings describe this repository, but
`finalize` and the shipped templates serve every Meridian project, Lean Delivery
and Governed SDD alike. A consumer project without those scripts (for example a
Rust project) can no longer finalize an integration, and its shipped template
instructs a command it does not have. Replace the hard-coded fragments with a
project declaration and align the gate documentation for both workflows before
the next release.

## Acceptance Criteria

- [ ] The mandatory candidate-validation command fragments are read from a
  project-owned declaration, per integration outcome (`REUSE`, `BOUNDED`,
  `FULL`), not from constants in `scripts/meridian.py`.
- [ ] A project without a declaration keeps the pre-121 behavior: a non-empty
  list of non-empty command strings is accepted. No consumer is blocked by this
  change.
- [ ] This repository declares its own fragments (`scripts/check_repository.py`
  for every outcome and `unittest discover` for `FULL`), so task 121's behavior
  is preserved here.
- [ ] The declaration location is documented, readable by Lean Delivery and
  Governed SDD, and validated: a malformed declaration blocks `finalize` with a
  clear error instead of silently accepting any evidence.
- [ ] The comparison stays a pure string check that executes nothing and accepts
  the `set -o pipefail;` prefix and an output-bounding pipeline.
- [ ] If the declaration is a managed template file, the release carries the
  migration and Upgrade notes required by `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`.
- [ ] Tests cover: undeclared project accepted, declared fragments enforced per
  outcome, malformed declaration blocked, this repository's declaration, and
  both workflow modes.
- [ ] `docs/WORKTREE_LIFECYCLE.md` and
  `templates/workflows/lean-delivery/docs/WORKTREE_LIFECYCLE.md` (task 122) are
  corrected so the gate is expressed as the project's declared repository check
  and full suite, and this repository's script names appear only as its own
  declaration.
- [ ] The Governed SDD templates (`LIFECYCLE_ORCHESTRATION.md`, `REVIEW.md`,
  `COMPLETION_REPORT_TEMPLATE.md`, and its `WORKTREE_LIFECYCLE.md` if shipped)
  carry the same per-outcome gate definition (`REUSE`, `BOUNDED`, `FULL`) and the
  governance-only path proof, which task 122 added to Lean Delivery only. The
  strength of no Governed gate changes; only the wording is aligned.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `CANDIDATE_VALIDATION_COMMANDS` and `missing_candidate_validation_commands`. |
| `docs/WORKTREE_LIFECYCLE.md` | Candidate evidence contract (task 121) and gate definition (task 122). |
| `templates/workflows/*/` | Lean gate wording to generalize; Governed wording to add. |
| `tests/test_task_worktree_isolation.py` | Finalize tests added by task 121. |
| `.meridian/` and workflow templates | Candidate locations for the declaration. |

## Technical Context

- Task 121's own brief asked to resolve how consumers declare these strings
  before implementing; the merged change did not, which is the defect fixed here.
- Choose the declaration home by existing precedent (the project's
  `.meridian/` configuration or its workflow document) and justify the choice;
  prefer a location that already reaches Governed SDD projects.
- Not yet released if no tag includes `844e7ad`; confirm before deciding whether
  consumers can already be affected.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the outcome definitions chosen by task 122, executing commands, and
changing `integrate stage` decisions.

## Dependencies

- **Depends on**: 121, 122
- **Blocks**: none
