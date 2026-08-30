---
name: meridian-governed-sdd
description: Bootstrap or operate a project using Meridian's governed spec-driven task workflow with ADRs, dependency gates, optional review, and reviewer-led integration.
---

# Meridian Governed SDD

Use this skill when the user asks to bootstrap a governed development workflow, create a governed atomic task, perform a review/integration, or audit SDD process conformance.

Read the target project's `PROJECT_WORKFLOW.md` and `AGENTS.md` before acting. If they are absent, use Meridian's `templates/workflows/governed-sdd/` assets to bootstrap them without replacing an existing workflow unless the user explicitly requests migration.

## Routing

- Bootstrap: copy the governed overlay, fill project-specific commands/invariants, and create an initial ADR/task only when explicitly requested.
- Tech design: record decisions in ADRs, then create atomic tasks with explicit dependencies, review policy, measurable acceptance criteria, and validation.
- Implement: work only on the requested task and follow the task lifecycle.
- Review: use `docs/CODE_REVIEW_PROMPT.md`; integrate only if all repository and forge gates are met.
- Audit: read-only comparison of ADRs, specifications, tasks, queue, lifecycle state, and Git evidence.

Keep domain-specific architecture in the target project, not in Meridian's generic workflow assets.

## Token discipline

Read the assigned task before its references, then load only documents and files that the task needs. Do not scan whole backlogs or replay earlier chats when the task report, commit, and diff provide the handoff evidence. Keep plans to three bullets and routine final reports to ten lines. Use review only when the task policy requires it.
