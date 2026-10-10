# Task 192 — Allow SPIKE execution evidence at integration

> **ID**: `192`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Assigned to**: unassigned
> **Session**: GitHub issue triage, 2026-10-10

## Objective

Fix [issue #10](https://github.com/biagiolibe/meridian/issues/10): declared SPIKE
validation writes `.meridian/execution-evidence.json`, but the SPIKE integration
path check rejects that file. Keep the existing evidence location and permit
the ledger produced by the supported validation command.
Authority: `docs/ADR_STOPS_AND_DENIALS.md`, the satisfiable gate contract.

## Acceptance Criteria

- [x] A regression reproduces a SPIKE running its declared validation through
  `meridian execution validate` and integrating its durable evidence.
- [x] The canonical execution-evidence ledger is allowed by the SPIKE path
  check, without weakening validation evidence checks or allowing arbitrary
  `.meridian/` paths, production code, or undeclared deliverables.
- [x] Integration retains the evidence bytes and accepts the valid SPIKE
  candidate without restoring or removing the ledger as a workaround.
- [x] Tests cover allowed evidence, a disallowed neighboring path, declared
  deliverables, and existing non-SPIKE behavior.
- [x] Document the allowed evidence path and add a changelog fragment.
- [x] Repository checks, the full unit suite, and `git diff --check` pass.

## Relevant Files

`scripts/meridian.py`, `tests/test_meridian_cli.py`,
`docs/WORKTREE_LIFECYCLE.md`, `changelog.d/`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Moving the evidence ledger, evidence freshness policy, and generic changes to
the SPIKE allowlist.

## Dependencies

- **Depends on**: 142
- **Blocks**: 193
