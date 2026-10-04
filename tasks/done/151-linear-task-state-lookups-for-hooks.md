# Task 151 — Make hook task-state lookups linear and keep the briefing within its timeout

> **ID**: `151`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2.5h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D14, 2026-10-04

## Objective

In a Governed SDD project with about 300 task records (Palimpsest, CLI 1.2.7), the
`UserPromptSubmit` queue-briefing hook runs 21 to 30 s and exceeds its 5 s
timeout on every prompt, so Claude Code discards its output, including the
language-policy reminder. Measured breakdown: `meridian locations` and
`meridian setup --check` take about 0.2 s each; `meridian worktree states`
takes 21.4 s. A profile of `registered_worktree_task_states` showed 302
`resolve_task_identity` calls (23.4 s), 303 `_task_authorities` calls (18.7 s),
91,506 `_task_record_id` reads, and 606 Git subprocesses.

Cause: `registered_worktree_task_states` (`scripts/meridian.py`) iterates every
task authority and calls `resolve_task_identity(..., "existing")` for each, and
every call recomputes `_task_authorities` over all task records and spawns
`git check-ref-format`. The cost is O(n²) in the number of tasks.
`active_worktree_task`, which both read-guards call on every `Read` in a task
worktree, has the same loop, so the read-guard hook can also exceed its 5 s
timeout in large projects.

Make these lookups proportional to the in-flight tasks, keep every hook well
within its timeout, and make the briefing degrade instead of losing its output.

## Acceptance Criteria

- [ ] `registered_worktree_task_states` and `active_worktree_task` enumerate the
  lifecycle state files under the Git common directory's `meridian-worktrees/`
  (and, for `active_worktree_task`, only the state matching the current
  worktree's branch), and resolve identities only for those tasks. They never
  iterate every task authority.
- [ ] Identity resolution inside one command computes the task-authority map, the
  task-identity policy, and the project locations once and reuses them; a test
  proves `_task_authorities` runs at most once per `worktree states` and per
  `active_worktree_task` call, and that the number of Git subprocesses does not
  grow with the number of task records.
- [ ] Every other loop in `scripts/meridian.py` that calls `resolve_task_identity`
  or `_task_authorities` per task is reviewed; any with the same O(n²) pattern is
  fixed the same way and listed in the handoff, or listed with the reason it is
  not affected.
- [ ] Results are unchanged: the existing worktree-states, active-task,
  read-guard, briefing, console, and stage tests pass without modification of
  their expectations.
- [ ] A regression test builds a synthetic Governed project with 300 task records
  and a few registered task worktrees, and asserts that `meridian worktree states
  --format json` completes in under 1 s and the whole `hooks/queue-briefing.sh`
  in under 2 s on the CI runner, alongside the structural call-count assertions
  above (the structural assertions are the primary guard; the time budgets catch
  regressions they miss).
- [ ] `hooks/queue-briefing.sh` prints the language-policy reminder and the queue
  briefing before any optional lookup. It bounds the `worktree states` call
  separately (about 2 s, portable on macOS and Linux without GNU `timeout`), and on
  timeout or error it omits only the in-progress section and prints one line
  saying it was skipped. The script's total stays under the 5 s hook timeout.
- [ ] `meridian setup --check` reports, as an advisory without writing anything,
  a Claude Code user or project settings entry that registers
  `queue-briefing.sh` or `read-guard.sh` directly while the Meridian plugin is
  enabled, naming the settings file and the duplicate command. Documentation
  states that no Meridian command writes such an entry.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI and
  plugin-hook change with no template text or capability-version change and no
  migration.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `registered_worktree_task_states` (~line 1030), `active_worktree_task` (~line 988), `resolve_task_identity`, `_task_authorities`, `_lifecycle_paths`, `setup --check`. |
| `hooks/queue-briefing.sh` | Output order and the bounded `worktree states` call. |
| `hooks/read-guard.sh`, `scripts/codex_read_guard.py` | Callers of the active-task lookup. |
| `tests/` | Performance regression, call-count, hook degradation, and setup advisory tests. |

## Technical Context

- Measured in Palimpsest on 2026-10-04 (four runs, normal load): hook wall time
  21.4 s, 29.7 s, 27.4 s; cProfile of `registered_worktree_task_states`: 27.6 s.
- The duplicate registration observed in one installation was a hand-written
  absolute-path entry in user settings; no Meridian command writes Claude Code
  hook entries (`setup` writes only the project command allowlist). It doubled
  the briefing and its cost.
- The `queue-briefing` v1 capability text does not change.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `bash hooks/queue-briefing.sh` timed against a synthetic 300-task project
- `git diff --check`

## Out of scope

Changing hook timeouts in `hooks/hooks.json`, the briefing content, task-identity
rules, and writing Claude Code settings.

## Dependencies

- **Depends on**: —
- **Blocks**: none
