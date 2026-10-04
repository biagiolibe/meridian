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

### Phase 51 — Context cost

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 134 | Add `meridian context size` to measure the startup read set | 🟡 P2 | — | [134](done/134-context-size-command.md) |
| `[x]` | 135 | Report measured token usage of agent sessions | 🟡 P2 | — | [135](done/135-session-usage-report.md) |
| `[x]` | 136 | Load workflow context by phase and point agents to bounded readers | 🟡 P2 | 134, 135 | [136](done/136-per-phase-context-loading.md) |
| `[x]` | 137 | Tell Codex agents to wait once for long commands | 🟡 P2 | — | [137](done/137-codex-wait-guidance-for-long-commands.md) |
| `[ ]` | 138 | Run the unit suite in parallel without changing what it covers | 🟡 P2 | — | [138](138-parallel-test-runner.md) |
| `[x]` | 139 | Make `check_repository.py` catch managed-copy digest drift | 🟡 P2 | — | [139](done/139-check-managed-copy-digest-drift.md) |
| `[x]` | 141 | Count cached input in the Claude Code usage report | 🟡 P2 | — | [141](done/141-usage-report-claude-input-total.md) |

### Phase 53 — Upgrade follow-ups

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 148 | Drop retired markers from project sections carried by a restructure | 🔴 P1 | — | [148](done/148-restructure-drops-retired-markers-from-carried-sections.md) |
| `[x]` | 149 | Warn at upgrade when a markerless managed copy keeps local edits | 🟡 P2 | — | [149](done/149-upgrade-warns-on-edited-markerless-copies.md) |
| `[ ]` | 150 | Publish a `stable` branch so the Claude Code plugin follows releases | 🟡 P2 | — | [150](150-stable-release-branch-for-plugin-updates.md) |
| `[x]` | 151 | Make hook task-state lookups linear and keep the briefing within its timeout | 🔴 P1 | — | [151](done/151-linear-task-state-lookups-for-hooks.md) |
| `[x]` | 152 | Read project declarations from the primary checkout, keep budget state out of it, and state Review's closure authority | 🔴 P1 | — | [152](done/152-project-declaration-review-authority-and-budget-state.md) |
| `[x]` | 153 | Install the completion template here and keep validation commands unchained | 🟡 P2 | — | [153](done/153-completion-template-and-unchained-validation.md) |
| `[x]` | 154 | Retarget migration 062 to 1.2.8 and reject same-version migrations | 🔴 P1 | — | [154](done/154-retarget-migration-062-to-1-2-8.md) |
| `[x]` | 155 | Align capability-profile surfaces at upgrade and keep `upgrade --check` from blocking on them | 🔴 P1 | 154 | [155](done/155-align-profile-surfaces-at-upgrade.md) |
| `[ ]` | 156 | Stop `release.py` passing `--repo` to `gh api` | 🟡 P2 | — | [156](156-release-verify-gh-api-repo-flag.md) |
| `[ ]` | 157 | Stop `handoff-check` requiring one hard-coded Meridian test as the only valid skip | 🟡 P2 | — | [157](157-handoff-check-validation-skips-not-project-specific.md) |
