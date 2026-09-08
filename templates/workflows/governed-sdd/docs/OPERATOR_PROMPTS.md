# Governed SDD Operator Prompts

This non-normative cookbook provides focused prompts for starting Meridian chats. It does not change document precedence, task scope, task status, review policy, Git safeguards, or tool permissions. `LANGUAGE_POLICY.md`, `AGENTS.md`/`CLAUDE.md`, the assigned task, and the canonical workflow documents always govern the result.

For a repository containing `PROJECT_WORKFLOW.md`, these prompts operate only
in `GOVERNED_SDD` mode. They never authorize a fallback to Meridian Lean Delivery or
to any global/home-directory workflow instruction. If the local workflow files
are missing or contradictory, the agent must return `BLOCKED` before a mutation.

Replace every `<PLACEHOLDER>` before sending a prompt. Use one workflow per chat. An implementation and its required review must use separate chats, except that `Run lifecycle <TASK-ID>` is a coordinator chat that delegates each role to a separate session. Before starting an implementation, remediation, or review, confirm the project's `docs/EXECUTION_EVIDENCE_PROFILE.md` is configured for the task's stack and evidence channels.

The agent must communicate in the language persisted in `LANGUAGE_POLICY.md`, even if a prompt uses another language. Any repository artifact produced by a prompt must remain in English.

## Choose the reasoning level before sending

The chat's configured reasoning effort is the effective runtime setting. A task's
`Reasoning` field is its exact permitted cap, not a minimum or a suggestion;
it does not reconfigure an already-open chat. When the active agent supports
reasoning selection, create each worker chat at that exact level. If the
effective setting differs or cannot be confirmed, do not start substantive
work: launch a fresh chat at the declared level. Never raise an agent's effort
automatically. A `high` task must carry its written rationale; an `xhigh` task
also requires the developer's explicit authorization.

| Work | Default | Escalate only when |
| --- | --- | --- |
| Focused administrative or mechanical work | `low` | The task's bounded scope demonstrates that deeper reasoning is unnecessary. |
| Routine implementation, review, and task decomposition | `medium` | The task has a written complexity rationale and is materially ambiguous. |
| Design or architecture | `high` | The task records the cross-layer trade-off or unresolved authority interaction. |
| Exceptional work | `xhigh` | The task records the exceptional need and the developer explicitly authorizes it. |

## 1. Report project status (read-only)

Use this before deciding what to do next.

```text
Report the current governed-SDD status without modifying files.

Use the minimal read-only status profile in docs/CONTEXT_BUDGET_POLICY.md.
Confirm only the active workflow mode and local status rules, non-terminal
queue entries, their direct dependency readiness, the current Git state, the
next permitted governance action, and blockers.

Do not load completed milestones, broad file inventories, full specifications,
ADRs, audit prompts, review records, or Git history unless a concrete
discrepancy, blocker, or requested handoff requires them. State the specific
evidence gap before every expanded read. Do not select a task, implement code,
review code, change files, create commits, or reconstruct prior chat context.
```

## 2. Design a change or decompose a milestone

Use this for planning and governance only; it does not authorize implementation.

```text
Act as the project tech designer. Design <MILESTONE OR CHANGE>.

Read LANGUAGE_POLICY.md, AGENTS.md or CLAUDE.md, PROJECT_WORKFLOW.md,
docs/CONTEXT_BUDGET_POLICY.md, tasks/QUEUE.md,
docs/PULL_REQUEST_POLICY.md, and docs/CODE_ORGANIZATION.md. Load only the
ADRs, specifications, accepted verification evidence, and tasks needed for
this design. Use repository files as the source of truth.

Do not implement code, perform a code review, or choose an unassigned task.
Record durable decisions in an ADR and a normative specification only when
needed. Create or materially revise only atomic tasks that follow
tasks/TASK_BLUEPRINT.md: declare dependencies, reasoning and justification,
review policy, authority, expected code surface, measurable acceptance
criteria, validation, and out-of-scope boundaries. Do not anticipate later
milestones.

Verify the documentation diff. Create a commit only if the governing workflow
and current authorization permit it. Report changed files, assumptions, and
the next permitted governance action.
```

## 3. Design the next milestone or phase

Use this when the next milestone is not already named. The tech designer derives it from accepted project evidence rather than assuming a roadmap item or solution.

```text
Act as the project tech designer. Design the next appropriate milestone or
phase.

Determine what comes next from the current accepted project state; do not
assume a milestone name, roadmap item, or solution in advance.

Read LANGUAGE_POLICY.md, AGENTS.md or CLAUDE.md, PROJECT_WORKFLOW.md,
docs/CONTEXT_BUDGET_POLICY.md, tasks/QUEUE.md, relevant accepted ADRs,
specifications, completion reports, verification evidence, and only the Git
history needed to establish the current state.

Identify the highest-value next governed step permitted by accepted
dependencies, documented goals, unresolved risks, and architectural boundaries.
If no next milestone can be justified from repository evidence, report that
explicitly rather than inventing one.

Do not implement code, review code, select an implementation task, or modify
unrelated project records. When a next milestone is justified, create or update
only the necessary ADRs, normative specifications, and atomic tasks following
tasks/TASK_BLUEPRINT.md. Each task must declare authority, dependencies,
reasoning and justification, review policy, expected code surface, measurable
acceptance criteria, validation, and out-of-scope boundaries.

Verify the documentation diff. Create a commit only if the governing workflow
and current authorization permit it. Report the proposed milestone, its
rationale, changed files, assumptions, dependencies, and the next permitted
governance action.
```

