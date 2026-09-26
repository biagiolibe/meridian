# Pull Request Policy

Task context loading, reasoning selection, task shape, and completion handoffs are governed by `docs/CONTEXT_BUDGET_POLICY.md`, `tasks/TASK_BLUEPRINT.md`, and `docs/COMPLETION_REPORT_TEMPLATE.md`; this document defines review and forge integration only.

<!-- MERIDIAN:BEGIN capability=task-worktree-integration v1 -->
For `Review: REQUIRED`, the implementer pushes the task branch once after
validation for each review attempt and records its deterministic branch,
absolute dedicated-worktree path, implementation commit, base `main` commit,
and current task commit in the completion handoff. The reviewer-integrator
uses that same task worktree in a fresh session after the implementer stops. It
verifies the registered mapping and cleanliness, never switches the primary
checkout to the task branch, and never pushes the task branch.

On `CHANGES_REQUESTED`, the reviewer creates or appends
`tasks/reviews/<TASK-ID>.md` following `docs/REVIEW_RECORD_TEMPLATE.md`, then
updates only the task and queue status to `IN_PROGRESS`. Commit exactly those
review-handoff artifacts locally; do not push them. The implementer uses that
record to resolve every unchecked finding, returns both statuses to
`READY_FOR_REVIEW`, and makes the next permitted task-branch push. This
preserves the evidence across chats without granting the reviewer authority to
repair implementation artifacts.

Before accepting, verify:

```bash
git merge-base --is-ancestor <recorded-base-main> <current-task-commit>
```

Current `main` need not be an ancestor of the branch. If the recorded-base
check fails, do not mark the task `ACCEPTED`; return `BLOCKED`. Do not fetch,
rebase, amend, cherry-pick, or force-push as recovery. After `APPROVE`, append
the verdict and evidence to the review record and create only the local
review-and-status `ACCEPTED` commit.

Final integration is serialized in the primary checkout under one exclusive
integration lease, acquired by atomically creating
`meridian-integration.lock` in the absolute common Git directory. An existing
lease is `BLOCKED`; only its owner removes it, and stale-lease removal requires
explicit developer authorization. If the primary checkout is missing, dirty,
cannot switch to `main`, or another
integration owns the lease, return `BLOCKED` and preserve task state. Run `git
merge --no-ff --no-commit <task-branch>`. Reject a conflict with `git merge
--abort`; never resolve it by choosing one task's governance state. Run the
applicable validation against the combined tree, abort on failure, and only
then create the merge commit and push `main` exactly once. Remove the linked
worktree and then the local branch only after success. Release the lease after
success or a clean abort.

For `Review: NOT_REQUIRED`, the implementer performs the same `ACCEPTED` status
commit and integration transaction after validation. Owner acceptance remains
an explicit exception: it updates only statuses and does not automatically
integrate the branch.

Task reservation, completion, review, and archive mutations stay on the task
branch. Concurrent tasks change only their own task row and records. They do
not reorder shared governance files, change shared timestamps, or archive a
phase; phase archival waits until all rows are integrated. Any shared-file
conflict blocks integration with both branches intact.
<!-- MERIDIAN:END -->

## Validation evidence for review

<!-- MERIDIAN:BEGIN capability=ci-verified-validation v1 -->
A reviewer never accepts a bare "tests passed" claim as evidence — that
self-report is exactly what an independent review exists to verify, not to
repeat back. Two paths, in order:

1. **CI configured and has a completed run for the exact task-branch
   commit:** use that run's status as validation evidence. A CI run is an
   independent, tamper-evident execution against an immutable commit; do not
   re-run the same checks locally when a passing run for that exact SHA
   already exists — that would be pure duplication of an equally trustworthy
   result. If CI ran but does not cover the task's actual validation
   surface, treat it as partial and fall through to (2) for the rest.
2. **No CI, or none for that commit:** the implementer's local run is
   self-reported and is not, by itself, independent evidence. Perform your
   own validation, scoped to the diff's actual surface per
   `docs/CONTEXT_BUDGET_POLICY.md` — not the implementer's full historical
   run, and not zero verification. This is the difference between "re-derive
   evidence" (required) and "trust the implementation report" (prohibited)
   from `docs/CODE_REVIEW_PROMPT.md`.

Either path requires the completion report to name exact commands and exit
status, or the CI check run, per `docs/COMPLETION_REPORT_TEMPLATE.md` — a
claim that cannot be checked is not evidence.
<!-- MERIDIAN:END -->

## Remote task-branch cleanup

A remote task branch may intentionally lack a local review-and-status `ACCEPTED` commit: its acceptance evidence is published through the subsequent `main` push. Once `main` contains and has pushed the accepted work, local integration is complete and the local task branch may be deleted.

Remote task-branch deletion is optional and non-blocking. After successful `main` integration, an agent may attempt `git push origin --delete <task-branch>` without force. If the remote deletion fails or the branch is already absent, report a warning only. Never block accepted integration, fetch/rebase, or force-delete solely to clean up a remote task branch.

If the forge requires an approving review, a distinct authorized reviewer identity is required. The PR author cannot satisfy that gate.

## Reviewer-integrator identity on a single-operator project

Review must run in a fresh agent session that did not write the code and must re-derive evidence from the actual diff and cited sources. For the `ACCEPTED` commit only, use the project-scoped reviewer-specific author override, while retaining the operator's normal committer identity:

```bash
git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
```

Do not change global or repository Git config. Verify the override with `git log --format='%an <%ae>'`.
