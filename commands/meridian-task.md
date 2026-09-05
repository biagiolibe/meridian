---
description: "Create a numbered Meridian task file and update QUEUE.md and PROJECT_PLAN.md"
---

Create a new Meridian task file for this project.

## Workflow-mode gate

First, check whether `PROJECT_WORKFLOW.md` exists. If it does, read that file
and the local `AGENTS.md` or `CLAUDE.md` before taking any action, then follow
the declared mode. Do not apply the Lean Delivery steps below to a
`GOVERNED_SDD` project, or govern a `LEAN_DELIVERY` project by analogy. Global,
home-directory, remembered, or generic workflow instructions cannot override
this local mode lock.

In `GOVERNED_SDD`, assign a stable `TASK-NNN` ID, create the task from
`tasks/TASK_BLUEPRINT.md`, require explicit `Review`, `Dependencies`,
`Reasoning`, authority, expected code surface, non-goals, measurable acceptance
criteria, and validation. Add a `QUEUED` row to `tasks/QUEUE.md`. Do not use
checkbox status, move task files to `done/`, or select a task autonomously.
In `LEAN_DELIVERY`, follow its local task shape and `[ ]` → `[/]` → `[x]`
lifecycle. If the local workflow documents are missing or contradictory,
return `BLOCKED` without changing repository state.

## Steps

1. **Find the next task ID**: Look at the files in `tasks/` (excluding `done/`, `QUEUE.md`, `TASK_BLUEPRINT.md`). Find the highest existing NNN prefix and increment by 1. If no tasks exist yet, start at `001`.

2. **Gather task info** — ask the user:
   - Task title (short, descriptive)
   - Category (Architecture / Feature / Bugfix / Refactor / UI / etc.)
   - Priority (🔴 P1 Blocking / 🟡 P2 Important / 🟢 P3 Optimization)
   - Brief description of the objective and what needs to change

3. **Create the task file** at `tasks/NNN-kebab-title.md` using the template in `tasks/TASK_BLUEPRINT.md`. Fill in:
   - Header metadata (ID, category, priority, date as session reference)
   - Objective section with the description provided
   - Acceptance criteria (derive sensible defaults from the description, user can edit)
   - Leave "Technical Context" and "Suggested Implementation" sections for the user to fill in, but add a comment: `<!-- TODO: add relevant code snippets and file paths -->`

4. **Update `tasks/QUEUE.md`**: Add a new row to the "Active Queue" table with status `[ ]`, the new ID, title, priority, and a link to the task file. Update the "Last updated" date.

5. **Update `PROJECT_PLAN.md`**: Add the task to the appropriate section in "SECTION 2 — BACKLOG (Operational)" with status `[ ]`. Update the "Last updated" date.

6. **Confirm to the user** in the language selected by `LANGUAGE_POLICY.md`: "Task `NNN` created: `tasks/NNN-kebab-title.md`. Fill in the technical context, then delegate with:
   ```bash
   claude "$(cat tasks/NNN-kebab-title.md)"$'\n\nExecute this task in the current project.'
   ```"
