---
name: meridian-governed-sdd-claude-code
description: Bootstrap or operate a project using Meridian's governed spec-driven task workflow (ADRs, dependency gates, optional review, reviewer-led integration) from Claude Code. Use when the user asks to bootstrap governed SDD, design/scope a governed task, implement an assigned TASK-ID, run a review/integration pass, or audit governed-workflow conformance in a Claude Code session.
---

# Meridian Governed SDD (Claude Code)

Claude Code counterpart of the Codex `meridian-governed-sdd` skill (`skills/meridian-governed-sdd/`). Same governed lifecycle and documents; this version is written for a Claude Code session and its plugin commands instead of Codex's `AGENTS.md`-only, `$name`-invoked skills.

Read the target project's `LANGUAGE_POLICY.md`, `PROJECT_WORKFLOW.md`, and `CLAUDE.md` before acting. `LANGUAGE_POLICY.md` fixes the developer-facing language independently of the current prompt and requires English for all persistent repository text. When present, also read `docs/CONTEXT_BUDGET_POLICY.md`; it governs context loading and reasoning selection. If the project was also generated for Codex, it will additionally have `AGENTS.md` — the two must not drift; treat `PROJECT_WORKFLOW.md` as the shared source of truth and update both instruction files together when the process changes.

If governed documents are absent, bootstrap them rather than working ad hoc:

- Prefer running this plugin's `/meridian-init` command with workflow mode `governed-sdd` — it also handles the base templates (`PROJECT_PLAN.md`, `TECH_DESIGN.md`, etc.) and the persistent conversation-language setting in one pass.
- Fall back to asking the developer for a conversation language, then copying `templates/workflows/governed-sdd/` (`LANGUAGE_POLICY.md`, `PROJECT_WORKFLOW.md`, `CLAUDE.md`, `AGENTS.md`, `docs/`, `tasks/`) directly and replacing `[Conversation language]` in `LANGUAGE_POLICY.md` only if `/meridian-init` is not installed in this session. Repository text remains English in all cases.

Never overlay the governed workflow onto an existing project without showing the diff and getting an explicit migration decision — the project may already have its own task queue, agent instructions, or branch policy.

## Routing

- **Bootstrap**: run `/meridian-init` (mode `governed-sdd`) when available; otherwise copy the governed overlay and fill in project-specific commands/invariants. Create an initial ADR/task only when explicitly requested.
- **Tech design**: record decisions in `docs/ARCHITECTURE_DECISIONS.md`, then create atomic tasks — via `/meridian-task` (it detects `PROJECT_WORKFLOW.md` and switches to governed mode automatically) or directly from `tasks/TASK_BLUEPRINT.md` — with explicit dependencies, authority, expected code surface, reasoning profile, review policy, measurable acceptance criteria, validation, and out-of-scope boundary. Do not pick the next task to work on automatically.
- **Implement**: work only on the one assigned `TASK-ID`, in its own branch/worktree (`task-NNN`, no provider prefix). Read the task, its cited authority, its expected code surface, and `git status --short` first; state a short plan (max three bullets) and stop if unrelated changes or an unresolved higher-precedence conflict exist. Run the task's validation plus the project baseline checks from `CLAUDE.md`. Update the task and its `tasks/QUEUE.md` row to `READY_FOR_REVIEW` or `ACCEPTED` per its `Review` policy — never claim completion when required validation fails.
- **Review/integrate**: use `docs/CODE_REVIEW_PROMPT.md`. Run the review from a context independent of the implementer's — a fresh chat, or a Task-tool subagent when this session has one — so the reviewer-integrator isn't anchored on the implementer's own reasoning. Read `PROJECT_WORKFLOW.md`, `CLAUDE.md`/`AGENTS.md`, the task, its governing documents, and the exact diff; report `APPROVE`, `CHANGES_REQUESTED`, or `BLOCKED`. After `APPROVE` only, verify `git merge-base --is-ancestor main <task-branch>`, create only the local status-only `ACCEPTED` commit with the project-scoped reviewer author override, then fast-forward and push `main` exactly once and delete the local task branch. Never push the task branch again; remote cleanup is optional and never blocks accepted `main` integration; follow `docs/PULL_REQUEST_POLICY.md` for ancestry, checkout, and forge-gate conditions.
- **Owner acceptance**: on `Accept <TASK-ID>` from the developer, run only the status-only handoff in `CLAUDE.md`/`AGENTS.md` — confirm both status records are `READY_FOR_REVIEW`, set both to `ACCEPTED`, commit that alone. Do not re-review, revalidate, or merge.
- **Audit**: read-only comparison of ADRs, specifications, tasks, queue, lifecycle state, and Git evidence against `PROJECT_WORKFLOW.md`, using `docs/AUDIT_PROMPT_READ_ONLY.md`. Report drift; do not fix it silently.

Keep domain-specific architecture in the target project, not in Meridian's generic workflow assets. `docs/CODE_ORGANIZATION.md` states generic ownership/dependency-direction rules only; the project's own module map belongs in its architecture documentation.

## Context and reasoning discipline

Apply `docs/CONTEXT_BUDGET_POLICY.md` when it exists. Start with the assigned task, then load only its authority and expected code surface; expand context only for a blocker, insufficient acceptance evidence, or an authoritative conflict. Use `medium` by default for implementation, review, and routine SDD work; use `high` for complex design/architecture, and `xhigh` only with explicit justification when the active tooling supports it. Use `docs/COMPLETION_REPORT_TEMPLATE.md` for concise handoffs. Review only when the task policy requires it, and prefer a dedicated subagent (Task tool) over widening the current context whenever a step calls for isolation (review, audit) rather than continuity with the implementer.
