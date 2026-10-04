# Task 143 — Make the read-guard and queue-briefing hooks independent of queue status

> **ID**: `143`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2.5h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D1/D8, design approved 2026-10-04

## Objective

Task branches no longer edit the queue (`TASK_CLOSURE_DESIGN.md`, Decision 2);
in-progress state is derived from the canonical branch, registered worktree, and
unarchived task record. Three hooks still read state from queue rows:

- `hooks/read-guard.sh` finds the active task by scanning the queue for
  `IN_PROGRESS` (Governed) or `[/]` (Lean); `scripts/codex_read_guard.py` does the
  same for Lean. Without that row, the task's own record and authority sources lose
  their exemption.
- `hooks/queue-briefing.sh` counts `IN_PROGRESS` and `READY_FOR_REVIEW` from rows.

The read-guard also exempts only `LANGUAGE_POLICY.md` and reads always-loaded files
from the legacy `docs/workflows/ENTRY_ROUTER.md`, so it denies a whole-file read of
`PROJECT_WORKFLOW.md` that the generated `CLAUDE.md`/`AGENTS.md` router requires
before any response (observed: 454 lines against a 400-line threshold). Its denial
message tells the agent to "raise" a profile field that older adoptions lack,
because the profile is project-owned and upgrades do not add the field.

## Acceptance Criteria

- [ ] Both read-guards derive the active task from the session's working directory:
  when it is a registered task worktree whose branch maps to one task identity
  (the same resolver `meridian worktree check` uses), that task is active. Queue
  status is never consulted. In the primary checkout there is no active task.
- [ ] The task's own record, its archive under `done/`, its handoff, its review
  record, and its `context authority` sources stay exempt, as today.
- [ ] The router read set is exempt from `Read-guard threshold` in both modes, but
  only up to a per-file ceiling: `LANGUAGE_POLICY.md`, `PROJECT_WORKFLOW.md`,
  `AGENTS.md`, `CLAUDE.md`, and every procedure file the generated router routes
  to, taken from one shared source (the router or `meridian context size --role`),
  not a second hard-coded list. The legacy `ENTRY_ROUTER.md` declaration keeps
  working. The exemption never removes the bound; it replaces the 400-line runtime
  denial with a declared ceiling.
- [ ] The ceiling is the optional `routerFileLinesCeiling` key of
  `.meridian/context-size.json` (version 1, default 1000 lines). A router file
  above it is still denied, with a message that says to shrink the file and never
  to read it in ranges; `LANGUAGE_POLICY.md` keeps its unconditional exemption.
- [ ] `meridian context size` reports each router file above the ceiling, and a
  role whose startup read set exceeds its byte ceiling, as a failure; `meridian
  audit` reports the same condition as a FAIL row, from the same computation.
- [ ] The denial message says to add or raise `` `Read-guard threshold` `` in
  `docs/EXECUTION_EVIDENCE_PROFILE.md`, and the threshold default stays 400.
- [ ] The queue briefing derives Governed in-progress and ready-for-review tasks
  from task records plus registered worktrees, as the console does
  (`scripts/console_workflow.py`); queue rows are used only for `QUEUED` and terminal
  rows. Lean output is unchanged except that `[/]` is no longer required to report
  an active task.
- [ ] A branch created under the old rule that still carries a queue status edit is
  reported the same way (no double count, no error).
- [ ] Tests cover: the active task found from a task worktree with the queue row
  still `[ ]`/`QUEUED`; no active task in the primary checkout; `PROJECT_WORKFLOW.md`
  above the threshold and below the ceiling readable; a router file above the
  ceiling denied with the shrink message; a custom ceiling; an unrelated large
  file still denied; `context size` and `audit` failures for an oversized router
  file; the new message; and the briefing for Governed and Lean.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; hook copies installed
  into projects follow the existing managed-hook update path.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `hooks/read-guard.sh` | Active-task lookup (around the queue `awk`), exemptions, message. |
| `scripts/codex_read_guard.py` | Codex read-guard equivalent. |
| `hooks/queue-briefing.sh` | Status counts. |
| `scripts/console_workflow.py` | Existing derivation of effective state to reuse. |
| `scripts/meridian.py` | Task identity and worktree resolution; `context size` read set. |
| `tests/` | Hook tests. |

## Technical Context

- The read-guard capability text (`read-guard` v1 in `CONTEXT_BUDGET_POLICY.md`) is
  corrected by task 146; this task changes behavior only.
- Prefer one `meridian` subcommand or flag that hooks call over parsing Git state in
  shell.
- Reading a mandated router file in ranges costs the same bytes in more calls, so
  the runtime denial saved nothing; the bound moves to a declared, checkable
  ceiling. The structural fix for an oversized `PROJECT_WORKFLOW.md` is removing
  restated framework rules (tasks 144 and 145), not a larger ceiling.
- The context-size configuration parser rejects unknown keys today; adding
  `routerFileLinesCeiling` keeps version 1 and is documented in
  `docs/CONTEXT_BUDGET_POLICY.md` next to `fileBytesThreshold`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the threshold default, the console, `integrate stage`, capability text,
and the size of any project file.

## Dependencies

- **Depends on**: —
- **Blocks**: 145
