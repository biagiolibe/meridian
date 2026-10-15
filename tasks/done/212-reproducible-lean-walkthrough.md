# Task 212 — Add a reproducible Lean Delivery walkthrough

> **ID**: `212`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

Show a newcomer what a Meridian project looks like after its first task,
without committing a sample project whose copies would drift from the
templates. The walkthrough lists real CLI commands, and a test runs them so
the example cannot silently go stale.

## Acceptance Criteria

- [x] `docs/examples/LEAN_DELIVERY_WALKTHROUGH.md` walks one small task in a
  new Lean Delivery project. It covers the initialized files, the task record,
  `worktree prepare`, implementation, the handoff, `worktree advance`, and
  `cleanup`. It shows short excerpts of the resulting queue, plan, and handoff.
- [x] Every CLI command in the walkthrough is in a fenced block that a test
  extracts and runs in order, in a temporary project with a local bare
  `origin`. The test fails when a command exits non-zero, or when an excerpt
  marked as checked no longer matches the generated file.
- [x] Steps that run inside an agent host, such as `/meridian-init`, are
  marked as host steps. The test reproduces them through the CLI or fixture
  path that the skill uses, and the walkthrough says so.
- [x] `docs/QUICKSTART.md` links the walkthrough.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/examples/LEAN_DELIVERY_WALKTHROUGH.md` | New walkthrough. |
| `tests/` | Walkthrough execution test. |
| `docs/QUICKSTART.md` | Link from the quick start (task 211). |

## Technical Context

- Reuse the existing test helpers that create temporary projects and bare
  remotes. Do not add a second fixture mechanism.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

A Governed SDD walkthrough and a committed sample project.

## Dependencies

- **Depends on**: 211
- **Blocks**: none
