# Implementation Procedure

Use this procedure only for `Proceed with <TASK-ID>` after the entry-point router has applied its always-loaded invariants.

<!-- MERIDIAN:BEGIN capability=manual-verification-precondition v3 -->If the task declares `Manual verification: required`, check its `Manual verification rationale` first, before any probe: if it is missing, or names a property readable as a value anywhere in the program (a tier-1 structural or tier-2 derived-value property per `docs/CONTEXT_BUDGET_POLICY.md`'s evidence tiers), return `BLOCKED` asking for the task to be re-scoped as a deterministic check instead — do not run the probe. Only once the rationale names a genuine tier-3 perceptual property, confirm evidence availability before any implementation, not after: run an end-to-end probe that actually succeeds and produces the exact evidence channel the task will record, confirmed readable by the responsible agent or reviewer. A visible terminal entry, a launched process, or a presumed ability to automate an application window is not evidence availability; the probe must actually locate the application window and acquire its image, or otherwise produce and open the real artifact. If no such probe succeeds before implementation, return `BLOCKED` immediately; do not implement in the hope the channel will become available later. A probe that has been attempted and failed is positive evidence about the environment: report it and request the evidence channel from the developer before continuing, whatever the evidence tier — never respond to a failed probe by exploring the local environment for an alternative. When a deterministic test can serve as the change's primary acceptance evidence (for example, a geometry or layout assertion), it suspends only the requirement to *capture* manual or visual confirmation as the sole gate; it never suspends the requirement to stop on a probe that has already been attempted and failed.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=host-impact-routing v1 -->Before implementation, read the task's `Host impact` declaration. `NOT_APPLICABLE` needs a non-empty rationale explaining why no host-facing contract can change. `REQUIRED` needs a host-independent policy outcome, one profile row with every declared column, all three evidence-plan categories, and a fallback for every profile. For a host-sensitive task, if the required static, host-execution, or manual-activation evidence cannot be obtained for a profile, stop and return `BLOCKED`; retain that profile as `unverified`, `advisory`, or `unsupported` with its fallback rather than claiming `enforced`. A template declaration is not host enforcement, and no automatic host probe is required by this routing rule.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=spike-routing v1 -->If any acceptance criterion cannot be evaluated without first discovering an unknown, do not implement past that point: return `BLOCKED`, naming the exact `Class: SPIKE` task (see `tasks/TASK_BLUEPRINT.md`'s spike shape) needed to resolve the unknown, proposing it if it does not exist yet. Do not investigate the unknown inside this task's own branch, commit, or budget — that is what turns a spike into an unbounded side-channel for work that should have gone through its own `Question`/`Budget` gate.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->scoped to the diff's actual surface per `docs/CONTEXT_BUDGET_POLICY.md`'s validation-scope rule — skip a full build/test/lint suite for a documentation/policy-only change and state so explicitly.<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=execution-command-gate v1 -->
For a normal task, execute every named `Validation` entry only through
`meridian execution validate <TASK-ID> <validation-id> --project .`; running
the literal command directly is not completion evidence. Before a budgeted
diagnostic, capture, or context expansion, use `meridian execution evidence`.
Before broad or uncertain-yield research outside the initial task authority,
use `meridian execution investigate`. For `Review: REQUIRED`, write the
completion handoff and run `meridian execution ready-check <TASK-ID> --project
.` before setting the task or queue row to `READY_FOR_REVIEW`. If a nonterminal
legacy task lacks the current generated execution contract, run `meridian
execution reconcile <TASK-ID> --apply --project .` before substantive work.
<!-- MERIDIAN:END -->
