# Remediation Procedure

Use this procedure only for `Address review <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=task-worktree-remediation v3 -->
Remediation reuses the prepared task worktree only after the reviewer has
stopped. Start in the coordinator-supplied existing directory and run
`meridian worktree check <TASK-ID> --project <primary-checkout>
--format json` before reading the task or review record.
Verify the result against the durable handoff before writing. Never remediate
in the primary checkout, create a replacement worktree, or run concurrently
with a reviewer. A mismatch is `BLOCKED` and preserves the existing state.
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

<!-- MERIDIAN:BEGIN capability=phase-reads v1 -->
## Phase reads

Read each document when its phase begins, in the order listed. This changes
only when a document is read; no gate, acceptance criterion, or review rule is
waived by reading a document later.

- At start: this procedure, the entry-point router, the workflow document, and the language policy.
- At first production-source change: `docs/CODE_ORGANIZATION.md`.
- At first validation: `docs/EXECUTION_EVIDENCE_PROFILE.md`.
- At a finding that cannot be remediated: `docs/LIFECYCLE_ORCHESTRATION.md`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=bounded-context-readers v1 -->
## Bounded context readers

Read the task's cited ADRs and specification sections with `meridian context
authority <TASK-ID>`, and a single ADR with `meridian adr show <ADR-ID>`. Do
not open the whole ADR log or a whole specification to find them. Read the
queue only through the resolved queue briefing; do not open the whole queue.
Open a source document directly only when a bounded reader reports an entry
unresolved or its excerpt cannot verify an acceptance criterion, and record
that reason in the report.
<!-- MERIDIAN:END -->
