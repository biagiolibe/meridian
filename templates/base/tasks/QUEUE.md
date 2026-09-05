# Task Execution Queue

This is the operational execution queue. Tasks are ordered by priority.

Fully closed phases or sections (all `[x]`) belong in
`tasks/QUEUE_ARCHIVE.md`, not here. This file tracks only work with open
items, keeping the reading cost low in every session. Consult the archive
only when the history or rationale of a past phase is needed.

## How to use this queue

- **Execution**: Take the first available `[ ]` task.
- **Update**: Change `[ ]` to `[/]` when starting and to `[x]` when finishing.
- **Task-file archive**: When a task is complete, move its file to `tasks/done/`.
- **Queue archive**: When an entire Active Queue phase or section becomes `[x]`, move its rows to `tasks/QUEUE_ARCHIVE.md` (create it if absent, reusing this file's table structure) instead of accumulating them here. Archive a phase as soon as it closes.

## Priorities

| Code | Meaning |
|--------|-------------|
| 🔴 P1  | Blocking / Critical |
| 🟡 P2  | Important feature |
| 🟢 P3  | Optimization / Polish |

---

## 🤖 How to delegate a task to Claude CLI

```bash
claude "$(cat tasks/NNN-name.md)"$'\n\nExecute this task in the current project.'
```

---

## 🏃 Active Queue

| Status | ID | Title | Priority | Agent | Task File |
|-------|----|--------|----------|--------|-----------|
| `[ ]` | 001 | Initial setup | 🔴 P1 | — | [001](001-setup.md) |

---

## 🧪 Quick Tasks (No File)

Tasks that take less than 15 minutes and do not need a detailed briefing.

| Status | Description | Priority |
|-------|-------------|----------|
| `[ ]` | *(none)* | — |

---

## ✅ Archived (Completed)

| Status | ID | Title | Agent | File |
|-------|----|--------|--------|------|

---

*Last updated: [Date]*
