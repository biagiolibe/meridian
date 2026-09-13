# Review Procedure

Use this procedure only for `Review <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

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

<!-- MERIDIAN:BEGIN capability=implementer-reviewer-handoff v1 -->
## Implementer-to-reviewer handoff

After validation, create the task commit and push the task branch once for each
review attempt. The completion handoff must record the branch name,
implementation commit, and base `main` commit. Leave the primary checkout
clean and on the task branch; do not switch back to `main`.

The reviewer-integrator uses that same primary checkout in a fresh agent session that did not write the implementation. If the reviewer session starts on clean `main`, run `git switch <task-branch>`. If the branch is missing locally, or a dirty checkout prevents switching, return `BLOCKED` with the exact condition.

For `Review: REQUIRED`, the reviewer must never push the task branch. On
`CHANGES_REQUESTED`, it commits only the review record and matching task/queue
transition to `IN_PROGRESS`; the implementer then resolves and pushes the next
review attempt. Before accepting, run `git merge-base --is-ancestor main
<task-branch>`. If it fails, do not mark the task `ACCEPTED`; return `BLOCKED`
with no fetch, rebase, non-fast-forward merge, or force-push recovery. If it
passes, create the local review-and-status `ACCEPTED` commit, switch to `main`,
fast-forward merge the task branch, push `main` exactly once, and delete the
local task branch. For `Review: NOT_REQUIRED`, the implementer performs the
same acceptance commit and main integration after validation. Owner acceptance
is status-only and does not automatically integrate the branch.
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
