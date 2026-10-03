# Task 130 — Make task creation follow the project's task-identity mode

> **ID**: `130`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task-identity option review, 2026-10-03

## Objective

An agent that creates a task today assigns the next numeric ID by scanning
`tasks/` and writes `tasks/NNN-kebab-title.md` (the `/meridian-task` command; in
Governed SDD, "assign a stable `TASK-NNN` ID"). It never reads
`.meridian/task-identity.json`. In a `milestone` project such an ID is rejected
as a new non-matching task, so `meridian worktree prepare` would fail when the
task starts, and the project's choice would be ignored where it matters. Make
task creation follow the declared mode, and give the agent a deterministic way
to obtain the next valid ID instead of counting by hand.

## Acceptance Criteria

- [x] A read-only command, for example `meridian task identity next --milestone
  <N> --workstream <W> --format json`, returns the next canonical ID for a
  `milestone` project: the highest ordinal already used for that milestone and
  workstream across the project's task and queue authorities, plus one,
  formatted as `M<N>-<W>-<ordinal>`.
- [x] The command refuses, without writing anything, in these cases: the project
  is `opaque`; the milestone or workstream does not satisfy the grammar; the
  ordinal would exceed `999`; or the authorities are ambiguous or contradictory
  (it fails closed, as the resolver does).
- [x] The command counts legacy-opaque IDs and structured IDs that merely look
  similar correctly: only IDs that match the same milestone and workstream raise
  the ordinal, and an ID in another milestone or workstream never does.
- [x] The returned ID is validated through the same resolver as
  `meridian task identity check`, and the JSON includes the derived task file
  name and path, so the agent does not rebuild them.
- [x] `/meridian-task` reads the declaration first. In `opaque` (including no
  file) its behavior, ID assignment, and file naming are unchanged. In
  `milestone` it asks for the milestone and workstream, calls the command, shows
  the proposed ID for confirmation, and creates `<ID>.md` in the project's task
  root, adding the queue row with the canonical ID and a link to that file.
- [x] The Governed SDD guidance that tells an agent to assign a task ID (the
  `/meridian-task` Governed branch and the tech-designer task-creation wording
  in the Governed templates) points to the same rule. Template wording changes
  are additive and follow the capability-marker and migration rules; if they
  cannot be done within this task, the command-side change ships and the
  decision is recorded in the handoff.
- [x] The agent never invents an ordinal: where the command is unavailable or
  fails, the instruction is to stop and report, not to guess.
- [x] Neutral across workflows: the command and the `/meridian-task` behavior
  work for Lean Delivery and Governed SDD alike.
- [x] Tests cover: next ordinal in an empty and a populated milestone; legacy
  IDs ignored; other milestones and workstreams ignored; `opaque` refused;
  invalid grammar refused; ordinal overflow; ambiguity failing closed; JSON
  shape and exit codes; and that nothing is written.
- [x] A recorded rehearsal on a scratch copy of a project's task records (as in
  the earlier Palimpsest rehearsal, not touching the real project) shows the
  proposed ID for an existing and a new milestone.
- [x] One changelog fragment is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Completion

The command-side implementation, task-creation command, and both governed
skills are complete. Updating the managed Governed operator-prompt template is
intentionally deferred: it requires a template-changing release packet with a
new capability marker and migration, which is outside this task's CLI-focused
release scope. The handoff records this decision for the follow-up release
task.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Task-identity resolver, `task identity` subcommands, and the grammar. |
| `commands/meridian-task.md` | Task-creation command to make identity-aware. |
| `skills/meridian-governed-sdd*/SKILL.md` | Governed guidance that assigns task IDs. |
| `templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md` | Tech-designer task-creation wording, additive change only. |
| `tests/test_meridian_cli.py` | Identity and task command tests. |

## Technical Context

- `meridian task identity check <ID> --format json` already returns the
  canonical ID, kind (`structured`, `legacy-opaque`, `opaque`), branch name, and
  derived handoff path; reuse its resolver rather than parsing the grammar a
  second time.
- The grammar is `M<milestone>-<WORKSTREAM>-<ordinal>` with a milestone that has
  no leading zero and a three-digit ordinal (`001`–`999`). A recurring task
  with no ordinal (for example `M38-VERIFY`) is not valid for new tasks; the
  recommended form is `M38-VERIFY-001`.
- Project locations (queue and task roots) come from the project location
  resolver; do not hard-code `tasks/`.
- Depends on task 129 only for the project to have a declaration to read; the
  command itself works for any project that already has the file.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the grammar, resolver, or schema; renaming existing tasks; choosing the
mode (task 129); generating specifications or ADRs per milestone; and writing to
any existing project.

## Dependencies

- **Depends on**: 129
- **Blocks**: none
