---
description: "Crea un nuovo task file Meridian numerato e aggiorna QUEUE.md e PROJECT_PLAN.md"
---

Create a new Meridian task file for this project.

## Steps

1. **Find the next task ID**: Look at the files in `tasks/` (excluding `done/`, `QUEUE.md`, `TASK_BLUEPRINT.md`). Find the highest existing NNN prefix and increment by 1. If no tasks exist yet, start at `001`.

2. **Gather task info** — ask the user:
   - Task title (short, descriptive)
   - Category (Architettura / Feature / Bugfix / Refactor / UI / etc.)
   - Priority (🔴 P1 Bloccante / 🟡 P2 Importante / 🟢 P3 Ottimizzazione)
   - Brief description of the objective and what needs to change

3. **Create the task file** at `tasks/NNN-kebab-title.md` using the template in `tasks/TASK_BLUEPRINT.md`. Fill in:
   - Header metadata (ID, category, priority, date as session reference)
   - Objective section with the description provided
   - Acceptance criteria (derive sensible defaults from the description, user can edit)
   - Leave "Contesto Tecnico" and "Implementazione Suggerita" sections for the user to fill in, but add a comment: `<!-- TODO: add relevant code snippets and file paths -->`

4. **Update `tasks/QUEUE.md`**: Add a new row to the "Coda Attiva" table with status `[ ]`, the new ID, title, priority, and a link to the task file. Update the "Ultimo aggiornamento" date.

5. **Update `PROJECT_PLAN.md`**: Add the task to the appropriate section in "SEZIONE 2 — BACKLOG (Operativo)" with status `[ ]`. Update the "Ultimo aggiornamento" date.

6. **Confirm to the user**: "Task `NNN` created: `tasks/NNN-kebab-title.md`. Fill in the technical context, then delegate with:
   ```bash
   claude "$(cat tasks/NNN-kebab-title.md)"$'\n\nEsegui questo task nel progetto corrente.'
   ```"
