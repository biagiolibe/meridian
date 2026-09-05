---
name: meridian-lean-delivery
description: Operate a small project, prototype, demo, or reversible low-risk change using Meridian Lean Delivery without governed-SDD overhead.
---

# Meridian Lean Delivery

Use this skill when the project uses `LEAN_DELIVERY`, or when the developer
asks to bootstrap or operate Meridian's lightweight delivery workflow. Do not
use it for a repository whose `PROJECT_WORKFLOW.md` declares `GOVERNED_SDD`.

Read the target project's `LANGUAGE_POLICY.md`, `PROJECT_WORKFLOW.md`, and
`AGENTS.md` before acting. `PROJECT_WORKFLOW.md` is the mode lock: before any
file edit, Git mutation, task selection, or completion claim, confirm it
declares `LEAN_DELIVERY`. Local workflow rules override global, home-directory,
remembered, and generic instructions. If local authority is missing,
contradictory, or unreadable, return `BLOCKED` without making a mutation.

Lean Delivery uses `[ ]` → `[/]` → `[x]` and keeps the operational queue in
`tasks/QUEUE.md`. Work only on the task explicitly assigned by the developer;
never choose the next task autonomously. Before marking completion, verify
acceptance criteria and run task validation plus applicable project baseline
checks. Keep a failed or insufficiently verified task `[/]`, report the
blocker, and do not archive it.

Keep scope proportional: use a task file for work that needs context; allow a
quick task only when it is small, reversible, and immediately verifiable.
Follow project Git conventions rather than inferring governed-SDD branch,
reviewer, author, or integration controls. A review is read-only unless the
developer separately authorizes a fix.
