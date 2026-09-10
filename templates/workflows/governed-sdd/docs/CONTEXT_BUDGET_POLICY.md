# Context Budget and Reasoning Policy

This policy reduces context and reasoning overhead while preserving governed-SDD authority and review quality.

## Task-first loading

For an implementation or review:

1. Read `AGENTS.md` or `CLAUDE.md`, then the assigned task.
2. Read only the task's `Authority` entries and the minimum files needed to verify its `Expected code surface`.
3. Do not scan the repository, full backlog, unrelated ADRs/specifications, prior chats, or generic design documents without a task-specific need.
4. Expand context only when the task is blocked, an acceptance criterion cannot be verified, or an authoritative conflict is discovered. Record the reason in the completion or review report.
5. <!-- MERIDIAN:BEGIN capability=queue-briefing v1 -->For the task queue, rely on the resolved briefing that fires at the start of each turn — active, in-review, next-startable, and dependency-blocked rows — instead of opening the queue file. Open it directly only when the briefing did not fire, a row's exact wording or a column it does not surface is needed, or its resolved state conflicts with other evidence.<!-- MERIDIAN:END -->

Dependencies establish readiness; they do not automatically require rereading their entire implementation history.

<!-- MERIDIAN:BEGIN capability=minimal-read-only-status v1 -->
## Minimal read-only status

For a request to report the current governed-SDD status without modifying
files, minimize context deliberately:

1. Read `LANGUAGE_POLICY.md`, then only the portions of `AGENTS.md` or
   `CLAUDE.md` and `PROJECT_WORKFLOW.md` needed to confirm the active mode and
   the local status-reporting rules.
2. Read this policy, query the canonical queue for non-terminal entries only,
   and inspect Git's current branch, clean/dirty state, and configured remote
   relation when relevant.
3. Read only the direct dependencies and task records needed to establish
   readiness for the next permitted governance action.
4. Do not load completed milestones, broad file inventories, full
   specifications, ADRs, audit prompts, review records, or Git history unless
   a concrete discrepancy, blocker, or requested handoff requires them.
5. Before every expanded read, state the specific evidence gap it resolves.

A status report is not a conformance audit. It reports workflow mode,
non-terminal work, dependency readiness, Git state, the next permitted action,
and blockers; use the audit procedure only when the developer asks for an
audit.
<!-- MERIDIAN:END -->

## Validation scope

