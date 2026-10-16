# Task 228 — Start a new budget attempt only by explicit re-preparation

> **ID**: `228`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: GitHub issue #15 triage, 2026-10-16
> **Origin**: friction

## Objective

Fix [issue #15](https://github.com/biagiolibe/meridian/issues/15). Retiring a
task worktree and re-preparing the task keeps the budget spends of the retired
attempt. `resolve_budget_key` (`scripts/meridian.py`) increments the attempt
only on a `READY_FOR_REVIEW -> IN_PROGRESS` status change, and the ledger lives
in the shared `.git/meridian-budget.json`. A re-prepared task therefore starts
with counters it never used, and can stop at once with `BLOCKED
BUDGET_EXHAUSTED`.

Resetting the counters automatically on re-preparation would open a bypass: a
commit-less worktree can be retired with commands an agent may run
(`git worktree remove` without `--force`, `git branch -d`), so an agent could
reset an exhausted cap by retiring and re-preparing. Make inherited spends
visible and let a new attempt start only through an explicit, journaled,
developer-authorized option.

## Acceptance Criteria

- [ ] `meridian worktree prepare <TASK-ID>` stops with a registered stop code
  before creating a worktree when the task's current budget attempt has
  recorded spends and the task has no registered worktree. The message lists
  the inherited counters and the resume command.
- [ ] `meridian worktree prepare <TASK-ID> --new-attempt --reason "<text>"`
  starts the next attempt: the attempt number increases, the new
  `<TASK-ID>:<attempt>` key starts at zero, and the previous attempt's
  counters stay in the ledger unchanged. The command journals the task, the
  previous and new attempt, the reason, and the counters carried as history.
  It refuses `--new-attempt` without `--reason`, and when the task still has a
  registered worktree.
- [ ] `--new-attempt` never changes the task record's caps or status and never
  deletes ledger entries.
- [ ] The governed-SDD workflow text states that only the developer
  authorizes `--new-attempt`, as with a budget overrun, and that an agent
  stops with the new stop code instead. If managed text inside capability
  markers must change, the change ships with its migration, and the handoff
  records that the release becomes template-changing.
- [ ] `meridian budget show <TASK-ID>` prints the current attempt number, and
  the queue briefing shows it for a task whose attempt is above 1 or whose
  current attempt has spends.
- [ ] The existing bump on `READY_FOR_REVIEW -> IN_PROGRESS` keeps working.
- [ ] Tests cover:
  - the stop on a re-prepare with inherited spends;
  - a re-prepare with no spends, which proceeds as today;
  - `--new-attempt` with a reason, including the journal entry and the
    preserved history;
  - `--new-attempt` refused without a reason and with a registered worktree;
  - the attempt number in `budget show`;
  - the existing review-remediation bump.
- [ ] A changelog fragment `changelog.d/228.md` records the fix under
  `Fixed` and the new option under `Added`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `resolve_budget_key`, `budget_show`, `budget_spend`, `prepare_task_worktree`, journal. |
| `hooks/queue-briefing.sh` | Queue briefing output. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Budget and overrun rules. |
| `capabilities/stop-codes-v1.json` | Registry for the new stop code. |
| `migrations/` | Required only if managed marker text changes. |
| `tests/` | Budget and worktree tests. |

## Technical Context

- The issue lists three options. Automatic reset on prepare (option 1) is the
  bypass described above. Bumping on `IN_PROGRESS -> QUEUED` (option 3) does
  not apply, because retiring a worktree performs no status transition. This
  task takes the explicit command (option 2) and places it on `prepare`,
  where the inherited spends become visible.
- Editing `.git/meridian-budget.json` by hand is forbidden as false state; the
  journal entry is the audit trail for the reset.
- Issue #11, now closed, explains why a prepared worktree cannot be moved, so
  retiring and re-preparing remains the recovery for a design change on
  `main`.

## Out of scope

Changing budget caps or their defaults. Lean Delivery budgets, if any differ.
Re-delivery after handoff correction (task 227).

## Dependencies

- **Depends on**: none
- **Blocks**: none. Task 227 also edits `scripts/meridian.py`; run them one
  after the other.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/228-budget-attempt-on-re-prepare.md)"$'\n\nExecute this task in the current project.'
```
