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
- [ ] A project has one of three declaration states: `declared` (fragments per
  outcome, enforced by `finalize`), `none` (an explicit, recorded choice that
  imposes no fragment and keeps the pre-121 behavior: a non-empty list of
  non-empty command strings is accepted), or `undeclared` (no choice recorded).
  `undeclared` is never a silent pass; see the first-use stop below.
- [ ] This repository declares its own fragments (`scripts/check_repository.py`
  for every outcome and `unittest discover` for `FULL`), so task 121's behavior
  is preserved here.
- [ ] The declaration location is documented, readable by Lean Delivery and
  Governed SDD, and validated: a malformed declaration blocks `finalize` with a
  clear error instead of silently accepting any evidence.
- [ ] The comparison stays a pure string check that executes nothing and accepts
  the `set -o pipefail;` prefix and an output-bounding pipeline.
- [ ] The declaration is a small machine-readable project file under
  `.meridian/` (not prose in a Markdown document), versioned, and not a managed
  template file, so later upgrades cannot conflict with project values.
- [ ] First-use stop: when the first task of an `undeclared` project reaches
  integration, the lifecycle stops once with `BLOCKED
  UNDECLARED_VALIDATION_COMMANDS` and a resume command, before any merge, lease,
  or staged state exists. Put the check in `integrate stage` (or the earlier
  `worktree evidence` or `closure-status` step) and not in `finalize`, which
  would leave a staged merge to abort. Record in the handoff why the chosen step
  is the earliest safe one and confirm that tasks that do not integrate are not
  stopped.
- [ ] The stop carries evidence for the developer: the commands the task
  actually ran for validation and a proposed declaration. The agent never writes
  the declaration itself; `Proceed with` does not authorize it. Recording it
  needs an explicit developer decision: accept the proposal, supply other
  commands, or choose `none`. After any of the three the stop never recurs.
- [ ] Rollout to existing adopters follows three levels and never infers values
  during `upgrade --apply`:
  1. The migration delivers only the structure: the declaration point in the
     `undeclared` state. If the migration engine cannot create a project-owned
     unmanaged file, record that finding and deliver the file through
     `meridian setup` instead. A missing file is treated as `undeclared`.
  2. `meridian codex doctor` or `audit` reports an `undeclared` project as an
     advisory gap, never as an error that blocks unrelated work, so the gap is
     visible before the first integration.
  3. `meridian setup` may propose values from the detected stack and writes them
     only after explicit consent; a project can always edit the file by hand.
- [ ] Before implementing, verify and record two open points: whether a migration
  can create an unmanaged project file, and whether `setup` already has a way to
  propose values from the detected stack. Report the result in the handoff.
- [ ] The release is template-changing and shares one migration and one
  `workflowBaselineVersion` bump with task 123, as agreed for a single release
  after all queued tasks. It carries Upgrade notes per
  `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` naming the optional manual step
  (declaring the commands or choosing `none`) and the one-time stop that
  the first integrating task of an undeclared project will report.
- [ ] Tests cover: `undeclared` stops once before staging with no lease or merge
  left behind, `none` accepted with any non-empty evidence, declared fragments
  enforced per outcome, malformed declaration blocked, the stop not recurring
  after any of the three choices, this repository's declaration, and both
  workflow modes.
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
- The one-time stop is intentional: it follows the existing rule that a failed
  gate stops once with `BLOCKED <reason>` and a resume command, and it replaces
  the earlier idea that an undeclared project passes silently. The cost is one
  interruption for the first integrating task of each adopter project.
- A migration cannot ask questions or infer project values: a wrong inferred
  command would block `finalize` in a project that worked before. Structure is
  delivered by the migration; values are supplied only by the project or with
  its consent.
- `PROJECT_WORKFLOW.md` already holds one project-filled line (`Project
  integration smoke command`) as a precedent for a project declaration, but
  enforcement should not depend on parsing prose.
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
