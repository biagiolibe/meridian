# Governed SDD Workflow — [Project Name]

<!-- MERIDIAN:BEGIN capability=workflow-mode-lock v1 -->
## Workflow-mode lock

The presence of this file selects **governed SDD exclusively**. Before any file
edit, Git mutation, task selection, or completion claim, an agent must read
this file and `AGENTS.md` or `CLAUDE.md`, then identify the active mode as
`GOVERNED_SDD`. Global, home-directory, remembered, or generic agent
instructions are not authority to select a lifecycle, task status, queue
format, branch procedure, or review action in this repository.

Do not fall back to Meridian Lean Delivery. In particular, checkbox statuses, moving
tasks to `tasks/done/`, using `PROJECT_PLAN.md` as the canonical queue,
autonomous task selection, and direct completion updates that bypass a task's
review policy are prohibited. A request such as “update the queue” changes
only the authorized governed-SDD record and never authorizes a different
workflow. If the local workflow documents are absent, contradictory, or cannot
be read before a mutation, return `BLOCKED` without changing files or Git
state.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=document-precedence v1 -->
## Document precedence

When documents conflict, the first applicable document wins:

1. `LANGUAGE_POLICY.md` — mandatory conversation-language preference and English-only repository-text invariant.
2. `AGENTS.md` / `CLAUDE.md` — operating rules for the active agent.
3. `docs/ARCHITECTURE_DECISIONS.md` — accepted architecture decisions.
4. Project and milestone specifications.
5. `tasks/QUEUE.md` and atomic task files — execution scope, dependencies, review policy, and validation.
6. `docs/CODE_ORGANIZATION.md` — normative source-organization policy; it cannot change task scope, behavior, or public contracts.
7. Design/background documents.

Implementation never resolves a conflict silently: update the lower-precedence document or record an ADR.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=task-lifecycle v2 -->
## Task lifecycle

```text
Review: REQUIRED
QUEUED -> IN_PROGRESS -> READY_FOR_REVIEW -> ACCEPTED
                         |                    ^
                         +-> CHANGES_REQUESTED -> IN_PROGRESS

Review: NOT_REQUIRED
QUEUED -> IN_PROGRESS -> ACCEPTED

Class: SPIKE
QUEUED -> IN_PROGRESS -> ANSWERED | INCONCLUSIVE
```

Only `ACCEPTED` tasks satisfy dependencies. `ANSWERED` also satisfies a
dependency — it is a `SPIKE`'s completion state and records that its
deliverable (an ADR or a documented reference value; see `tasks/TASK_BLUEPRINT.md`'s
spike shape) answered the declared `Question`. `INCONCLUSIVE` does not
satisfy a dependency: it records that the spike's `Budget` was exhausted
without answering `Question`, and the dependent task stays blocked until a
follow-up spike or a redesign removes the dependency.

Tooling that tallies queue rows by `Review: REQUIRED`/`NOT_REQUIRED` lifecycle
states (for example, the queue-briefing hook) does not recognize
`ANSWERED`/`INCONCLUSIVE`; a `SPIKE` row is invisible to those counts by
design, since it never merges production code for them to track.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=execution-assets v2 -->
## Execution assets

- `docs/CONTEXT_BUDGET_POLICY.md` defines task-first context loading, reasoning profiles, and concise communication.
- `tasks/TASK_BLUEPRINT.md` defines the canonical atomic-task shape.
- `docs/COMPLETION_REPORT_TEMPLATE.md` defines the implementation and review handoff.
- Completion handoffs live at `tasks/handoffs/<TASK-ID>.md`.
- `docs/REVIEW_RECORD_TEMPLATE.md` defines the durable reviewer-to-implementer handoff for requested changes.
- `docs/LIFECYCLE_ORCHESTRATION.md` defines the autonomous orchestration of one task through implementation, review, remediation, and integration.
- `docs/CODE_ORGANIZATION.md` defines module ownership, dependency direction, and visibility rules for production code.
- `docs/AUDIT_PROMPT_READ_ONLY.md` defines a read-only conformance audit for this workflow.
- `docs/OPERATOR_PROMPTS.md` provides non-normative, focused prompts for operating the workflow.

For a task or review, start with `AGENTS.md` or `CLAUDE.md`, then read only the assigned task and sources it cites. These assets are operational guidance and do not supersede the precedence order above.

**Canonical locations.** Task files live at `tasks/<TASK-ID>.md`, the queue at
`tasks/QUEUE.md`, and durable review records at `tasks/reviews/<TASK-ID>.md`,
unless this section declares different locations for this project. Every
other document that references these locations follows this declaration,
not a hardcoded path of its own.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=task-identity-policy v1 -->
## Task identity

