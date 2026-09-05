# Lean Delivery Workflow — [Project Name]

## Workflow-mode lock

This file selects `LEAN_DELIVERY` exclusively. Before any file edit, Git
mutation, task selection, or completion claim, an agent must read this file and
`AGENTS.md` or `CLAUDE.md`, then confirm the active mode. Local workflow
documents override global, home-directory, remembered, and generic agent
instructions for lifecycle, queue, task, review, and Git decisions.

Do not fall back to Governed SDD. In particular, do not invent ADR gates,
reviewer-integrator roles, required task branches, `READY_FOR_REVIEW`,
`ACCEPTED`, or governed status-only commits unless this project explicitly adds
them. If the local workflow documents are missing, contradictory, or cannot be
read before a mutation, return `BLOCKED` without changing files or Git state.

## Purpose

Lean Delivery is a complete workflow for small projects, proof-of-concepts,
demos, experiments, and reversible low-risk changes. It optimizes for delivery
speed while keeping scope, verification, and progress visible. Use Governed SDD
when the change has public API, dependency, security, persistence, state,
deterministic-behavior, or unresolved architectural risk.

## Lifecycle

```text
[ ] TODO -> [/] IN_PROGRESS -> [x] DONE
```

`tasks/QUEUE.md` is the operational queue; `PROJECT_PLAN.md` is the product
backlog and delivery record. An agent works only on the task explicitly
assigned by the developer. It must not autonomously select the next queue item.

## Minimum task contract

Every task that is not a quick task records an objective, acceptance criteria,
relevant files or technical context, and validation. A quick task may omit a
task file only when it is small, reversible, and can be verified immediately.
Neither form may bypass validation or hide scope changes.

## Completion and Git

Before marking a task `[x]`, verify its acceptance criteria and run its stated
validation plus the project's applicable baseline checks. If evidence is
incomplete or a check fails, keep the task `[/]` and report the blocker. Update
the queue and project plan together when they both record the task. Archive a
completed task file and fully closed queue section only after successful
verification.

Use the project's documented Git conventions. Lean Delivery does not impose a
branch, reviewer, push, or author-identity policy; it must not silently relax a
project-specific one.

## Review

Review is risk-proportionate and may be requested by the developer or task.
When reviewing, do not silently repair implementation work: return findings to
the implementer or receive explicit authorization to make a separate fix.
