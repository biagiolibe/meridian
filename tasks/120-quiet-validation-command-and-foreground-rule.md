# Task 120 — Quiet validation command and foreground rule for long checks

> **ID**: `120`
> **Category**: Documentation / Test hygiene
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up of the task 118 efficiency analysis (2026-10-03)

## Objective

Reduce the time and context spent on the full test suite. The current profile
command (`unittest ... -v 2>&1 | tail -n 200`) prints nothing until the suite
ends, lists one line per test, and lets expected-failure noise from the
release/publish tests reach the agent. Together these pushed task 118 into
detached background runs with polling. Replace the command, state the foreground
rule, and remove the noise at its source without hiding real failures.

## Acceptance Criteria

- [ ] `docs/EXECUTION_EVIDENCE_PROFILE.md` declares
  `set -o pipefail` and `python3 -m unittest discover -s tests -q 2>&1 | tail -n 40`
  as the full-suite command. `check_repository.py` and `git diff --check` keep
  their `pipefail` plus `tail` form and exit-status preservation.
- [ ] The profile states that a command expected to run longer than a minute
  runs in the foreground with a timeout of up to 600 seconds (or a persistent
  terminal session), and is never detached and polled.
- [ ] The Lean Delivery and Governed SDD template profiles state the same
  foreground rule in stack-neutral wording; they do not gain a Python-specific
  command.
- [ ] Release/publish tests that exercise expected failures no longer write
  their expected diagnostics to the suite's stderr, and the suppression lives
  inside those tests.
- [ ] A test proves that a genuinely failing assertion inside the same test
  module still produces visible failure output and a non-zero exit status.
- [ ] No test is removed, skipped, or weakened. The unit test count does not
  decrease.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Project command and foreground rule. |
| `templates/workflows/lean-delivery/docs/EXECUTION_EVIDENCE_PROFILE.md` | Neutral foreground rule. |
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Neutral foreground rule. |
| `tests/test_release.py` | Source of expected-failure noise (confirm others before editing). |
| `docs/PLAN_TOKEN_EFFICIENCY.md` | Prior decision requiring `pipefail` and exit-status preservation. |

## Technical Context

- `docs/PLAN_TOKEN_EFFICIENCY.md` makes `set -o pipefail` mandatory and treats
  the `tail` bound as a project choice; this task changes the bound and the
  verbosity only, not coverage or exit status.
- Locate the noisy tests by running the suite once and inspecting stderr before
  editing; do not guess the modules.
- Template changes may need a release and migration step if the repository
  ships managed capability markers; follow `CONTRIBUTING.md` for template edits.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing `integrate finalize`, defining the bounded gate, test sharding, and any
change to which tests run.

## Dependencies

- **Depends on**: none
- **Blocks**: 121