`.meridian/task-identity.json` is the sole optional project declaration for
task-identity policy. Its absence selects backwards-compatible `opaque` mode;
an explicit version-1 declaration may select `opaque` or `milestone` mode.
Meridian resolves task IDs through this declaration and the canonical task and
queue authorities. Workflow mode, host configuration, and identifier spelling
do not provide a second identity policy or imply task semantics.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=roles v2 -->
## Roles

- Tech designer: defines ADRs, specifications, task scope, dependencies, and review policy. Does not implement feature code unless explicitly assigned.
- Implementer: works on exactly one task in its deterministic linked worktree, validates it, creates the task commit, pushes once per review attempt, and updates the task state according to its review policy. It never implements in the primary checkout.
- Reviewer-integrator: independently reviews `READY_FOR_REVIEW` tasks in a fresh agent session using the same dedicated task worktree after the implementer has stopped. It records review evidence in the task's review record for every verdict. For `CHANGES_REQUESTED`, it also returns the task to `IN_PROGRESS`; after `APPROVE`, it records `ACCEPTED` in the local review-and-status commit and integrates from the primary checkout when repository gates allow it.
- Orchestrator: coordinates one explicitly assigned task through distinct implementer and reviewer-integrator sessions. It uses only durable task, review, validation, and Git evidence to select the next permitted action; it never implements or reviews substantively.

The developer drives these roles with five command triggers, defined in `AGENTS.md`/`CLAUDE.md`: `Proceed with <TASK-ID>` starts implementation, `Review <TASK-ID>` starts independent review, `Address review <TASK-ID>` starts the bounded remediation recorded by the reviewer, `Run lifecycle <TASK-ID>` authorizes the orchestrated implementation-to-integration loop, and `Accept <TASK-ID>` performs the owner-acceptance status handoff after the developer's own review, skipping the agent review without skipping the status/queue update.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=review-policy v2 -->
## Review policy

Every task declares `Review: REQUIRED`, `Review: NOT_REQUIRED`, or is a
`Class: SPIKE` task governed by its own gate below. `Review: NOT_REQUIRED` is
restricted to low-risk documentation, mechanical configuration, simple
scaffolding, or focused tests that add no production behavior. It is
prohibited for public APIs, dependencies, security, state transitions,
deterministic rules, persistence/history, or unresolved design questions —
unless the task itself is a `SPIKE`, whose entire purpose is investigating one
unresolved design question and whose deliverable is never production code.

A `SPIKE` task does not declare `Review: REQUIRED` or `NOT_REQUIRED`; its
queue row carries `SPIKE` in the `Review` column instead. At close-out
the implementer self-administers this gate: does the committed
deliverable answer the declared `Question` within the declared `Budget`? If
yes, record `ANSWERED`; if `Budget` is exhausted first, record
`INCONCLUSIVE`. No separate reviewer pass is required — a spike's bounded
blast radius (throwaway branch that is never merged, no production code
ships, a declared budget) is what justifies skipping full review. If the
committed deliverable does not self-evidently answer `Question`, record
`INCONCLUSIVE` rather than `ANSWERED` on the strength of author judgment.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=codex-worktree-access v3 -->
Task worktrees live below one machine-level resolved root, namespaced as
`<root>/<remote-host>/<owner>/<repository>/<canonical-task-id>`. Use `meridian
codex worktree-path` for derivation and collision checks and `meridian codex
doctor` for separate trust, permission-model, root-write, command-policy, and
Git-metadata status. Once per machine, run `meridian setup --check`, review the
bounded changes, then explicitly consent with `meridian setup --apply` and
restart Codex. Claude Code needs no host configuration. Static configuration
alone never proves effective host access.

If `meridian codex configure --check` reports `repair-required`, the effective
profile is identical and only Meridian's ownership markers were damaged, for
example by a Codex app rewrite. Review the printed diff and run `--apply` only
after explicit confirmation. A `BLOCKED` result names the diverging fields and
requires manual reconciliation. Repair never proves that a running session
loaded the profile; start a fresh session and probe it.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=bounded-worktree-lifecycle v3 -->
The coordinator runs `meridian worktree prepare` before creating an
implementer, reviewer, or remediation session and passes the returned existing
path, branch, primary checkout, and worktree root as durable launch inputs.
Every worker starts in that exact directory and runs read-only `meridian
worktree check` before any task, handoff, implementation, or diff read. Hosts
must not create a substitute checkout. Integration uses `meridian worktree
integrate stage`, separately recorded candidate validation, and `integrate
finalize` or `integrate abort`; verified post-push cleanup uses `meridian
worktree cleanup`. See `docs/WORKTREE_LIFECYCLE.md`.
Absolute paths are runtime launch inputs only. A handoff or other tracked
record that names the worktree uses the `handoff_worktree` value returned by
`meridian worktree prepare`, the path relative to the worktree root, never an
absolute path.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=git-workflow v7 -->
## Git workflow

