---
description: "Bootstrap un nuovo progetto con il workflow Meridian (sceglie profilo: generic / game-rust-bevy / web-typescript)"
argument-hint: "[profile]"
---

Initialize a new project with the Meridian agentic development methodology.

The Meridian template source is at: `/Users/biagioliberto/dev/src/meridian/`

## Steps

1. Ask the user for the **project name** (will replace `[Project Name]` / `[Nome del Gioco]` placeholders).

2. Ask the user to choose a **profile**:
   - `generic` — Any software project (language-agnostic)
   - `game-rust-bevy` — Rust game with the Bevy engine
   - `web-typescript` — TypeScript web project (React/Next.js/etc.)

3. Ask the user to choose a **workflow mode**:
   - `classic` — the existing lightweight checkbox queue.
   - `governed-sdd` — ADRs, dependency gates, review policy, task worktrees, and reviewer-led integration.

4. Ask the user for two **language** choices (they can differ, and default to English/same-as-chat if the user has no preference):
   - **Writing language** — the language for docs, code, comments, and commit messages (e.g. English).
   - **Conversation language** — the language the agent should use to talk with the user (e.g. Italian).

5. Copy the following files from the template source to the current working directory:
   - From `templates/base/PROJECT_PLAN.md` → `PROJECT_PLAN.md`
   - From `templates/base/tasks/TASK_BLUEPRINT.md` → `tasks/TASK_BLUEPRINT.md`
   - From `templates/base/tasks/QUEUE.md` → `tasks/QUEUE.md`
   - From `templates/profiles/<chosen-profile>/TECH_DESIGN.md` → `TECH_DESIGN.md`
   - From `templates/base/CLAUDE.md` → `CLAUDE.md`
   - From `templates/base/README.md` → `README.md` (skip if a `README.md` already exists — merge the "Repository & Claude Code Configuration" section into it instead)
   - From `templates/base/.gitignore` → `.gitignore` (merge with an existing `.gitignore` instead of overwriting)
   - From `templates/base/.claudeignore` → `.claudeignore` (merge with an existing `.claudeignore` instead of overwriting)

6. If workflow mode is `governed-sdd`, overlay these files after copying the base/profile templates:
   - `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` → `PROJECT_WORKFLOW.md`
   - `templates/workflows/governed-sdd/AGENTS.md` → `AGENTS.md`
   - `templates/workflows/governed-sdd/CLAUDE.md` → `CLAUDE.md`
   - `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` → `tasks/TASK_BLUEPRINT.md`
   - `templates/workflows/governed-sdd/tasks/QUEUE.md` → `tasks/QUEUE.md`
   - `templates/workflows/governed-sdd/docs/` → `docs/`
   Do not overwrite an existing governed document without showing its diff and receiving explicit confirmation.

7. Replace all occurrences of `[Project Name]` and `[Nome del Gioco]` in the copied files with the actual project name provided in step 1.

8. Replace all occurrences of `[Data]` with today's date in ISO format (YYYY-MM-DD).

9. Create the `tasks/done/` directory (empty, for archiving completed tasks) only in `classic` mode. Governed SDD retains accepted task files as causal project records.

10. In `CLAUDE.md`, fill in the `## Commands` block with the project's actual run/test/lint/format commands, and the `## Conventions` block with any language/stack-specific rules (ask the user if unclear, or infer from the chosen profile's `TECH_DESIGN.md`). Add a **Language** line to `## Conventions` stating the two choices from step 4 explicitly, e.g.: "Code, comments, docs, and commit messages in **English**; conversation with the user in **Italian**."

11. In `README.md`, fill in the "Toolchain" bullet with the pinned language/runtime version and key dependencies, and the "Claude Code — session settings" bullets with the model, advisor, and effort level currently in use for this session (ask the user via `/model`, `/advisor`, `/effort` output if not already known from context).

12. Confirm to the user: "Meridian initialized for **[Project Name]** with profile `<profile>` and workflow `<workflow-mode>`. Next steps:
   - Fill in `TECH_DESIGN.md` with your actual stack details.
   - Add your first features to `PROJECT_PLAN.md`.
   - Run `/meridian-task` when you're ready to delegate the first task."
