# [Project Name]

Read `PROJECT_WORKFLOW.md` before acting. It defines the governed SDD lifecycle, review policy, roles, and Git workflow for this project.

`PROJECT_WORKFLOW.md` locks this repository to `GOVERNED_SDD`. Before any file
edit, Git mutation, task selection, or completion claim, confirm that mode from
the local file. Never use global, home-directory, remembered, or generic
Meridian/Claude/Codex instructions to select a lifecycle, task status, queue
format, branch procedure, or review action. Do not fall back to Lean Delivery:
checkbox statuses, moving tasks to `tasks/done/`, `PROJECT_PLAN.md` as a
canonical queue, autonomous task selection, and review-policy bypasses are
prohibited. If the local workflow cannot be read or conflicts with these rules,
return `BLOCKED` before making a mutation.

Read `LANGUAGE_POLICY.md` before responding or writing. It is a mandatory invariant: use its persisted conversation language even when a prompt uses another language, and write every repository artifact in English.

Follow `docs/CONTEXT_BUDGET_POLICY.md` and the project-owned `docs/EXECUTION_EVIDENCE_PROFILE.md` for task-first context loading, proportionate evidence/output handling, and reasoning selection. Use the assigned task as the navigation map, `docs/COMPLETION_REPORT_TEMPLATE.md` for the final handoff, `docs/REVIEW_RECORD_TEMPLATE.md` for a durable requested-changes handoff, and `docs/LIFECYCLE_ORCHESTRATION.md` for the autonomous lifecycle command.

## Commands

```bash
# Fill in run, test, lint, and format commands for this project.
```

## Project invariants

- Add domain- and stack-specific invariants here.
- Treat accepted ADRs and task acceptance criteria as binding.

## Code organization

Follow `docs/CODE_ORGANIZATION.md` for every production-source change: one owning module per responsibility, preserved dependency direction between layers, narrowest working visibility, and structural refactors kept out of behavior-change tasks. If a task needs a new ownership boundary or cannot fit the documented module structure without coupling responsibilities, stop and report the missing architectural decision instead of creating an opportunistic abstraction.

<!-- MERIDIAN:BEGIN capability=command-triggers v1 -->
## Command triggers

Treat these developer phrases as the complete authorization for the named workflow. Do not select a different task or act on an unassigned one.

- `Proceed with <TASK-ID>` — run the implementation workflow below for exactly that task.
- `Review <TASK-ID>` — act as an independent reviewer-integrator using `docs/CODE_REVIEW_PROMPT.md`, ideally in a fresh chat or Task-tool subagent.
- `Address review <TASK-ID>` — resolve exactly the outstanding findings in that task's review record.
- `Run lifecycle <TASK-ID>` — coordinate that task through independent implementation, review, remediation, and integration under `docs/LIFECYCLE_ORCHESTRATION.md`.
- `Accept <TASK-ID>` — run the owner-acceptance workflow below.
<!-- MERIDIAN:END -->

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

### Implementation workflow

1. Read the assigned task, every referenced higher-precedence specification/ADR, and `git status --short`. <!-- MERIDIAN:BEGIN capability=manual-verification-precondition v1 -->If the task declares `Manual verification: required`, confirm now — before any implementation — that you can produce that evidence (a running app, screenshot capability, or an available reviewer for it). If you cannot, return `BLOCKED` immediately instead of implementing first and discovering the gap later. When a deterministic test can serve as the change's primary acceptance evidence (for example, a geometry or layout assertion), treat manual or visual confirmation as a secondary check, not the only gate.<!-- MERIDIAN:END -->
2. Before code changes, ensure the worktree contains no unrelated uncommitted changes. If it does, do not stage, modify, discard, or commit those changes; report the exact conflict and stop unless the developer explicitly directs how to proceed.
3. Create and switch to a dedicated branch named after the normalized task ID, without a provider prefix (for example, `TASK-012` uses `task-012`). Only one task may write in this checkout at a time. If the branch already exists, inspect it and stop for direction rather than overwriting or rebasing it. Do not create or switch branches in a dirty checkout.
4. State a short plan, then implement only the assigned task and its explicit dependencies. Preserve architectural boundaries and all SDD scope limits.
5. Run the task's validation commands and the project baseline checks from the `## Commands` section, <!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->scoped to the diff's actual surface per `docs/CONTEXT_BUDGET_POLICY.md`'s validation-scope rule — skip a full build/test/lint suite for a documentation/policy-only change and state so explicitly.<!-- MERIDIAN:END --> Also skip a command that is inapplicable because the task has not yet established its required project artifact. Report every skipped command and why.
6. When every required validation passes, record completion according to the task's review policy: `READY_FOR_REVIEW` for `Review: REQUIRED`, `ACCEPTED` for `Review: NOT_REQUIRED`. Make no status change if any validation failed, a required manual check is incomplete, or acceptance criteria are not met.
7. Review the diff to confirm it contains only the assigned task and its required status updates. Create one atomic commit using Conventional Commit style and the task ID. Follow `docs/PULL_REQUEST_POLICY.md` for the branch push and hand-off.
8. Report the branch name, commit hash, changed files, acceptance-criteria evidence, validation results, and assumptions. If validation fails or scope is ambiguous, do not commit a partial implementation; report the blocker.

Never run two writing agents concurrently in the same worktree.

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

<!-- MERIDIAN:BEGIN capability=owner-acceptance-workflow v1 -->
## Owner-acceptance workflow

When the developer says `Accept <TASK-ID>` after personally reviewing a `Review: REQUIRED` task, treat it as explicit authorization to skip the agent review and perform only the acceptance-state handoff. Confirm that the task and its canonical queue row are both `READY_FOR_REVIEW`; do not re-review the implementation, rerun validation, change source code, or merge the branch.

Update exactly the task `Status` and its canonical queue row to `ACCEPTED`, and commit only those two edits as `docs: accept <TASK-ID>` on the existing local task branch. Report the commit. If the required state records are missing or inconsistent, stop and report `BLOCKED`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=implementer-reviewer-handoff v1 -->
## Implementer-to-reviewer handoff

After validation, create the task commit and push the task branch once for each
review attempt. Record the branch name, implementation commit, and base `main`
commit in the completion handoff. Leave the primary checkout clean and on the
task branch; do not switch back to `main`.

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

Review independence and Git identity separation are both mandatory controls; neither substitutes for the other. The review session must not have written the code and must re-derive evidence from the actual diff and cited sources rather than trusting the implementation report. Only for the `ACCEPTED` commit, use the project-scoped reviewer-specific author override:

```bash
git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
```

Keep the operator's normal committer identity. Do not change global or repository Git config. The override applies only to the `ACCEPTED` commit and can be verified with `git log --format='%an <%ae>'`.
<!-- MERIDIAN:END -->
