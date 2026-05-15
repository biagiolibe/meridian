---
description: "Bootstrap un nuovo progetto con il workflow Meridian (sceglie profilo: generic / game-rust-bevy / web-typescript)"
argument-hint: "[profile]"
---

Initialize a new project with the Meridian agentic development methodology.

The Meridian template source is at: `/Users/biagioliberto/dev/src/remote/meridian/`

## Steps

1. Ask the user for the **project name** (will replace `[Project Name]` / `[Nome del Gioco]` placeholders).

2. Ask the user to choose a **profile**:
   - `generic` — Any software project (language-agnostic)
   - `game-rust-bevy` — Rust game with the Bevy engine
   - `web-typescript` — TypeScript web project (React/Next.js/etc.)

3. Copy the following files from the template source to the current working directory:
   - From `templates/base/PROJECT_PLAN.md` → `PROJECT_PLAN.md`
   - From `templates/base/tasks/TASK_BLUEPRINT.md` → `tasks/TASK_BLUEPRINT.md`
   - From `templates/base/tasks/QUEUE.md` → `tasks/QUEUE.md`
   - From `templates/profiles/<chosen-profile>/TECH_DESIGN.md` → `TECH_DESIGN.md`

4. Replace all occurrences of `[Project Name]` and `[Nome del Gioco]` in the copied files with the actual project name provided in step 1.

5. Replace all occurrences of `[Data]` with today's date in ISO format (YYYY-MM-DD).

6. Create the `tasks/done/` directory (empty, for archiving completed tasks).

7. Create a `.claude/CLAUDE.md` in the project root with this content:
   ```markdown
   # [Project Name] — Claude Context

   This project uses the Meridian agentic development workflow.

   - See `PROJECT_PLAN.md` for the backlog and progress.
   - See `TECH_DESIGN.md` for architecture and conventions.
   - See `tasks/QUEUE.md` for the active task queue.
   - Use `/meridian-task` to create a new task file.
   ```

8. Confirm to the user: "Meridian initialized for **[Project Name]** with profile `<profile>`. Next steps:
   - Fill in `TECH_DESIGN.md` with your actual stack details.
   - Add your first features to `PROJECT_PLAN.md`.
   - Run `/meridian-task` when you're ready to delegate the first task."
