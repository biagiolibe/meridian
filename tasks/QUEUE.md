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

Ordered by return, not by effort. Phases 1, 2, 2b, 3, 3b, 4, 6, 8, 9, 10, and 12
are fully closed — see `tasks/QUEUE_ARCHIVE.md`. Phase 5 (SemVer version split) is
new: separates `frameworkVersion` (public CLI release), `workflowBaselineVersion`
(governed template baseline, derived from migrations), and `protocolVersion`
(manifest/CLI compatibility) so a CLI-only release no longer requires a fake
migration.

### Phase 5 — SemVer version split

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 015 | Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner | 🔴 P1 | — | [015](015-split-workflow-baseline-version.md) |
| `[ ]` | 016 | Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption` | 🔴 P1 | 015 | [016](016-adopt-workflow-baseline-version.md) |
| `[ ]` | 017 | Relax `check_migrations()`'s VERSION equality to `<=` | 🔴 P1 | 015 | [017](017-relax-check-migrations-version-gate.md) |
| `[ ]` | 018 | Persist-time SemVer guard for prerelease `frameworkVersion` | 🟡 P2 | 015 | [018](018-prerelease-version-guard.md) |
| `[ ]` | 019 | `releases/<version>.json` immutable release ledger + `check_releases()` | 🟡 P2 | 017 | [019](019-releases-ledger.md) |
| `[ ]` | 020 | Update docs for the version split | 🟢 P3 | 015, 017, 019 | [020](020-docs-version-split.md) |
| `[ ]` | 021 | Ship the first CLI-only release as end-to-end proof | 🟢 P3 | 016, 018, 019, 020 | [021](021-first-cli-only-release.md) |

### Phase 7 — Shared consumer entry routers

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 027 | Add generated shared entry-router support | 🔴 P1 | 025 | [027](done/027-generated-entry-router-support.md) |
| `[x]` | 028 | Add routed-read fixtures and adoption audit | 🟡 P2 | 027 | [028](done/028-router-route-fixtures-and-audit.md) |
| `[ ]` | 029 | Map and additively extract Palimpsest router procedures | 🟡 P2 | 026, 028 | [029](029-palimpsest-router-additive-extraction.md) |
| `[ ]` | 030 | Generate compact Palimpsest entry routers and retire copies | 🟡 P2 | 029 | [030](030-palimpsest-generated-router-retirement.md) |
| `[ ]` | 031 | Publish the consumer router-adoption playbook | 🟢 P3 | 030 | [031](031-consumer-router-adoption-playbook.md) |

### Phase 11 — Long-lag consumer upgrade safety

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 036 | Plan capability moves correctly across long-lag consumer upgrades | 🔴 P1 | — | [036](done/036-long-lag-capability-move-upgrades.md) |
| `[x]` | 037 | Let a long-lag consumer stop an upgrade before retirement | 🔴 P1 | 036 | [037](done/037-stop-before-retirement-upgrade.md) |

## 🧪 Quick Tasks (No File)

None currently. The three pre-queue uncommitted working-tree edits flagged at
project start are all resolved: task 001 shipped the output-bound rewrite,
task 002 filled the `[policy]` placeholder with a default number, and task 004
committed the `AGENTS.md` change-summary line as its own drift proof case,
then folded it into the regenerated `CLAUDE.md`.

## ✅ Archived (Completed)

| Status | ID | Title | File |
|--------|----|-------|------|
| `[x]` | 001 | Output bounds belong in the command string | [001](done/001-output-bounds-in-command.md) |
| `[x]` | 002 | Ship default numeric budgets, not empty brackets | [002](done/002-default-numeric-budgets.md) |
| `[x]` | 006 | Budget state, CLI, and hook echo | [006](done/006-budget-cli-and-hook.md) |
| `[x]` | 003 | Close the probe / escape-hatch composition | [003](done/003-probe-escape-hatch.md) |
| `[x]` | 004 | Generate `CLAUDE.md` from `AGENTS.md` | [004](done/004-generate-claude-md.md) |
| `[x]` | 005 | Stop instructing sessions to read both files | [005](done/005-prompts-read-one-file.md) |
| `[x]` | 012 | `append_only_new_markers` treats a version bump as a new capability | [012](done/012-marker-supersession.md) |
| `[x]` | 010 | A `SPIKE` task class | [010](done/010-spike-task-class.md) |
| `[x]` | 014 | The `CLAUDE.md` generator altered protected marker content | [014](done/014-generator-altered-protected-blocks.md) |
| `[x]` | 013 | Evidence tiers and a routing rule for `Manual verification` | [013](done/013-evidence-tiers-and-routing.md) |
| `[x]` | 011 | Warn about the head/SIGPIPE/pipefail trap in the template | [011](done/011-sigpipe-trap-in-template.md) |
| `[x]` | 007 | A retirement path for capabilities | [007](done/007-capability-retirement-path.md) |
| `[x]` | 008 | Retire `role-scoped-agent-rules` | [008](done/008-retire-role-scoped-rules.md) |
| `[x]` | 009 | Bound the queue read | [009](done/009-bound-the-queue-read.md) |
| `[x]` | 022 | Design a bounded agent-instruction router | [022](done/022-agent-instruction-routing-spike.md) |
| `[x]` | 026 | Roll out routing to Palimpsest and measure initial context | [026](done/026-palimpsest-routing-rollout.md) |
| `[x]` | 033 | `budget_spend()` durably consumes budget before the cap check can reject it | [033](done/033-budget-spend-write-before-check.md) |
| `[x]` | 034 | Add `meridian adr show` and `meridian context authority` | [034](done/034-authority-excerpt-command.md) |
| `[x]` | 035 | `PreToolUse` guard against unranged large-file reads | [035](done/035-pretooluse-read-guard.md) |
| `[x]` | 038 | Make a budget cap admit exactly `cap` uses | [038](done/038-budget-cap-boundary-allows-cap-uses.md) |

Phases 1, 2, 2b, 3, 3b, 4, 6, 8, 9, 10, and 12 (001, 002, 006, 003, 004, 005,
012, 010, 014, 013, 011, 007, 008, 009, 023, 024, 025, 026, 032, 033, 034, 035,
038) are
fully closed and moved to `tasks/QUEUE_ARCHIVE.md`;
this table keeps a flat completed-task index across both files.

*Last updated: 2026-09-19*
