# Review Procedure

Use this procedure only for `Review <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=task-worktree-review-procedure v7 -->
## Mandatory task-worktree preflight

This is the first review action. Before reading the assigned task,
implementation files, or any implementation diff:

1. Start in the exact existing directory returned by `meridian worktree
   prepare` and run `meridian worktree check <TASK-ID> --project
   <primary-checkout> --format json`. A blocked result
   stops before any other read; never use host automatic worktree isolation.
2. Resolve the canonical completion-handoff location and read only that
   handoff. Obtain its task-worktree value (relative to the worktree root), task branch, current task
   commit, validated task commit, and validated base `main` commit. Confirm
   that the implementer session has stopped. A missing field, missing handoff,
   or active or unconfirmed implementer is `BLOCKED`.
3. Confirm that the successful check result and handoff name the same path,
   branch, HEAD, base, clean state, and repository. As an additional bounded
   check, run `git worktree list
   --porcelain` and locate exactly one registered entry whose normalized
   absolute path equals the handoff value resolved against the worktree root. The entry must record the handoff branch
   as `refs/heads/<task-branch>` and its `HEAD`. A full-SHA current task commit
   field must equal that `HEAD`. For a descriptive current task commit field,
   resolve it to the registered task branch `HEAD` and confirm its stated
   subject matches `git log -1 --format=%s <task-branch>`; treat that resolved
   value as `HEAD` for this comparison. Do not infer the task worktree from
   the session's initial current directory. If the path is absent, unregistered,
   duplicated, disagrees with the handoff, names a different commit, or has a
   mismatched subject, return `BLOCKED`.
4. Root additional read-only Git checks in the recorded path with `git -C
   <absolute-task-worktree> ...`. Verify its absolute top level, symbolic
   branch, `HEAD`, and empty `git status --short`; verify that the validated
   task and base commits exist; then verify that the base is an ancestor of
   the validated task commit and the validated task commit is an ancestor of
   current task `HEAD`. A missing commit, detached or mismatched branch,
   mismatched `HEAD`, dirty worktree, or failed ancestry check is `BLOCKED`.

Every failure above stops before substantive review and preserves the task,
branch, primary checkout, and linked worktree exactly as found. Never switch,
move, create, repair, or delete a checkout to make preflight pass. The bounded
`check` result is required and is never replaced by a branch name or the
worker's initial directory.

Only after every preflight check passes may the reviewer read the task, queue,
implementation files, or compute the implementation diff. When the session
started in the primary checkout, every such read uses the verified absolute
task-worktree path and every Git command uses `git -C
<absolute-task-worktree>`; the initial current directory is never treated as
the task checkout. Review never runs concurrently with an implementer.

After approval, commit the review and `ACCEPTED` state on the task branch,
then use the serialized integration transaction in `PROJECT_WORKFLOW.md`.
The validated task commit must remain an ancestor of task `HEAD`, with only
permitted lifecycle records in the intervening diff. Current `main` may have
advanced; reuse evidence, run the bounded gate, select full validation, or
return `BLOCKED` only through that transaction's deterministic decision.
Independent review, acceptance evidence, and forge gates remain mandatory.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=review-mode-boundary v1 -->
### Review-mode boundary

For `Review <TASK-ID>`, review is read-only until an explicit `APPROVE` verdict.
Do not edit source code, tests, manifests, implementation documentation, task
content, or queue records to remedy a finding. For `CHANGES_REQUESTED`, the
only allowed mutation is a local review-handoff commit: create or append
the declared review record (see `PROJECT_WORKFLOW.md`'s canonical locations)
using `docs/REVIEW_RECORD_TEMPLATE.md`, change
the task and queue status from `READY_FOR_REVIEW` to `IN_PROGRESS`, and commit
only those three artifacts. The record must contain every actionable finding
with priority and evidence; its unchecked findings are the implementer's
bounded remediation scope. Do not push this commit. Only after `APPROVE` and
the required ancestry check may the reviewer append the approval evidence to
the review record, make the two `ACCEPTED` status edits, and commit those three
artifacts with the required reviewer-integrator author override.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=implementer-reviewer-handoff v3 -->
## Implementer-to-reviewer handoff

After validation, create the task commit and push the task branch once for each
review attempt. The completion handoff must record the branch name,
linked-worktree value (relative to the worktree root, never an absolute path), implementation and current task commits,
validated task and base `main` commits, successful validation evidence, and
declared integration surface. Stop the implementer and leave the registered
task worktree clean before starting the fresh reviewer session. This durable
handoff transfers sequential ownership of that worktree; implementation and
review never overlap.

For `Review: REQUIRED`, the reviewer must never push the task branch. On
`CHANGES_REQUESTED`, it commits only the review record and matching task/queue
transition to `IN_PROGRESS`; the implementer then resolves and pushes the next
review attempt. For `Review: NOT_REQUIRED`, the implementer records acceptance
after validation without creating a reviewer session. Owner acceptance is
status-only. Checkout selection, validation ancestry, integration, and cleanup
are governed by their current dedicated procedures, not by this handoff.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=reviewer-integrator-identity v1 -->
## Reviewer-integrator identity on a single-operator project

Both controls are mandatory and neither substitutes for the other:

- Review runs in a fresh agent session that did not write the code. Re-derive evidence from the actual diff and cited sources; do not trust the implementation report.
- Only for the `ACCEPTED` commit, use the project-scoped reviewer author override below, with the project's actual name and slug:

  ```bash
  git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
  ```

Keep the operator's normal committer identity. Do not change global or repository Git config. The override applies only to the `ACCEPTED` commit and can be verified with `git log --format='%an <%ae>'`.
<!-- MERIDIAN:END -->
