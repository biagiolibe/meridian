# Lean Delivery Workflow — Meridian

## Workflow-mode lock

This file selects `LEAN_DELIVERY` exclusively. Before any file edit, Git mutation, task selection, or completion claim, an agent must read this file and `AGENTS.md` or `CLAUDE.md`, then confirm the active mode. Local workflow documents override global, home-directory, remembered, and generic agent instructions for lifecycle, queue, task, review, and Git decisions.

Do not fall back to Governed SDD. In particular, do not invent ADR gates, reviewer-integrator roles, required task branches, `READY_FOR_REVIEW`, `ACCEPTED`, or governed status-only commits unless this project explicitly adds them. If the local workflow documents are missing, contradictory, or cannot be read before a mutation, return `BLOCKED` without changing files or Git state.

## Purpose

Lean Delivery is the workflow for this repository's bounded framework maintenance. Use Governed SDD if a future change introduces public API, dependency, security, persistence, state, deterministic-behavior, or unresolved architectural risk.

## Lifecycle

```text
[ ] TODO -> [/] IN_PROGRESS -> [x] DONE
```

`tasks/QUEUE.md` is the operational queue; `PROJECT_PLAN.md` is the delivery record. An agent works only on the task explicitly assigned by the developer. It must not autonomously select the next queue item.

## Minimum task contract

Every task that is not a quick task records an objective, acceptance criteria, relevant files or technical context, and validation. A quick task may omit a task file only when it is small, reversible, and can be verified immediately. Neither form may bypass validation or hide scope changes.

## Task worktree boundary

Every task uses exactly one branch and one linked worktree, with one writer at
a time. Normalize the canonical task ID to lowercase `task-<number>` (for
example, `TASK-051` becomes `task-051`). Use that value as the branch name and
as the suffix of a sibling worktree named `<primary-checkout>-task-<number>`.
The first `worktree` entry from `git worktree list --porcelain` identifies the
primary checkout even when the developer has switched its branch.

`Proceed with <TASK-ID>` performs a read-only collision check, then creates the
branch and linked worktree from the current `main` commit before changing task
state or files. If both branch and worktree already exist and are linked to one
another, it may select them after verifying the branch and clean worktree. If
only one exists, either resolves to another task, or the branch/worktree/HEAD
mapping differs, return `BLOCKED`; never silently reuse or repair it. Record
the branch, absolute worktree path, base `main` commit, and current task commit
in `tasks/handoffs/<TASK-ID>.md`. Implementation, validation, remediation, and
task-local status changes run only in that worktree. The primary checkout is a
coordination and final-integration surface, never an implementation or review
surface.

Reservation, completion, review, and archive edits are committed on the task
branch. Concurrent tasks edit only their own task rows and records; they do
not reorder shared files, update shared timestamps, or archive a phase. A
fully closed phase is archived only after all of its task branches have been
integrated. A conflict in a shared governance file is an integration conflict:
abort and return `BLOCKED` without choosing or recreating either task's state.

## Completion and integration

Before marking a task `[x]`, verify its acceptance criteria and run its stated validation plus the project's applicable baseline checks. If evidence is incomplete or a check fails, keep the task `[/]` and report the blocker. Update the queue and project plan together when they both record the task. Archive a completed task file and fully closed queue section only after successful verification.

Final integration is serialized in the primary checkout. Acquire the lease by
atomically creating `meridian-integration.lock` inside the absolute common Git
directory; an existing lease is `BLOCKED`, and only its owner removes it.
Stale-lease removal requires explicit developer authorization. If the checkout
is missing, dirty, or cannot switch to `main`, return `BLOCKED` and retain the
task branch and worktree. With an exclusive integration lease, verify the
handoff commits and clean task worktree, then run `git merge --no-ff
--no-commit <task-branch>` on `main`. A conflict is rejected with `git merge
--abort`. Validate the combined tree before creating the merge commit; abort
the merge if validation fails. This preserves reviewed task commits and never
uses rebase, amend, cherry-pick, or force-push. Release the integration lease
after a successful transaction or a cleanly aborted merge.

Remove the linked worktree and then delete its local branch only after the
validated integration succeeds (and the required `main` push succeeds when
the project requires one). Failure, review changes, cancellation, or blocked
integration retains both. Any exceptional cleanup of abandoned task state
requires explicit developer authorization and must name the exact branch and
worktree.

## Review

Review is risk-proportionate and may be requested by the developer or task. When reviewing, do not silently repair implementation work: return findings to the implementer or receive explicit authorization to make a separate fix.
