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

Ordered by return, not by effort. Phases 1, 2, 2b, 3, 3b, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 22, 25, 26, 27, 28, 31, 32, 34, 35, 36, 42, 44, 45, 46, and 47
are fully closed — see `tasks/QUEUE_ARCHIVE.md`.

### Phase 50 — Interrupted task recovery

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 133 | Let a confirmed Resume reach a dirty task worktree | 🟡 P2 | — | [133](133-resume-dirty-task-worktree.md) |

### Phase 51 — Context cost

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 134 | Add `meridian context size` to measure the startup read set | 🟡 P2 | — | [134](done/134-context-size-command.md) |
| `[x]` | 135 | Report measured token usage of agent sessions | 🟡 P2 | — | [135](done/135-session-usage-report.md) |
| `[x]` | 136 | Load workflow context by phase and point agents to bounded readers | 🟡 P2 | 134, 135 | [136](done/136-per-phase-context-loading.md) |
| `[ ]` | 137 | Tell Codex agents to wait once for long commands | 🟡 P2 | — | [137](137-codex-wait-guidance-for-long-commands.md) |
| `[ ]` | 138 | Run the unit suite in parallel without changing what it covers | 🟡 P2 | — | [138](138-parallel-test-runner.md) |
| `[x]` | 139 | Make `check_repository.py` catch managed-copy digest drift | 🟡 P2 | — | [139](done/139-check-managed-copy-digest-drift.md) |
| `[ ]` | 141 | Count cached input in the Claude Code usage report | 🟡 P2 | — | [141](141-usage-report-claude-input-total.md) |

### Phase 52 — Consumer conformance (Palimpsest report)

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 142 | Recognize spike rows at stage and require `git diff --check` at finalize | 🔴 P1 | — | [142](done/142-stage-spike-rows-and-diff-check.md) |
| `[x]` | 143 | Make the read-guard and queue-briefing hooks independent of queue status | 🔴 P1 | — | [143](done/143-hooks-derive-task-state-from-worktree.md) |
| `[x]` | 144 | Add `.meridian/project.json` as the project declaration surface | 🟡 P2 | — | [144](done/144-project-declaration-file.md) |
| `[x]` | 145 | Align Governed lifecycle capability text with the closure design and the CLI | 🔴 P1 | 142, 143, 144 | [145](done/145-governed-lifecycle-text-alignment.md) |
| `[ ]` | 146 | Restructure inline markers, audit managed copies, and add consumer profiles | 🟡 P2 | 145 | [146](146-marker-structure-audit-and-consumer-profiles.md) |
| `[x]` | 147 | Isolate setup CLI tests from the developer's real home directory | 🔴 P1 | — | [147](done/147-isolate-setup-tests-from-real-home.md) |
