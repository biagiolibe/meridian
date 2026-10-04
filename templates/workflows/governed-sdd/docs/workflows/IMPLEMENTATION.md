# Implementation Procedure

Use this procedure only for `Proceed with <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=task-worktree-boundary v7 -->
Order of operations: before `prepare`, read only the router read set
(`AGENTS.md` or `CLAUDE.md`, `PROJECT_WORKFLOW.md`, `LANGUAGE_POLICY.md`, and
this procedure); read no task material and mutate nothing. Apart from the
read-only lookup of the primary checkout, `prepare` is the only command
permitted before `check`. Any other document the phase-reads list names for the
start of work is read only after `check` passes.

Choose exactly one start mode before reading the task, its handoff,
implementation files, or any diff. The task ID is taken only from the
`Proceed with <TASK-ID>` trigger; never infer it from a branch, directory, or
task file.

**Coordinator-launched.** When the coordinator supplied the branch, absolute
worktree path, primary checkout, and worktree root as launch inputs, start in
that exact existing directory. Do not use host automatic isolation or create
another checkout. Run `meridian worktree check <TASK-ID> --project
<primary-checkout> --format json` before any task read.

**Manually triggered.** When no coordinator supplied all of those launch
inputs, determine the primary checkout from the first entry of `git worktree
list --porcelain`. Before any other command, run `meridian worktree prepare
<TASK-ID> --project <primary-checkout> --format json` for exactly the task ID
in the trigger, without `--worktree-root`. A non-zero result, including partial
or mismatched state, an existing active writer, or an unresolvable task ID, is
`BLOCKED`: report the command's message verbatim and change nothing else.
`prepare` is the only command permitted before `check` passes. After a
successful `prepare`, change to its returned worktree and run `meridian
worktree check <TASK-ID> --project <primary-checkout> --format json` there.

For either mode, a blocked `check` result stops all task work and preserves both
checkouts. If the host cannot run commands or write in the prepared directory,
return `BLOCKED`, name that exact directory, and tell the developer to restart
the session there; never fall back to the primary checkout. Run every later
read, implementation, validation, status, and handoff operation in the same
verified worktree, never the primary checkout.

`Proceed with <TASK-ID>` is standing authority for the complete gated lifecycle:
validation, completion and archive records, staging and candidate validation,
finalize or abort, one plain `git push origin main`, and cleanup. It also
authorizes, for the first review attempt, one plain `git push origin
<task-branch>` (the `branch` value returned by `prepare`) only to obtain `T1_CI`
for that task commit; the project's CI is `meridian project show --field ci`,
and without CI there is no push. `Address review <TASK-ID>` authorizes the next
attempt's push, and a reviewer never pushes. `Proceed with` never authorizes tags or releases; force, deleting, or
mirroring pushes; history rewrites; forced worktree removal; bypassing a
required independent review; textual conflict resolution; or another task.
Do not ask for confirmation within that boundary.

After acceptance criteria and required validation pass, commit the completion
and exact archive records. `Review: REQUIRED` then stops at
`REVIEW_REQUIRED`; it is a gate, not a request for authorization. Leave the
clean worktree for the fresh reviewer-integrator, who resumes C4 through C10
after approval. `Review: NOT_REQUIRED` proceeds through C10. The remaining
stops are `ACCEPTANCE_UNMET`, `VALIDATION_FAILED`, `WRONG_WORKTREE`,
`EVIDENCE_INCOMPLETE`, `PRIMARY_DIRTY`, `MAIN_BEHIND_ORIGIN`, `LEASE_HELD`,
`INTEGRATION_CONFLICT`, `CANDIDATE_VALIDATION_FAILED`, `EVIDENCE_MISMATCH`,
`PUSH_REJECTED`, and `CLEANUP_BLOCKED`; report each once with its resume
command. A test-reported sandbox skip is not `VALIDATION_FAILED` only when no
acceptance criterion depends solely on it; record it as `Validation skips:` in
the handoff.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=manual-verification-precondition v3 -->If the task declares `Manual verification: required`, check its `Manual verification rationale` first, before any probe: if it is missing, or names a property readable as a value anywhere in the program (a tier-1 structural or tier-2 derived-value property per `docs/CONTEXT_BUDGET_POLICY.md`'s evidence tiers), return `BLOCKED` asking for the task to be re-scoped as a deterministic check instead — do not run the probe. Only once the rationale names a genuine tier-3 perceptual property, confirm evidence availability before any implementation, not after: run an end-to-end probe that actually succeeds and produces the exact evidence channel the task will record, confirmed readable by the responsible agent or reviewer. A visible terminal entry, a launched process, or a presumed ability to automate an application window is not evidence availability; the probe must actually locate the application window and acquire its image, or otherwise produce and open the real artifact. If no such probe succeeds before implementation, return `BLOCKED` immediately; do not implement in the hope the channel will become available later. A probe that has been attempted and failed is positive evidence about the environment: report it and request the evidence channel from the developer before continuing, whatever the evidence tier — never respond to a failed probe by exploring the local environment for an alternative. When a deterministic test can serve as the change's primary acceptance evidence (for example, a geometry or layout assertion), it suspends only the requirement to *capture* manual or visual confirmation as the sole gate; it never suspends the requirement to stop on a probe that has already been attempted and failed.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=host-impact-routing v1 -->Before implementation, read the task's `Host impact` declaration. `NOT_APPLICABLE` needs a non-empty rationale explaining why no host-facing contract can change. `REQUIRED` needs a host-independent policy outcome, one profile row with every declared column, all three evidence-plan categories, and a fallback for every profile. For a host-sensitive task, if the required static, host-execution, or manual-activation evidence cannot be obtained for a profile, stop and return `BLOCKED`; retain that profile as `unverified`, `advisory`, or `unsupported` with its fallback rather than claiming `enforced`. A template declaration is not host enforcement, and no automatic host probe is required by this routing rule.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=spike-routing v1 -->If any acceptance criterion cannot be evaluated without first discovering an unknown, do not implement past that point: return `BLOCKED`, naming the exact `Class: SPIKE` task (see `tasks/TASK_BLUEPRINT.md`'s spike shape) needed to resolve the unknown, proposing it if it does not exist yet. Do not investigate the unknown inside this task's own branch, commit, or budget — that is what turns a spike into an unbounded side-channel for work that should have gone through its own `Question`/`Budget` gate.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->scoped to the diff's actual surface per `docs/CONTEXT_BUDGET_POLICY.md`'s validation-scope rule — skip a full build/test/lint suite for a documentation/policy-only change and state so explicitly.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=execution-command-gate v2 -->
For a normal task, execute every named `Validation` entry only through
`meridian execution validate <TASK-ID> <validation-id> --project .`; running
the literal command directly is not completion evidence. Before a budgeted
diagnostic, capture, or context expansion, use `meridian execution evidence`.
Before broad or uncertain-yield research outside the initial task authority,
use `meridian execution investigate`. For `Review: REQUIRED`, write the
completion handoff and run `meridian execution ready-check <TASK-ID> --project
.` before setting the task record to `READY_FOR_REVIEW`. If a nonterminal
legacy task lacks the current generated execution contract, run `meridian
execution reconcile <TASK-ID> --apply --project .` before substantive work.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=phase-reads v1 -->
## Phase reads

Read each document when its phase begins, in the order listed. This changes
only when a document is read; no gate, acceptance criterion, or review rule is
waived by reading a document later.

- At start: this procedure, the entry-point router, the workflow document, the language policy, and `docs/CONTEXT_BUDGET_POLICY.md`.
- At first production-source plan: `docs/CODE_ORGANIZATION.md`.
- At proposing a spike: `tasks/TASK_BLUEPRINT.md`.
- At first validation: `docs/EXECUTION_EVIDENCE_PROFILE.md`.
- At completion: `docs/COMPLETION_REPORT_TEMPLATE.md`.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=bounded-context-readers v1 -->
## Bounded context readers

Read the task's cited ADRs and specification sections with `meridian context
authority <TASK-ID>`, and a single ADR with `meridian adr show <ADR-ID>`. Do
not open the whole ADR log or a whole specification to find them. Read the
queue state through the resolved queue briefing, never by opening the whole
queue file. When the briefing did not fire, conflicts with other evidence, or a
row must be read verbatim or edited, locate that row and read only its range.
Open a source document directly only when a bounded reader reports an entry
unresolved or its excerpt cannot verify an acceptance criterion, and record
that reason in the report.
<!-- MERIDIAN:END -->
