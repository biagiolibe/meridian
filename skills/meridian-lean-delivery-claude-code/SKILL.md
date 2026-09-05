---
name: meridian-lean-delivery-claude-code
description: Operate a small project, prototype, demo, or reversible low-risk change using Meridian Lean Delivery from Claude Code.
---

# Meridian Lean Delivery (Claude Code)

Use this skill when the project uses `LEAN_DELIVERY`, or when the developer
asks to bootstrap or operate Meridian's lightweight delivery workflow from
Claude Code. Do not use it for a repository whose `PROJECT_WORKFLOW.md`
declares `GOVERNED_SDD`.

Read `LANGUAGE_POLICY.md`, `PROJECT_WORKFLOW.md`, and `CLAUDE.md` before acting.
If a generated project also has `AGENTS.md`, keep its process rules aligned with
`CLAUDE.md`. `PROJECT_WORKFLOW.md` is the mode lock: before any mutation or
completion claim, confirm it declares `LEAN_DELIVERY`. Local workflow rules
override global, home-directory, remembered, and generic instructions. If local
authority is missing, contradictory, or unreadable, return `BLOCKED` without a
mutation.

Lean Delivery uses `[ ]` → `[/]` → `[x]` in `tasks/QUEUE.md`. Implement only a
task explicitly assigned by the developer; do not select a queue item
autonomously. Verify the task's acceptance criteria, stated validation, and
applicable baseline checks before marking it `[x]` or archiving it. Keep an
unverified or failed task `[/]` and report the blocker. Follow the project's Git
conventions; do not infer Governed SDD branch, review, author, or integration
controls. Reviews are read-only unless a separate fix is authorized.