## 4. Analyze an accepted result

Use this to interpret evidence without turning the chat into a review or implementation task.

```text
Analyze the accepted result of <MILESTONE OR CHANGE> as tech-design and
governance input.

Read the relevant specification, accepted tasks, completion or verification
reports, governing ADRs, the canonical queue, and only the Git history needed
to establish the result. Use repository files as the source of truth.

Explain what the evidence demonstrates, what remains bounded or unproven, and
which documented claims are inconsistent with the evidence, if any. Do not
perform a formal code review, change files, create future work, select a task,
or implement a remedy. End with the next permitted governance state.
```

## 5. Implement exactly one task

Use this in a dedicated implementation chat only after the task is dependency-ready. Configure the chat at the task's exact declared reasoning cap first when supported; if its effective level cannot be confirmed, do not proceed.

```text
Proceed with <TASK-ID>.
```

The trigger delegates the detailed implementation procedure to `AGENTS.md` or `CLAUDE.md`. Do not append unrelated work to this prompt.

## 5a. Run one autonomous required-review lifecycle

Use this when the task is dependency-ready and you authorize implementation,
all remediation cycles, acceptance, and the final `main` push. The coordinator
must use distinct implementer and reviewer sessions; it must not turn its own
chat into either role.

```text
Run lifecycle <TASK-ID>.
```

The trigger delegates the full procedure to
`docs/LIFECYCLE_ORCHESTRATION.md`. It continues from durable repository state,
uses `tasks/reviews/<TASK-ID>.md` instead of copied chat findings, and stops
only at its retry limit or a real repository, validation, authority, or forge
blocker.

## 6. Independently review a required-review task

Use this in a fresh chat that did not implement the task.

```text
Review <TASK-ID>.
```

The trigger delegates the detailed review and integration procedure to `AGENTS.md` or `CLAUDE.md` and `docs/CODE_REVIEW_PROMPT.md`.

## 7. Record owner acceptance after personal review

Use this only after personally reviewing a `Review: REQUIRED` task marked `READY_FOR_REVIEW` in both canonical status records.

```text
Accept <TASK-ID>.
```

The trigger performs only the status-only owner-acceptance workflow defined in `AGENTS.md` or `CLAUDE.md`; it does not authorize a review, source change, validation rerun, or merge.

## 7a. Address requested review changes

Use this after an independent reviewer returns `CHANGES_REQUESTED`. The
reviewer has already recorded the scope, evidence, and state transition in
`tasks/reviews/<TASK-ID>.md`; do not copy the findings into this prompt.

```text
Address review <TASK-ID>.
```

The trigger limits implementation to the unchecked findings in the durable
review record, validates them, returns the task to `READY_FOR_REVIEW`, and
pushes the next review attempt. It does not authorize unrelated work or a
reinterpretation of a finding.

## 8. Run the established read-only audit

```text
Perform the repository's read-only governed-SDD audit using
docs/AUDIT_PROMPT_READ_ONLY.md. Do not modify files, run write-mode formatters,
create commits, or implement code. Report PASS/FAIL findings with file and line
evidence only.
```

## 9. Correct a bounded documentation inconsistency

Use this when a source claim is demonstrably stale or inconsistent. Name the exact target; do not silently widen scope into a redesign.

```text
Correct this documentation inconsistency only:
<EXACT INCONSISTENCY AND TARGET FILES>.

Read LANGUAGE_POLICY.md, AGENTS.md or CLAUDE.md, PROJECT_WORKFLOW.md,
docs/CONTEXT_BUDGET_POLICY.md, the canonical source that establishes the
correct statement, and the target files. Do not change source code, task
acceptance states, queue ordering, ADR intent, or unrelated documentation.
Verify the resulting documentation diff. Create a commit only if the governing
workflow and current authorization permit it. Report the evidence and any
commit created.
```

## 10. Ask a bounded repository question

Use this for explanation or diagnosis without granting modification authority.

```text
Answer this repository question using repository files only:
<QUESTION>

Read only the authoritative documents, task records, reports, and source files
needed to answer. Cite exact repository paths. Do not change files, implement
work, review a task, or infer a new roadmap item.
```

## Useful short forms

```text
Proceed with <TASK-ID>.
Run lifecycle <TASK-ID>.
Review <TASK-ID>.
Address review <TASK-ID>.
Accept <TASK-ID>.
Analyze <MILESTONE> as governance only; do not modify files.
Report the current SDD handoff state; do not modify files.
```

## What a prompt cannot authorize

- A task may start only when its dependencies are `ACCEPTED` and the developer explicitly assigns it.
- A required-review task needs a separate reviewer-integrator chat unless the owner uses the explicit `Accept <TASK-ID>` path.
- `Run lifecycle <TASK-ID>` may coordinate the required-review loop only through distinct implementer and reviewer sessions, as defined by `docs/LIFECYCLE_ORCHESTRATION.md`.
- A prompt cannot change a chat's reasoning setting; configure it before sending the prompt when the active agent supports it.
- A task, review, audit, or analysis does not authorize unrelated code, future milestones, destructive Git recovery, or external publication.
