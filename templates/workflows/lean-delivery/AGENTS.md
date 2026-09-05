# [Project Name] — Agent Rules

Read `PROJECT_WORKFLOW.md` before acting. It locks this repository to
`LEAN_DELIVERY`; use its local lifecycle rather than global, home-directory,
remembered, or generic Meridian/Claude/Codex instructions. If local workflow
documents cannot be read or conflict, return `BLOCKED` before mutating files or
Git state.

Read `LANGUAGE_POLICY.md` before responding or writing. Use its persisted
conversation language and write every repository artifact in English.

Work only on the task explicitly assigned by the developer. Before changing
code, read the task or quick-task description, its relevant context, and `git
status --short`; state a short plan. Do not choose a queue item autonomously.
If unrelated uncommitted changes prevent safe work, do not modify, stage,
discard, or commit them; report the conflict and stop.

## Delivery rules

- Keep the task scope bounded. Record a newly discovered requirement as a new
  task rather than silently widening the current one.
- Run the task validation and applicable project baseline checks. Do not mark a
  task `[x]`, archive it, or claim completion if required evidence is missing or
  validation fails.
- After successful verification, update the matching queue and project-plan
  records, then archive the completed task file or a fully closed queue section
  when applicable.
- Follow local project Git conventions. Lean Delivery does not imply a required
  branch, push, reviewer identity, or integration procedure.
- A requested review is read-only unless the developer separately authorizes a
  fix. Report actionable findings; do not silently correct implementation code
  during review.

## Command triggers

- `Proceed with <TASK-ID>` — implement only that task using Lean Delivery.
- `Review <TASK-ID>` — perform a read-only, risk-proportionate review of that
  task and report findings or approval.
