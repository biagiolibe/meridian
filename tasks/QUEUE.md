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
| `[x]` | 156 | Stop `release.py` passing `--repo` to `gh api` | 🟡 P2 | — | [156](done/156-release-verify-gh-api-repo-flag.md) |
| `[x]` | 157 | Stop `handoff-check` requiring one hard-coded Meridian test as the only valid skip | 🟡 P2 | — | [157](done/157-handoff-check-validation-skips-not-project-specific.md) |
| `[x]` | 158 | Migrate legacy budget state only at upgrade, never from a read | 🔴 P1 | — | [158](done/158-budget-state-migration-only-at-upgrade.md) |
| `[x]` | 159 | Retire the reasoning budget contract | 🔴 P1 | — | [159](done/159-retire-reasoning-budget-contract.md) |
| `[x]` | 160 | Give the Claude Code allowlist parity with the Codex execution-command rules | 🟡 P2 | — | [160](done/160-claude-allowlist-execution-commands.md) |
| `[x]` | 161 | State that a local `main` ahead of `origin/main` does not block integration | 🟡 P2 | — | [161](done/161-state-main-ahead-of-origin-is-allowed.md) |
| `[ ]` | 170 | Require a declared validation ID for every command that proves a criterion | 🟡 P2 | — | [170](170-declare-validation-id-for-every-proving-command.md) |

### Phase 54 — Stops and denials

Authority: [docs/ADR_STOPS_AND_DENIALS.md](../docs/ADR_STOPS_AND_DENIALS.md). 162–167 ship in the unreleased 1.2.9 with 161; 168 and 169 follow in the next release.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 162 | Add the stop-code registry and emit closure stops through it | 🟡 P2 | — | [162](done/162-stop-code-registry-and-closure-codes.md) |
| `[x]` | 163 | Check that managed text and tests agree with the stop-code registry | 🟡 P2 | 162 | [163](done/163-check-stop-codes-against-registry.md) |
| `[ ]` | 164 | State the stop and denial rules in the managed workflow text | 🟡 P2 | 161, 163 | [164](164-state-stop-and-denial-rules-in-managed-text.md) |
| `[x]` | 165 | Install the deny list as host permission rules | 🟡 P2 | — | [165](done/165-host-deny-rules-for-denied-actions.md) |
| `[x]` | 166 | Give codes and actionable messages to the execution and handoff gates | 🟡 P2 | 162 | [166](done/166-coded-actionable-execution-and-handoff-gates.md) |
| `[x]` | 167 | Make the execution preflight satisfiable during remediation | 🔴 P1 | 166 | [167](done/167-satisfiable-execution-preflight-during-remediation.md) |
| `[ ]` | 168 | Report queue sections that archival cannot read | 🟡 P2 | 162 | [168](168-report-unarchivable-queue-sections.md) |
| `[ ]` | 169 | Code the remaining gates and require every stop to carry a code | 🟡 P2 | 163, 166 | [169](169-code-remaining-gates-and-require-coded-stops.md) |

### Phase 55 — Closure flow and measurement

Authority: follow-up designs in [docs/ADR_STOPS_AND_DENIALS.md](../docs/ADR_STOPS_AND_DENIALS.md) and Decision 5 of [docs/TASK_CLOSURE_DESIGN.md](../docs/TASK_CLOSURE_DESIGN.md). 171–175 change only the CLI and hooks; 176 changes managed text after 164.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 171 | Record lifecycle command results in a local journal | 🟡 P2 | — | [171](171-lifecycle-journal.md) |
| `[ ]` | 172 | Add `meridian report flow` over the lifecycle journal | 🟡 P2 | 171 | [172](172-report-flow-command.md) |
| `[ ]` | 173 | Detect `BLOCKED` reports that no command emitted | 🟡 P2 | 171 | [173](173-detect-unbacked-blocked-reports.md) |
| `[ ]` | 174 | Add `meridian worktree advance` to drive closure through its mechanical steps | 🟡 P2 | 171 | [174](174-worktree-advance-driver.md) |
| `[ ]` | 175 | Let `advance` finalize from supplied candidate validation results | 🟡 P2 | 174 | [175](175-advance-through-candidate-validation.md) |
| `[ ]` | 176 | Replace the closure procedure in managed text with `advance` | 🟡 P2 | 164, 175 | [176](176-closure-text-uses-advance.md) |
| `[ ]` | 177 | Add an agent evaluation harness graded on the journal and Git state | 🟡 P2 | 171 | [177](177-agent-eval-harness.md) |
| `[ ]` | 178 | Add the safety and remediation scenarios and run them before template-changing releases | 🟡 P2 | 177, 167 | [178](178-agent-eval-scenarios-and-release-gate.md) |
