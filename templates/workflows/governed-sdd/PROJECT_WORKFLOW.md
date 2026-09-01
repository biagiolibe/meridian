# Governed SDD Workflow — [Project Name]

## Document precedence

When documents conflict, the first applicable document wins:

1. `AGENTS.md` / `CLAUDE.md` — operating rules for the active agent.
2. `docs/ARCHITECTURE_DECISIONS.md` — accepted architecture decisions.
3. Project and milestone specifications.
4. `tasks/QUEUE.md` and atomic task files — execution scope, dependencies, review policy, and validation.
5. Design/background documents.

Implementation never resolves a conflict silently: update the lower-precedence document or record an ADR.

## Task lifecycle

```text
Review: REQUIRED
QUEUED -> IN_PROGRESS -> READY_FOR_REVIEW -> ACCEPTED

Review: NOT_REQUIRED
QUEUED -> IN_PROGRESS -> ACCEPTED
```

Only `ACCEPTED` tasks satisfy dependencies.

## Execution assets

- `docs/CONTEXT_BUDGET_POLICY.md` defines task-first context loading, reasoning profiles, and concise communication.
- `tasks/TASK_BLUEPRINT.md` defines the canonical atomic-task shape.
- `docs/COMPLETION_REPORT_TEMPLATE.md` defines the implementation and review handoff.

For a task or review, start with `AGENTS.md` or `CLAUDE.md`, then read only the assigned task and sources it cites. These assets are operational guidance and do not supersede the precedence order above.

## Roles

- Tech designer: defines ADRs, specifications, task scope, dependencies, and review policy. Does not implement feature code unless explicitly assigned.
- Implementer: works on exactly one task in a dedicated branch/worktree, validates it, commits it, and updates the task state according to its review policy.
- Reviewer-integrator: independently reviews `READY_FOR_REVIEW` tasks. After `APPROVE`, it records `ACCEPTED`, pushes the status-only commit, and merges the existing PR when repository gates allow it.

## Review policy

Every task declares `Review: REQUIRED` or `Review: NOT_REQUIRED`. The latter is restricted to low-risk documentation, mechanical configuration, simple scaffolding, or focused tests that add no production behavior. It is prohibited for public APIs, dependencies, security, state transitions, deterministic rules, persistence/history, or unresolved design questions.

## Git workflow

- One writer per worktree.
- Use one branch per task, named from the normalized task ID without a provider prefix (for example, `task-012`).
- The implementer may not merge, rebase, amend, or force-push unless explicitly authorized.
- A reviewer-integrator merges only after `APPROVE`, required checks, and all forge gates are satisfied.
- A forge approval cannot be supplied by the same identity that authored the PR. If an external approval is required but unavailable, leave the PR open and report `BLOCKED`.

## Execution discipline

Apply `docs/CONTEXT_BUDGET_POLICY.md`. The review-policy restrictions above remain authoritative; use parallel agents only when their scopes and worktrees are independent.
