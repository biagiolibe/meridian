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

- Keep the task scope bounded. Record a newly discovered requirement as a new
  task rather than silently widening the current one.
- Run the task validation and applicable project baseline checks. Do not mark a
  task `[x]`, archive it, or claim completion if required evidence is missing or
  validation fails.
- After successful verification, update the matching queue and project-plan
  records, then archive the completed task file or a fully closed queue section
  when applicable.
- For `Proceed with <TASK-ID>`, create or select the deterministic task branch
  and linked worktree required by `PROJECT_WORKFLOW.md` before changing task
  state or files. Run implementation, validation, and task-local lifecycle
  edits only there; the primary checkout is reserved for coordination and
  final integration.
- Use one writer per task worktree. A review uses the same task worktree only
  after the implementer has stopped; it never switches the primary checkout to
  the task branch.
- A requested review is read-only unless the developer separately authorizes a
  fix. Report actionable findings; do not silently correct implementation code
  during review.

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

## Command triggers

- `Proceed with <TASK-ID>` — implement only that task using Lean Delivery.
- `Review <TASK-ID>` — perform a read-only, risk-proportionate review of that
  task and report findings or approval.
