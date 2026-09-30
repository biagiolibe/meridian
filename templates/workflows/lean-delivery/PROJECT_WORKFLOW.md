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

<!-- MERIDIAN:BEGIN capability=task-identity-policy v1 -->
## Task identity

`.meridian/task-identity.json` is the sole optional project declaration for
task-identity policy. Its absence selects backwards-compatible `opaque` mode;
an explicit version-1 declaration may select `opaque` or `milestone` mode.
Meridian resolves task IDs through this declaration and the canonical task and
queue authorities. Workflow mode, host configuration, and identifier spelling
do not provide a second identity policy or imply task semantics.
<!-- MERIDIAN:END -->

## Task worktree boundary

<!-- MERIDIAN:BEGIN capability=codex-worktree-access v2 -->
Every task uses exactly one branch and one linked worktree, with one writer at
a time. Normalize the canonical task ID to lowercase `task-<number>` and use
it as the branch name. Derive the worktree path with `meridian worktree path
<task-id> --project <primary-checkout> --worktree-root
<selected-root>`. The layout is
`<root>/<remote-host>/<owner>/<repository>/<canonical-task-id>`; a repository
without a usable remote uses a deterministic local name plus a canonical
Git-common-directory hash. Unsafe, ambiguous, colliding, or mismatched paths
are `BLOCKED`. Existing legacy worktrees remain discoverable and are never
moved or deleted automatically. The first `git worktree list --porcelain`
entry identifies the primary checkout.

Before creating or editing a task worktree, run `meridian codex doctor` for
the selected root. Static configuration is not proof of effective host access;
resolve `approval-required` explicitly and treat `blocked` as `BLOCKED`.

If `meridian codex configure --check` reports `repair-required`, the effective
profile is identical and only Meridian's ownership markers were damaged, for
example by a Codex app rewrite. Review the printed diff and run `--apply` only
after explicit confirmation. A `BLOCKED` result names the diverging fields and
requires manual reconciliation. Repair never proves that a running session
loaded the profile; start a fresh session and probe it.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=bounded-worktree-lifecycle v2 -->
`Proceed with <TASK-ID>` runs `meridian worktree prepare <task-id> --project
<primary-checkout> --worktree-root <selected-root> --format json` before
starting a worker. The coordinator passes the returned branch and absolute
path as durable launch inputs and does not use a host facility that creates a
second checkout. The worker starts in that exact directory and, before any task
read or write, runs `meridian worktree check <task-id> --project
<primary-checkout> --worktree-root <selected-root> --format json`. Any path,
branch, HEAD, root, state, or cleanliness mismatch is `BLOCKED`.
Absolute paths are runtime launch inputs only. A handoff or other tracked
record that names the worktree uses the `handoff_worktree` value returned by
`meridian worktree prepare`, the path relative to the worktree root, never an
absolute path.
<!-- MERIDIAN:END -->

Reservation, completion, review, and archive edits are committed on the task
branch. Concurrent tasks edit only their own task rows and records; they do
not reorder shared files, update shared timestamps, or archive a phase. A
fully closed phase is archived only after all of its task branches have been
integrated. A conflict in a shared governance file is an integration conflict:
abort and return `BLOCKED` without choosing or recreating either task's state.

## Completion and integration

<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->
Classify the changed surface before validation. Documentation-only changes may
skip unrelated build, test, or lint commands when the task does not require
them, and the completion evidence records that skip. Source, build, runtime,
or CI changes run every task-required check plus the applicable project
baseline. Validation scope never weakens an explicit acceptance criterion.
<!-- MERIDIAN:END -->

Before marking a task `[x]`, verify its acceptance criteria and run its stated
validation plus the project's applicable baseline checks. The handoff records
the validated task commit, validated base `main` commit, exact commands and
successful results, whether full combined-tree validation is required, and the
task's declared files, dependencies, and behavioral surfaces. If evidence is
incomplete or a check fails, keep the task `[/]` and report the blocker. Update
the queue and project plan together when they both record the task. Archive a
completed task file and fully closed queue section only after successful
verification.

Final integration uses `meridian worktree integrate stage` with accepted JSON
handoff evidence. The command owns the lease and prescribed no-commit merge and
returns the deterministic validation decision and candidate tree. Run the
selected validation separately in the ordinary sandbox, bind its JSON evidence
to that tree, then use `integrate finalize`; use `integrate abort` after a
failed gate. Lifecycle commands never execute validation or project code.

Project integration smoke command: `none`.

After any required `main` push, use `meridian worktree cleanup`; exceptional,
forced, abandoned-state, or stale-lease cleanup remains outside this surface.

## Review

Review is risk-proportionate and may be requested by the developer or task.
When reviewing, do not silently repair implementation work: return findings to
the implementer or receive explicit authorization to make a separate fix.