- One writer at a time owns each task worktree. `meridian worktree prepare` consumes the shared task-identity resolver and repository-qualified path derivation, rejects partial or mismatched state, and returns the only branch and path workers may use.
- Before any task read or mutation, the worker runs `meridian worktree check` from the exact prepared path. A host-created checkout, the primary checkout, or any sibling path is `BLOCKED` even when its branch and HEAD appear correct.
- After validation, the implementer creates the task commit and pushes the task branch once for each review attempt. Its completion handoff records the task branch, the machine-independent worktree value (the `handoff_worktree` field returned by `meridian worktree prepare`: the path relative to the worktree root, never an absolute path), implementation commit, validated task commit, validated base `main` commit, exact successful validation commands or CI evidence, the declared integration surface, and whether full combined-tree validation is required. It stops writing before review and leaves the dedicated worktree clean.
- The reviewer-integrator's first review action in a fresh session is a fail-closed preflight against the completion handoff: before reading the task, implementation files, or diff, resolve the recorded worktree value against the worktree root, then locate the resulting absolute path and the recorded branch in `git worktree list --porcelain`, confirm the implementer has stopped, and verify the registered path, branch, HEAD, cleanliness, validated task commit, and validated base commit. Any missing or mismatched evidence is `BLOCKED` and preserves all state. A session launched from the primary checkout roots every review read and Git command in the verified task worktree; it never switches or treats the primary checkout as the task checkout.
- For `Review: REQUIRED`, the reviewer-integrator must never push the task branch. On `CHANGES_REQUESTED`, it creates a local review-handoff commit containing only the review record and the matching task/queue transition to `IN_PROGRESS`; it does not edit implementation artifacts. The implementer resolves that record, creates the next implementation commit, and pushes the branch once for the next review attempt. After `APPROVE`, create the local review-and-status `ACCEPTED` commit on the task branch.
- For `Review: NOT_REQUIRED`, the implementer creates the same `ACCEPTED` status commit after validation. Neither path rebases, amends, cherry-picks, or force-pushes reviewed task commits.
- Final integration is serialized in the primary checkout through `meridian worktree integrate stage`. That command verifies accepted evidence, owns the lease and prescribed no-commit merge, and returns the deterministic decision and candidate tree without running project code. Run the selected bounded or full gate separately in the ordinary sandbox, bind successful evidence to that tree, and call `integrate finalize`; call `integrate abort` after failure. Stale, incomplete, or mismatched evidence is `BLOCKED`.
- Reservation, completion, review, and archive changes occur on the task branch. Concurrent tasks edit only their own queue row and task records, without reordering shared files, changing shared timestamps, or archiving a phase. Phase archival occurs only after all rows are integrated. A shared-governance conflict aborts integration; never choose one task's state over another.
- Only after successful validated integration and any required `main` push, use `meridian worktree cleanup`. Failure, requested changes, cancellation, or blocked integration retains both; exceptional cleanup remains explicitly authorized and outside the bounded command.
- Owner acceptance is an explicit exception: it updates only statuses and does not automatically integrate the branch.
- A forge approval cannot be supplied by the same identity that authored the PR. If an external approval is required but unavailable, leave the PR open and report `BLOCKED`.

### Reviewer-integrator identity on a single-operator project

Both controls below are mandatory, and neither substitutes for the other:

- The review runs in a fresh agent session that did not write the code. The reviewer re-derives evidence from the actual diff and cited sources rather than trusting the implementation report.
- Only for the acceptance commit, use this project-scoped reviewer-specific author override, replacing the placeholders with the project's actual name and slug:

  ```bash
  git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
  ```

Keep the operator's normal committer identity. Do not change global or repository Git config. The author override applies only to the `ACCEPTED` commit and can be verified with `git log --format='%an <%ae>'`.
<!-- MERIDIAN:END -->

Project integration smoke command: `none`.

<!-- MERIDIAN:BEGIN capability=execution-discipline v1 -->
## Execution discipline

Apply `docs/CONTEXT_BUDGET_POLICY.md`. The review-policy restrictions above remain authoritative; use parallel agents only when their scopes and worktrees are independent.
<!-- MERIDIAN:END -->
