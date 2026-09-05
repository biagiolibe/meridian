# Task Execution Queue

This is the operational execution queue. Tasks are ordered by priority.

Fully closed phases or sections (all `[x]`) belong in
`tasks/QUEUE_ARCHIVE.md`, not here. This file tracks only work with open
items, keeping the reading cost low in every session. Consult the archive
only when the history or rationale of a past phase is needed.

## How to use this queue

- **Execution**: The developer assigns a specific `[ ]` task; agents do not
  select work autonomously.
- **Update**: Change `[ ]` to `[/]` when starting and to `[x]` only after
  acceptance criteria and stated validation pass.
- **Task-file archive**: When a task is complete, move its file to `tasks/done/`.
- **Queue archive**: When an entire Active Queue phase or section becomes `[x]`, move its rows to `tasks/QUEUE_ARCHIVE.md` (create it if absent, reusing this file's table structure) instead of accumulating them here. Archive a phase as soon as it closes.

## Priorities

| Code | Meaning |
|--------|-------------|
| 🔴 P1  | Blocking / Critical |
| 🟡 P2  | Important feature |
| 🟢 P3  | Optimization / Polish |

---

## 🤖 Delegation prompt

```bash
Proceed with NNN. Read the assigned task and execute only its stated scope.
```

---

## 🏃 Active Queue

| Status | ID | Title | Priority | Agent | Task File |
|-------|----|--------|----------|--------|-----------|
| `[ ]` | 001 | Initial setup | 🔴 P1 | — | [001](001-setup.md) |

---

## 🧪 Quick Tasks (No File)

Tasks that take less than 15 minutes, are reversible, and can be verified
immediately. The row must state its acceptance evidence and validation.

| Status | Description | Priority | Acceptance evidence and validation |
|-------|-------------|----------|------------------------------------|
| `[ ]` | *(none)* | — | — |

---

*Last updated: [Date]*
