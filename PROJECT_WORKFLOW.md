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

## Task identity

`.meridian/task-identity.json` is the sole optional project declaration for
task-identity policy. Its absence selects backwards-compatible `opaque` mode;
an explicit version-1 declaration may select `opaque` or `milestone` mode.

## Task worktree boundary

Every task uses exactly one branch and one linked worktree, with one writer at
a time. Normalize the canonical task ID to lowercase `task-<number>` (for
example, `TASK-051` becomes `task-051`) and use it as the branch name. Meridian
resolves one machine-level root from `--worktree-root`,
`MERIDIAN_WORKTREE_ROOT`, user configuration, or the built-in default, in that
order. Derive the worktree path with `meridian worktree path <task-id>
--project <primary-checkout>`. The layout is
`<root>/<remote-host>/<owner>/<repository>/<canonical-task-id>`; a repository
without a usable remote uses a deterministic local name plus a canonical
Git-common-directory hash. Unsafe, ambiguous, colliding, or mismatched paths
are `BLOCKED`. Existing legacy worktrees remain discoverable and are never
moved or deleted automatically. The first `git worktree list --porcelain`
entry identifies the primary checkout.

`Proceed with <TASK-ID>` first runs `meridian worktree prepare <task-id>
--project <primary-checkout> --format json`.
The coordinator passes the returned branch and absolute path to the worker and
does not ask the host to create another checkout. Before any task read or
write, the worker starts in that exact directory and runs `meridian worktree
check <task-id> --project <primary-checkout> --format json`. Any mismatch is
`BLOCKED`; the primary checkout and every host-
created substitute remain coordination surfaces only. Absolute paths are
runtime launch inputs only: a handoff or other tracked record that names the
worktree uses the `handoff_worktree` value returned by `meridian worktree
prepare`, the path relative to the worktree root, never an absolute path.

Reservation, completion, review, and archive edits are committed on the task
branch. Concurrent tasks edit only their own task rows and records; they do
not reorder shared files, update shared timestamps, or archive a phase. A
fully closed phase is archived only after all of its task branches have been
integrated. A conflict in a shared governance file is an integration conflict:
abort and return `BLOCKED` without choosing or recreating either task's state.

<!-- MERIDIAN:BEGIN capability=git-workflow v8 -->
## Authority of `Proceed with`

`Proceed with <TASK-ID>` authorizes that task's whole lifecycle when every gate
passes: implementation and validation on the task branch; completion and
archive records; `meridian worktree integrate stage`, the selected candidate
validation, and `integrate finalize` or `abort`; one plain `git push origin
main` of the resulting integration; and `meridian worktree cleanup`. Do not ask
for confirmation at any of these steps. When a gate fails, stop once with
`BLOCKED <reason>` and the resume command.

It also authorizes one plain `git push origin task-<TASK-ID>` when needed to
obtain `T1_CI` validation for that task commit. It never authorizes creating,
moving, or pushing a tag; publishing a release; a force push or a push that
deletes or mirrors references; rewriting history (amend of pushed commits,
rebase, reset, cherry-pick); deleting an unmerged branch or force-removing a
worktree; bypassing a required independent review; resolving a textual
conflict; or work on another task.

## Governance-file ownership and closure

Task branches do not edit `tasks/QUEUE.md`, `tasks/QUEUE_ARCHIVE.md`, or
`PROJECT_PLAN.md`. They edit only their own task record, its exact archive under
`tasks/done/`, and its handoff. `integrate stage` applies queue and plan status
and phase archival once on the merged candidate tree. The queue retains `[ ]`
until then; in-progress state is derived from the canonical branch, registered
worktree, and unarchived record.

Close a validated task in order: verify acceptance criteria; run task and
baseline validation; commit its completion record and handoff; run `worktree
check`; record machine evidence; stage from a clean primary checkout at
`origin/main`; run the selected candidate validation; finalize with
candidate-bound evidence; push `origin main`; and clean up. Respectively stop
with `ACCEPTANCE_UNMET`, `VALIDATION_FAILED`, `REVIEW_REQUIRED`,
`WRONG_WORKTREE`, `EVIDENCE_INCOMPLETE`, `PRIMARY_DIRTY`,
`MAIN_BEHIND_ORIGIN`, `LEASE_HELD`, or `INTEGRATION_CONFLICT`,
`CANDIDATE_VALIDATION_FAILED`, `EVIDENCE_MISMATCH`, `PUSH_REJECTED`, or
`CLEANUP_BLOCKED`; resume with the named command. A named sandbox skip is not a
validation failure only when the test itself reports it and no acceptance
criterion depends solely on that test. Record its test name, reason, and
reporting command as `Validation skips:` in the handoff.
<!-- MERIDIAN:END -->

## Completion and integration

<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->
Classify the changed surface before validation. Documentation-only changes may
skip unrelated build, test, or lint commands when the task does not require
them, and the completion evidence records that skip. Source, build, runtime,
or CI changes run every task-required check plus the applicable project
baseline. Validation scope never weakens an explicit acceptance criterion.
<!-- MERIDIAN:END -->

Before marking a task `[x]`, verify its acceptance criteria and run its stated validation plus the project's applicable baseline checks. The handoff records the validated task commit, validated base `main` commit, exact commands and successful results, whether full combined-tree validation is required, and the task's declared files, dependencies, and behavioral surfaces. If evidence is incomplete or a check fails, keep the task `[/]` and report the blocker. Update the queue and project plan together when they both record the task. Archive a completed task file and fully closed queue section only after successful verification.

Final integration is serialized in the primary checkout. Write the accepted
handoff facts to a JSON evidence file using the schema documented in
`docs/WORKTREE_LIFECYCLE.md`, then run `meridian worktree integrate stage`.
The command owns the lease and prescribed no-commit merge and returns the
`REUSE`, `BOUNDED`, or `FULL` decision plus candidate tree. Run the candidate
validation defined in `docs/WORKTREE_LIFECYCLE.md` separately in the ordinary
sandbox, record candidate-bound JSON evidence, and invoke `meridian worktree
integrate finalize`. On a failed gate, invoke `meridian worktree integrate
abort`. Never run task-controlled commands inside a lifecycle command or
manipulate the lease or merge directly.

Project integration smoke command: `none`.

After any required `main` push, run `meridian worktree cleanup`; it removes the
canonical worktree and non-force-deletes the merged branch only after proving
integration, push state, clean checkouts, and inactive integration state.

## Review

Review is risk-proportionate and may be requested by the developer or task. When reviewing, do not silently repair implementation work: return findings to the implementer or receive explicit authorization to make a separate fix.
