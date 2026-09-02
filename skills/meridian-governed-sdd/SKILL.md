---
name: meridian-governed-sdd
description: Bootstrap or operate a project using Meridian's governed spec-driven task workflow with ADRs, dependency gates, optional review, and reviewer-led integration.
---

# Meridian Governed SDD

Use this skill when the user asks to bootstrap a governed development workflow, create a governed atomic task, perform a review/integration, or audit SDD process conformance.

Read the target project's `PROJECT_WORKFLOW.md` and `AGENTS.md` before acting. When present, also read `docs/CONTEXT_BUDGET_POLICY.md`; it governs context loading and reasoning selection. If these documents are absent, bootstrap them from Meridian's own template source, without replacing an existing workflow unless the user explicitly requests migration.

The Meridian template source is at `$MERIDIAN_ROOT` (an environment variable pointing at your local clone of the `meridian` repository, e.g. `export MERIDIAN_ROOT=/path/to/meridian` in your shell profile). If `$MERIDIAN_ROOT` is unset or does not point at a valid Meridian checkout, stop and ask the user for the repository path instead of guessing one — then remind them to set `MERIDIAN_ROOT` so future invocations don't need to repeat it. Copy `$MERIDIAN_ROOT/templates/workflows/governed-sdd/` (`PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md`, `docs/`, `tasks/`) into the target project.

## Routing

- Bootstrap: copy the governed overlay, fill project-specific commands/invariants, and create an initial ADR/task only when explicitly requested.
- Tech design: record decisions in ADRs, then create atomic tasks with explicit dependencies, authority, expected code surface, reasoning profile, review policy, measurable acceptance criteria, validation, and out-of-scope boundary.
- Implement: work only on the requested task, its cited authority, and its expected code surface; follow the task lifecycle.
- Review: use `docs/CODE_REVIEW_PROMPT.md` in a fresh session that did not write the implementation; integrate only if all repository and forge gates are met. The reviewer never pushes the task branch again.
- Owner acceptance: on `Accept <TASK-ID>`, perform only the status-only handoff described in `AGENTS.md`; do not re-review, revalidate, or merge.
- Audit: read-only comparison of ADRs, specifications, tasks, queue, lifecycle state, and Git evidence, using `docs/AUDIT_PROMPT_READ_ONLY.md`.

Keep domain-specific architecture in the target project, not in Meridian's generic workflow assets. `docs/CODE_ORGANIZATION.md` states generic ownership/dependency-direction rules only; the project's own module map belongs in its architecture documentation.

## Context and reasoning discipline

Apply `docs/CONTEXT_BUDGET_POLICY.md` when it exists. Start with the assigned task, then load only its authority and expected code surface; expand context only for a blocker, insufficient acceptance evidence, or an authoritative conflict. Use `medium` by default for implementation, review, and routine SDD work; use `high` for complex design/architecture, and `xhigh` only with explicit justification when the active tooling supports it. Use `docs/COMPLETION_REPORT_TEMPLATE.md` for concise handoffs. Review only when the task policy requires it. A remote task-branch cleanup is optional and never blocks an accepted `main` integration; follow `docs/PULL_REQUEST_POLICY.md`.
