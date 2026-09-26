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

## Task worktree boundary

Every task uses exactly one branch and one linked worktree, with one writer at
a time. Normalize the canonical task ID to lowercase `task-<number>` (for
example, `TASK-012` becomes `task-012`). Use that value as the branch name and
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

Before marking a task `[x]`, verify its acceptance criteria and run its stated
validation plus the project's applicable baseline checks. The handoff records
the validated task commit, validated base `main` commit, exact commands and
successful results, whether full combined-tree validation is required, and the
task's declared files, dependencies, and behavioral surfaces. If evidence is
incomplete or a check fails, keep the task `[/]` and report the blocker. Update
the queue and project plan together when they both record the task. Archive a
completed task file and fully closed queue section only after successful
verification.

Final integration is serialized in the primary checkout. Acquire the lease by
atomically creating `meridian-integration.lock` inside the absolute common Git
directory; an existing lease is `BLOCKED`, and only its owner removes it.
Stale-lease removal requires explicit developer authorization. If the checkout
is missing, dirty, or cannot switch to `main`, return `BLOCKED` and retain the
task branch and worktree. With an exclusive integration lease, verify the
handoff commits and clean task worktree. Reject missing evidence, a validated
base that is not an ancestor of the validated task commit, or a task HEAD whose
diff from that commit changes anything except the permitted completion status,
queue, plan, archive, or handoff records. The validated task commit must be an
ancestor of task HEAD; any task-relevant tree change makes the evidence stale.

If current `main` equals the validated base, reuse the task evidence. If it has
advanced, compare `git diff --name-only <validated-base>..main` with the
handoff's declared files, dependencies, generated or configuration inputs,
schemas, shared-governance records, and behavioral surfaces. Equal or nested
paths, a shared dependency/input/schema/configuration identity, or a shared
behavioral surface are material interactions and require full combined-tree
validation. An incomplete declaration or comparison is `BLOCKED`; a clean Git
merge or disjoint filenames alone never establish independence. Record an
independent comparison before using the bounded gate. Also use full validation
when the task explicitly requires it. Stale task evidence is rejected rather
than refreshed during integration.

Run `git merge --no-ff --no-commit <task-branch>` on `main` and reject a
conflict with `git merge --abort`. Every conflict-free candidate runs the
bounded gate: `git diff --check` plus the project smoke command declared below
when it is not `none`. A missing smoke command does not expand the gate to the
complete baseline. Run the complete baseline only for the full-validation
cases above, or after a bounded-gate failure when broader diagnosis is needed;
a failed bounded or full gate still aborts the merge and cannot create a merge
commit. Release the lease after success or a clean abort, and record the
decision, comparison evidence, commands, and results. This preserves validated
task commits and never uses rebase, amend, cherry-pick, or force-push.

Project integration smoke command: `none`.

Remove the linked worktree and then delete its local branch only after the
validated integration succeeds (and the required `main` push succeeds when
the project requires one). Failure, review changes, cancellation, or blocked
integration retains both. Any exceptional cleanup of abandoned task state
requires explicit developer authorization and must name the exact branch and
worktree.

## Review

Review is risk-proportionate and may be requested by the developer or task.
When reviewing, do not silently repair implementation work: return findings to
the implementer or receive explicit authorization to make a separate fix.
