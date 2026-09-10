# Task 006 — Budget state, CLI, and hook echo

> **ID**: `006`
> **Category**: Feature (CLI + hooks)
> **Priority**: 🔴 P1
> **Estimate**: ~1–2 days
> **Assigned to**: unassigned

## 🎯 Objective

Give the numeric budgets from task 002 a durable home, a CLI that computes them, and
a hook that re-injects them at the end of the context every turn. This is the item
the audit exists to argue for.

## 📋 Acceptance Criteria

- [ ] `.meridian/budget.json` stores per-task-per-attempt counters.
- [ ] `meridian budget show <TASK-ID>` prints the current state.
- [ ] `meridian budget spend <TASK-ID> <kind>` increments, and **returns non-zero
      once the declared cap is reached**, with a message naming `BLOCKED` as the
      required next move.
- [ ] `hooks/queue-briefing.sh` prints the active task's budget line.
- [ ] The briefing stays silent in a non-Meridian project and when no task is active,
      matching the hook's existing behavior.
- [ ] Unit tests cover: increment, cap reached, unknown task, missing budget file,
      and a fresh allocation on a new attempt.
- [ ] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `budget` subcommand and state I/O. |
| `bin/meridian` | Subcommand wiring. |
| `hooks/queue-briefing.sh` | Echo. |
| `tests/test_meridian_cli.py` | Coverage. |

## 🧩 Technical Context

Reuses the control-plane pattern `bin/meridian adopt --assisted` already established:
durable state on disk, computed by a tool, read by an agent that cannot quietly
disagree with it. See `migrations/ASSISTED_ADOPTION.md` and the `NEXT_ACTION` state
machine in `scripts/meridian.py`.

State shape:

```json
{ "TASK-041:2": { "diagnostic": 2, "captures": 1, "expansions": 0 } }
```

Briefing shape:

```
[Meridian Governed Queue]
  🔴 In progress: TASK-041
  ⏱  Diagnostics 2/3 · Captures 1/2 · Expansions 0/2
  ⛔ On exhaustion: return BLOCKED. Do not raise a cap.
```

The mechanism is entirely about **position**: ~40 tokens at the end of the context
every single turn, at maximum salience, versus a rule read once at turn 1 and buried
25 turns deep by the time it matters.

## 🔨 Suggested Implementation

1. State I/O and the `budget` subcommand.
2. Cap lookup from the task file's override fields, falling back to the profile defaults.
3. Hook echo.
4. Tests.

## ⚠️ Constraints and Considerations

- **Keying — settle this before writing code.** Key by task, not session, so a budget
  cannot be reset by opening a new chat. But a *plain* task key breaks remediation:
  `Address review <TASK-ID>` is legitimate new work with its own diagnostics, and a
  task may go through several review attempts. Under a plain task key, attempt 3
  inherits an exhausted counter and must return `BLOCKED` immediately — the mechanism
  firing on a task that is proceeding correctly. Key by `<TASK-ID>:<attempt>`, where
  attempt increments on each `READY_FOR_REVIEW → IN_PROGRESS` transition; the reviewer
  already writes that transition in the review-handoff commit, so there is a natural
  hook and no new bookkeeping.
- **Known limitation, to be stated in the completion report, not hidden.** In this
  stage the model calls `spend`, so the count is still a self-report — the win is
  salience, not enforcement. Stage two (a separate future task) increments from a
  `PostToolUse` hook keyed on the validation-command pattern, making the count a side
  effect of *running the test*. Ship stage one first: most of the benefit, none of the
  pattern-matching brittleness.
- The hook has a 5s timeout. Keep it cheap.
- A recorded spend is durable, auditable evidence and belongs in the completion report.

## 🔗 Dependencies

- **Depends on**: 002
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/006-budget-cli-and-hook.md)"$'\n\nExecute this task in the current project.'
```
