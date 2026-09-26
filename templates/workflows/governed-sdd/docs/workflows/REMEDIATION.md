# Remediation Procedure

Use this procedure only for `Address review <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=task-worktree-remediation v1 -->
Remediation reuses the registered dedicated task worktree only after the
reviewer has stopped. Verify its branch, path, current task commit, and clean
state against the durable handoff before writing. Never remediate in the
primary checkout, create a replacement worktree, or run concurrently with a
reviewer. A mismatch is `BLOCKED` and preserves the existing task state.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=review-remediation-record v2 -->
### Review-remediation workflow

For `Address review <TASK-ID>`, read the assigned task, its cited authority,
the current review record at the location `PROJECT_WORKFLOW.md` declares for
it, and `git status --short`. Confirm the
task and queue both say `IN_PROGRESS`, that the review record has unchecked
findings, and that its local review-handoff commit is present. Do not implement
new work, reinterpret a finding, or erase prior reviewer evidence. Resolve
every unchecked finding, mark each with implementation evidence in a new
attempt in the review record, rerun the task and baseline validation, and set
both task and queue status to `READY_FOR_REVIEW`. Commit the remediation and
updated review record, then push the task branch once for this next review
attempt. Report the review-record path, resolved findings, commit, and
validation. If a finding needs an authority or scope change, leave it
unchecked and return `BLOCKED`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=rejected-attempt-restart v3 -->
If a `CHANGES_REQUESTED` finding explicitly cannot be remediated because it
needs new or amended authority or scope, leave it unchecked and return
`BLOCKED` without ref or status mutation. Do not use remediation to restart it;
only explicit developer authorization may invoke the procedure in
`docs/LIFECYCLE_ORCHESTRATION.md`.
<!-- MERIDIAN:END -->
