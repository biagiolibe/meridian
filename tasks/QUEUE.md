# Task Execution Queue

This is the operational execution queue. Tasks are ordered by priority.

Fully closed phases or sections (all `[x]`) belong in `QUEUE_ARCHIVE.md`, not here.
This file tracks only work with open items, keeping the reading cost low in every
session.

Authority for this queue: [docs/AUDIT_TOKEN_EFFICIENCY.md](../docs/AUDIT_TOKEN_EFFICIENCY.md)
(evidence) and [docs/PLAN_TOKEN_EFFICIENCY.md](../docs/PLAN_TOKEN_EFFICIENCY.md)
(rationale and sequencing).

## How to use this queue

- **Execution**: Take the first available `[ ]` task whose dependencies are `[x]`.
- **Update**: Change `[ ]` to `[/]` when starting and to `[x]` when finishing.
- **Delegation**: Follow the delegation block at the end of each task file.
- **Task-file archive**: When a task is complete, move its file to `tasks/done/`.
- **Queue archive**: When an entire phase becomes `[x]`, move its rows to
  `tasks/QUEUE_ARCHIVE.md` instead of accumulating them here.

## Priorities

| Code | Meaning |
|------|---------|
| 🔴 P1 | Blocking / Critical |
| 🟡 P2 | Important feature |
| 🟢 P3 | Optimization / Polish |

## 🏃 Active Queue

Ordered by return, not by effort. Phase 1 (cost reduction, where the large saving
actually lives) is fully closed — see `tasks/QUEUE_ARCHIVE.md`. Phase 2 is
correctness work that blocks nothing and can slip without cost.

### Phase 2 — Correctness and drift (~1 day)

Little token value on their own; each fixes a rule that does not currently reach the
session meant to obey it. Zero risk, and nothing depends on them.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 003 | Close the probe / escape-hatch composition | 🔴 P1 | — | [003](done/003-probe-escape-hatch.md) |
| `[ ]` | 004 | Generate `CLAUDE.md` from `AGENTS.md` | 🔴 P1 | — | [004](004-generate-claude-md.md) |
| `[ ]` | 005 | Stop instructing sessions to read both files | 🟡 P2 | 004 | [005](005-prompts-read-one-file.md) |

### Phase 3 — The cause

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[ ]` | 010 | A `SPIKE` task class | 🟡 P2 | — | [010](010-spike-task-class.md) |

### Phase 4 — Stop the ratchet

Buys no tokens directly. It is what keeps phases 1–3 from being undone by the next
few upgrades.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[ ]` | 007 | A retirement path for capabilities | 🟡 P2 | — | [007](007-capability-retirement-path.md) |
| `[ ]` | 008 | Retire `role-scoped-agent-rules` | 🟢 P3 | 004, 007 | [008](008-retire-role-scoped-rules.md) |
| `[ ]` | 009 | Bound the queue read | 🟡 P2 | — | [009](009-bound-the-queue-read.md) |
| `[ ]` | 011 | Warn about the head/SIGPIPE/pipefail trap in the template | 🟡 P2 | — | [011](011-sigpipe-trap-in-template.md) |

`011` must not ship as a standalone version bump: release it with whichever
template change lands first, so an adopting project upgrades once rather than
twice. See its Constraints for why bundling *records* is not what saves the
reconciliation.

## 🧪 Quick Tasks (No File)

| Status | Description | Priority |
|--------|-------------|----------|
| `[ ]` | Decide the fate of the one remaining uncommitted working-tree edit (`AGENTS.md`'s change-summary line) — see the standing caution in `docs/PLAN_TOKEN_EFFICIENCY.md`. It is task 004's proof case for the `AGENTS.md`/`CLAUDE.md` asymmetry; do not hand-mirror it. The other two edits are resolved: task 001 shipped the output-bound rewrite and task 002 filled the `[policy]` placeholder with a default number. | 🟡 P2 |

## ✅ Archived (Completed)

| Status | ID | Title | File |
|--------|----|-------|------|
| `[x]` | 001 | Output bounds belong in the command string | [001](done/001-output-bounds-in-command.md) |
| `[x]` | 002 | Ship default numeric budgets, not empty brackets | [002](done/002-default-numeric-budgets.md) |
| `[x]` | 006 | Budget state, CLI, and hook echo | [006](done/006-budget-cli-and-hook.md) |
| `[x]` | 003 | Close the probe / escape-hatch composition | [003](done/003-probe-escape-hatch.md) |

Phase 1 (001, 002, 006) is fully closed and moved to `tasks/QUEUE_ARCHIVE.md`;
this table keeps a flat completed-task index across both files.

*Last updated: 2026-09-10*