<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->
Before running validation, classify the diff by surface: *documentation/policy
text* (Markdown, comments, configuration prose with no build or runtime
effect) versus *source/build* (application code, dependency manifests, build
or CI configuration). Run only the validation commands whose surface
intersects the actual diff. For a documentation/policy-only change, skip the
project's full build, test, and lint suites and state so explicitly in the
completion or review report (for example: "skipped: full test/build/lint
suite — no source or build surface changed") instead of running them
defensively. This is distinct from the existing exemption for a command that
is inapplicable because its target artifact does not exist yet: skip a
command here because its surface was not touched, not because it cannot run.

A reviewer verifies the same scoping: confirm that validation evidence
matches the actual diff surface, that nothing relevant was skipped, and that
nothing irrelevant was run and reported as if it were meaningful evidence.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=evidence-tiers v1 -->
## Evidence tiers

Before declaring `Manual verification: required`, name which tier the
property belongs to; only tier 3 justifies it.

1. **Structural** — counts, presence, identity, ordering, spawn/despawn invariants. Assertable directly.
2. **Derived value** — any observable the program itself computes and can read back: layout geometry, formatted output, serialized state, a colour held as a value, a duration. Assertable once you know where to read it.
3. **Perceptual** — exists only in the rendered artifact and nowhere as a value: shading, font rendering, visual balance, "does it read correctly".

If the property is readable as a value anywhere in the program, assert it instead of capturing it.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=execution-evidence-profile v3 -->
## Execution evidence discipline

Apply the project-specific `docs/EXECUTION_EVIDENCE_PROFILE.md` before an
implementation, remediation, or review. It translates this stack-agnostic
discipline into the project's commands, log locations, diagnostic tools, and
manual-evidence channels. Configure that profile during bootstrap or before the
first implementation after an upgrade that adds it.

- Do not reload or reproduce instructions, source text, tool documentation, or
  successful command output already available in the active session unless the
  source changed or an exact passage is needed to resolve a recorded evidence
  gap.
- Run the profile's literal declared command string for every required
  validation command, output bound included; do not run the bare command and
  summarize or truncate its output afterwards, since a bound applied only
  after the fact cannot stop already-billed output from entering context.
  Preserve the command and its exit status; expose expanded logs only for a
  failure, and start with the narrowest diagnostic output that can identify
  the failing component.
- Escalate diagnostics progressively. Do not request a full backtrace, trace,
  verbose mode, or complete log until ordinary output and a targeted diagnostic
  leave the cause or location unresolved. Record the reason for escalation.
- Do not use repeated test-and-tune cycles as a substitute for an approved
  implementation strategy. Before a second diagnostic attempt that changes an
  implementation hypothesis, state the evidence gap it will resolve. If a
  focused failure exposes a conflict between the task's acceptance criteria,
  authority, or allowed code surface, return `BLOCKED`; do not continue
  searching for a workaround past the profile's declared diagnostic-attempt
  budget.
- Inspect every changed hunk, beginning with a change summary and then
  per-file/hunk evidence. A complete printed diff is not required merely to
  establish diff scope.
- Plan manual evidence from the task's acceptance criteria before invoking UI
  or capture tools. Gather only the distinct views the criteria require; do not
  repeat a tool discovery call or acquire extra images without an evidence gap.
  Prefer a project-declared direct capture path when it supplies the required
  evidence without interaction.
- Reuse unchanged successful validation evidence during independent review
  unless a credibility or coverage gap requires a rerun. Independent source and
  diff review remain mandatory.

Choose the lowest reliable configured reasoning level. If the active agent
interface offers a faster execution mode, it may be used only when it does not
override the task's declared reasoning requirement or reduce required evidence.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=reasoning-budget-contract v1 -->
## Reasoning budget contract

Select the lowest reliable reasoning effort while designing the task, then
record it in the task's `Reasoning` field as the exact permitted runtime cap.
It is not a minimum: a worker must not silently use a higher configured
effort, and it must not raise its own effort because a task appears difficult.

Before implementation, remediation, or independent review, confirm the
worker's configured reasoning effort equals the task value. If it differs, or
cannot be confirmed, stop before substantive work and start a fresh session at
the declared value. Reducing or increasing the cap requires a material task
revision with its rationale; `high` requires a written complexity rationale,
and `xhigh` additionally requires the developer's explicit authorization.

This contract governs worker sessions. A lifecycle orchestrator uses the
lowest available effort because it only reads durable state and delegates no
substantive work.
<!-- MERIDIAN:END -->

## Lifecycle orchestration

For `Run lifecycle <TASK-ID>`, the orchestrator reads only the task and queue
status, the latest implementation commit, the latest review-record attempt,
and worker result fields. It delegates implementation and review to distinct
sessions and never copies their conversational context. Use the task's
reasoning profile for workers and the lowest supported profile for the
orchestrator. Do not add a separate summarization step or rerun an unchanged
successful validation.

## Planning and communication

- Keep execution plans to three bullets or fewer.
- Report only state changes, material findings, validation results, or blockers.
- Keep routine completion and review reports concise; include detail only for deviations or unresolved risk.
- Do not use parallel agents or repeated inspections when they add no independent evidence.

## Reasoning profile

Use the lowest profile that can reliably satisfy the task:

| Work | Default profile | Escalate when |
|---|---|---|
| Implementation, review, task decomposition, and routine SDD work | `medium` | Evidence is insufficient or the task is materially ambiguous |
| Design or complex architecture | `high` | Cross-layer trade-offs or unresolved authority interactions require it |
| Exceptional high-complexity work | `xhigh` | Only with explicit justification and only if active tooling/configuration supports it |

Never hardcode an unsupported model, reasoning level, or tool option. If escalation is unavailable, keep the task scoped and report the limitation rather than widening the task.
