# Context Budget and Reasoning Policy

This policy reduces context and reasoning overhead while preserving governed-SDD authority and review quality.

## Task-first loading

For an implementation or review:

1. Read `AGENTS.md` or `CLAUDE.md`, then the assigned task.
2. Read only the task's `Authority` entries and the minimum files needed to verify its `Expected code surface`.
3. Do not scan the repository, full backlog, unrelated ADRs/specifications, prior chats, or generic design documents without a task-specific need.
4. Expand context only when the task is blocked, an acceptance criterion cannot be verified, or an authoritative conflict is discovered. Record the reason in the completion or review report.

Dependencies establish readiness; they do not automatically require rereading their entire implementation history.

<!-- MERIDIAN:BEGIN capability=role-scoped-agent-rules v1 -->
## Role-scoped agent-rules reading

`AGENTS.md`/`CLAUDE.md` states rules for every role in one file; reading all
of it in every session is more than a given role needs. Read only the
sections your current role requires, identified by heading text:

- **Every role** reads the file's shared core: the introductory rules
  through "Command triggers", plus "Owner-acceptance workflow".
- **Implementer** (`Proceed with <TASK-ID>`, `Address review <TASK-ID>`)
  additionally reads "Autonomous lifecycle orchestration", "Implementation
  workflow", "Review-remediation workflow", and "Implementer-to-reviewer
  handoff".
- **Reviewer-integrator** (`Review <TASK-ID>`) additionally reads
  "Autonomous lifecycle orchestration", "Review-mode boundary",
  "Reviewer-integrator identity", and "Implementer-to-reviewer handoff".
- **Orchestrator** (`Run lifecycle <TASK-ID>`) does not read this file at
  all beyond confirming the command triggers it issues exist; see this
  policy's "Lifecycle orchestration" section for what it reads instead.

Match sections by heading text, not by line number or position, since a
future migration can move content between headings without renaming them.
If a heading this rule names is missing, renamed, or the mapping is
otherwise unclear, read the whole file instead of guessing — this rule
narrows a known-safe read; it never licenses skipping unfamiliar content.
<!-- MERIDIAN:END -->

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

<!-- MERIDIAN:BEGIN capability=execution-evidence-profile v1 -->
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
- Execute every required validation command, but use the profile's concise
  success-output form. Preserve the command and exit status; expose expanded
  logs only for a failure, and start with the narrowest diagnostic output that
  can identify the failing component.
- Escalate diagnostics progressively. Do not request a full backtrace, trace,
  verbose mode, or complete log until ordinary output and a targeted diagnostic
  leave the cause or location unresolved. Record the reason for escalation.
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
