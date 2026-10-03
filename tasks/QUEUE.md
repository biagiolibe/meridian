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

Ordered by return, not by effort. Phases 1, 2, 2b, 3, 3b, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 22, 25, 26, 27, 28, 31, 32, 34, 35, 36, and 42
are fully closed — see `tasks/QUEUE_ARCHIVE.md`.

### Phase 44 — Hands-off task closure design

Designs how an assigned task runs through implementation, validation,
integration, the required `main` push, and cleanup without stopping for avoidable
reasons, and creates the implementation follow-ups.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 100 | Design hands-off task closure | 🔴 P1 | 088, 097, 099 | [100](done/100-design-hands-off-task-closure.md) |
| `[x]` | 101 | Add `meridian worktree closure-status` | 🟡 P2 | 100 | [101](done/101-closure-status-command.md) |
| `[x]` | 102 | Add the evidence command and recompute main-advance facts in `integrate stage` | 🟡 P2 | 100, 111 | [102](done/102-evidence-command-and-main-advance-facts.md) |
| `[x]` | 103 | Apply queue and plan row status during `integrate stage` | 🟡 P2 | 100, 102 | [103](done/103-apply-queue-and-plan-rows-at-integration.md) |
| `[x]` | 104 | Apply phase archival during `integrate stage` | 🟡 P2 | 100, 103 | [104](done/104-apply-phase-archival-at-integration.md) |
| `[x]` | 105 | Derive `[/]` and show closure stop reasons in the console | 🟡 P2 | 101, 103 | [105](done/105-console-derive-in-progress-and-closure-stops.md) |
| `[x]` | 106 | Narrow the Codex push rule and offer a Claude Code allowlist | 🟡 P2 | 100 | [106](106-narrow-push-rule-and-claude-allowlist.md) |
| `[x]` | 107 | Block `integrate stage` when `main` is behind `origin` and report a pending push | 🟡 P2 | 100, 101 | [107](done/107-block-stage-when-main-behind-origin.md) |
| `[x]` | 108 | Add the `Validation skips` handoff field and its check | 🟡 P2 | 099, 100, 113 | [108](done/108-validation-skips-handoff-field.md) |
| `[x]` | 109 | Ship the Lean Delivery closure rules and migration | 🟡 P2 | 100, 101, 102, 103, 104, 106, 107, 108, 113 | [109](done/109-ship-lean-closure-rules-and-migration.md) |
| `[x]` | 110 | Ship the Governed SDD closure rules and migration | 🟡 P2 | 109, 113, 117 | [110](done/110-ship-governed-closure-rules-and-migration.md) |
| `[x]` | 117 | Make `integrate stage` completion mode-aware for Governed SDD | 🟡 P2 | 103, 104 | [117](done/117-make-stage-completion-governed-aware.md) |
| `[x]` | 118 | Show the running framework version and root in the project console | 🟢 P3 | 105 | [118](done/118-console-show-framework-version.md) |
| `[x]` | 119 | Show task elapsed time and lifecycle progress in the project console | 🟢 P3 | 118 | [119](done/119-console-show-task-elapsed-time-and-progress.md) |
| `[ ]` | 120 | Quiet validation command and foreground rule for long checks | 🟡 P2 | — | [120](120-quiet-validation-command-and-foreground-rule.md) |
| `[ ]` | 121 | Verify mandatory commands in candidate validation evidence | 🟡 P2 | 120 | [121](121-finalize-checks-candidate-validation-commands.md) |
| `[ ]` | 122 | Define the bounded gate per integration outcome | 🟡 P2 | 121 | [122](122-define-bounded-gate-per-integration-outcome.md) |
