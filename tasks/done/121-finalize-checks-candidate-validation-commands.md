# Task 121 — Verify mandatory commands in candidate validation evidence

> **ID**: `121`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up of the task 118 efficiency analysis (2026-10-03)

## Objective

`meridian worktree integrate finalize` accepts candidate validation evidence if
`scope` matches and `commands` is a non-empty list of strings. It never checks
which commands ran, so a weak gate and a full suite are indistinguishable.
Make `finalize` require the mandatory command strings for the staged scope.
The check compares strings only and executes nothing.

> Risk note: this changes deterministic lifecycle behavior. The developer
> accepted handling it under Lean Delivery. The check only adds a rejection
> condition, so it cannot weaken an existing gate.

## Acceptance Criteria

- [ ] For every staged decision (`REUSE`, `BOUNDED`, `FULL`), `finalize` blocks
  unless `commands` contains an entry that invokes `scripts/check_repository.py`.
- [ ] For `FULL`, `finalize` additionally blocks unless `commands` contains an
  entry that invokes the full unittest discovery (`unittest discover`).
- [ ] For `REUSE` and `BOUNDED`, the full suite is not required.
- [ ] The match rule is documented, deterministic, and tolerant of the
  `set -o pipefail;` prefix and an output bound such as `| tail -n 40`.
- [ ] A rejected evidence file names the missing mandatory command in the error
  and leaves the staged merge and lease untouched.
- [ ] Existing valid evidence for `FULL` runs and for `REUSE` and `BOUNDED`
  runs that already include `check_repository.py` still finalizes.
- [ ] The project mandatory commands come from one declared place (a constant or
  the project's workflow configuration), not hard-coded per call site.
- [ ] Tests cover: each decision accepted with the mandatory commands; each
  decision rejected when `check_repository.py` is missing; `FULL` rejected
  without the suite; `REUSE` accepted without the suite; pipefail and tail
  tolerance; no state change on rejection.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `finalize` evidence validation near the `required_scope` check. |
| `tests/test_meridian_cli.py` | Lifecycle finalize tests. |
| `docs/WORKTREE_LIFECYCLE.md` | Candidate evidence contract. |

## Technical Context

- `finalize` already compares `candidate_tree`, `passed`, and `scope`; add the
  command check beside them and before the commit.
- A consumer project may not use `check_repository.py`. Resolve how the
  mandatory strings are declared for projects other than this repository before
  implementing, and report the decision if it needs more than a constant.
- Lifecycle commands must never execute shell, hook, validation, smoke, or
  project-provided commands; keep this a pure string comparison.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Defining the bounded gate's content for consumers (task 122), executing or
re-running any command, and changing `integrate stage` decision logic.

## Dependencies

- **Depends on**: 120
- **Blocks**: 122
