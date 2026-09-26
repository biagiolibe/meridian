# Lifecycle Procedure

Use this procedure only for `Run lifecycle <TASK-ID>` or `Accept <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=lifecycle-orchestration v3 -->
### Autonomous lifecycle orchestration

For `Run lifecycle <TASK-ID>`, follow `docs/LIFECYCLE_ORCHESTRATION.md`
exactly. Act only as the coordinator: start an implementer session for
`Proceed with <TASK-ID>`, then a fresh, independent reviewer session for
`Review <TASK-ID>`. On `CHANGES_REQUESTED`, start a new implementer session for
`Address review <TASK-ID>` and then a new independent reviewer session. Do not
give a reviewer the implementer's chat context or let one session perform both
roles. Continue only on durable state and evidence, and stop at the document's
retry limit or any listed blocker.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=task-worktree-lifecycle v1 -->
The implementer and reviewer sessions use the same dedicated task worktree
sequentially; neither uses the primary checkout. Final integration uses the
serialized, combined-tree-validated merge transaction defined in
`docs/LIFECYCLE_ORCHESTRATION.md`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=rejected-attempt-restart v3 -->
For a finding explicitly not remediable without new or amended authority or
scope, return `BLOCKED`; do not restart through remediation. Only explicit
developer authorization may use the rejected-attempt restart procedure in
`docs/LIFECYCLE_ORCHESTRATION.md`, which requires accepted design authority,
preserved rejected evidence, and fresh implementation and review.
For `Restart rejected <TASK-ID>`, act only as a coordinator: complete the
preflight and atomic ref transaction defined in `docs/LIFECYCLE_ORCHESTRATION.md`,
write the governance-only restart handoff, then stop and direct a fresh
`Proceed with <TASK-ID>`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=owner-acceptance-workflow v1 -->
## Owner-acceptance workflow

When the developer says `Accept <TASK-ID>` after personally reviewing a `Review: REQUIRED` task, treat it as explicit authorization to skip the agent review and perform only the acceptance-state handoff. Confirm that the task and its canonical queue row are both `READY_FOR_REVIEW`; do not re-review the implementation, rerun validation, change source code, or merge the branch.

Update exactly the task `Status` and its canonical queue row to `ACCEPTED`, and commit only those two edits as `docs: accept <TASK-ID>` on the existing local task branch. Report the commit. If the required state records are missing or inconsistent, stop and report `BLOCKED`.
<!-- MERIDIAN:END -->
