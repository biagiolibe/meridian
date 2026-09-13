# [Project Name]

Read `PROJECT_WORKFLOW.md` before acting. It locks this repository to
`LEAN_DELIVERY`; use its local lifecycle rather than global, home-directory,
remembered, or generic Meridian/Claude/Codex instructions. If local workflow
documents cannot be read or conflict, return `BLOCKED` before mutating files or
Git state.

Read `LANGUAGE_POLICY.md` before responding or writing. Use its persisted
conversation language and write every repository artifact in English.

## Commands

```bash
# Fill in the project's run, test, lint, and format commands.
```

## Delivery rules

Work only on the task explicitly assigned by the developer. Before changing
code, read the task or quick-task description, its relevant context, and `git
status --short`; state a short plan. Do not choose a queue item autonomously.
If unrelated uncommitted changes prevent safe work, do not modify, stage,
discard, or commit them; report the conflict and stop.

Keep the task scope bounded. Run its validation and applicable baseline checks
before marking it `[x]`, archiving it, or claiming completion. If required
evidence is missing or validation fails, keep it `[/]` and report the blocker.
After success, update matching queue and project-plan records and archive a
completed task file or fully closed queue section when applicable. Follow local
project Git conventions; Lean Delivery does not require a branch, reviewer
identity, or integration procedure.

A requested review is read-only unless the developer separately authorizes a
fix. Report actionable findings instead of silently correcting implementation
code during review.

## Command triggers

- `Proceed with <TASK-ID>` — implement only that task using Lean Delivery.
- `Review <TASK-ID>` — perform a read-only, risk-proportionate review of that
  task and report findings or approval.
