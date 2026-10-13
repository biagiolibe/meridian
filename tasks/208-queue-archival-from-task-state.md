# Task 208 — Archive queue sections from task state

> **ID**: `208`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: GitHub issue #2 triage, 2026-10-13
> **Origin**: friction

## Objective

Implement Decision 8 (Amendment 1) of `docs/ADR_MACHINE_TASK_STATE.md`, which
answers [issue #2](https://github.com/biagiolibe/meridian/issues/2). Queue
archival decides from task state files instead of table text, so that:
- sections at any heading level can close;
- an `INCONCLUSIVE` spike closes its section;
- a project such as Palimpsest, with about 97 KB of queue under `##`
  sections, can shrink its queue.

Do not start this task until Amendment 1 is accepted.

## Acceptance Criteria

- [ ] `_archive_completed_queue_sections` treats a section as archivable when
  every task row in it has a state file, read through the shared reader by
  task ID, whose status is terminal for its workflow:
  - Governed SDD: `ACCEPTED`, `ANSWERED`, or `INCONCLUSIVE`;
  - Lean Delivery: `DONE`.
  Heading level, table shape, column order, and status-cell wording are not
  read for the decision. Section boundaries stay as today.
- [ ] A row without a state file falls back to the existing conservative rule,
  and a mixed section archives only when both rules agree. A legacy-only
  project behaves exactly as before.
- [ ] `meridian task state import --include-terminal` creates state files for
  terminal tasks from their current text. It prints what it would write and
  writes only with `--apply`. It never overwrites a file, and it stops with
  `TASK_STATE_INVALID` when texts disagree.
- [ ] `integrate stage` reports every section it archives and every section it
  retains, with the reason and the open or legacy rows. Nothing is skipped
  silently.
- [ ] Dependency satisfaction is unchanged: `INCONCLUSIVE` still does not
  satisfy a dependency.
- [ ] The archival rule in both managed `docs/WORKTREE_LIFECYCLE.md` copies
  (`worktree-lifecycle`), and in this repository's copy, states the
  state-based rule. It ships through the capability marker mechanism, with a
  migration whose `to` is the next release, extending an unreleased migration
  when one exists. `upgrade --check` on copies of the Palimpsest and Fusa
  manifests is recorded in the handoff.
- [ ] Tests cover:
  - a `##` section whose tasks are all terminal by state;
  - an `INCONCLUSIVE` spike section;
  - a section with one open state;
  - a legacy-only section, unchanged behavior;
  - a mixed section;
  - `--include-terminal`, dry run and `--apply`;
  - the archival report.
- [ ] One changelog fragment states the change under `Changed` and the
  adoption step under `Upgrade notes`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_archive_completed_queue_sections`, stage report, `task state import`. |
| `scripts/task_state.py` | Shared reader. |
| `templates/workflows/*/docs/WORKTREE_LIFECYCLE.md`, `docs/WORKTREE_LIFECYCLE.md` | Archival rule. |
| `migrations/` | Marker delivery. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decision 8 (Amendment 1).
- The current rule reads "Only `###` sections are archival candidates" in the
  managed copies (task 191).

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing dependency rules, the queue's Markdown format, and archiving historical
sections by hand.

## Dependencies

- **Depends on**: Amendment 1 of `docs/ADR_MACHINE_TASK_STATE.md`, accepted
- **Blocks**: none
