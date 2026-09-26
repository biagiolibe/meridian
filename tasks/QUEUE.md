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

Ordered by return, not by effort. Phases 1, 2, 2b, 3, 3b, 4, 6, 7, 8, 9, 10, 11, 12, 14, and 15
are fully closed — see `tasks/QUEUE_ARCHIVE.md`. Phase 5 (SemVer version split) is
new: separates `frameworkVersion` (public CLI release), `workflowBaselineVersion`
(governed template baseline, derived from migrations), and `protocolVersion`
(manifest/CLI compatibility) so a CLI-only release no longer requires a fake
migration.

### Phase 17 — Per-task worktree isolation

This phase is a global prerequisite for all other active work. It makes a
dedicated linked worktree mandatory for each Lean Delivery and Governed SDD
task and replaces the parallel-hostile integration assumptions in the current
Governed SDD contract.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 051 | Enforce isolated worktrees for every task | 🔴 P1 | — | [051](051-enforce-isolated-task-worktrees.md) |

### Phase 5 — SemVer version split

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 015 | Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner | 🔴 P1 | 051 | [015](015-split-workflow-baseline-version.md) |
| `[ ]` | 016 | Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption` | 🔴 P1 | 015 | [016](016-adopt-workflow-baseline-version.md) |
| `[ ]` | 017 | Relax `check_migrations()`'s VERSION equality to `<=` | 🔴 P1 | 015 | [017](017-relax-check-migrations-version-gate.md) |
| `[ ]` | 018 | Persist-time SemVer guard for prerelease `frameworkVersion` | 🟡 P2 | 015 | [018](018-prerelease-version-guard.md) |
| `[ ]` | 019 | `releases/<version>.json` immutable release ledger + `check_releases()` | 🟡 P2 | 017 | [019](019-releases-ledger.md) |
| `[ ]` | 020 | Update docs for the version split | 🟢 P3 | 015, 017, 019 | [020](020-docs-version-split.md) |
| `[ ]` | 021 | Ship the first CLI-only release as end-to-end proof | 🟢 P3 | 016, 018, 019, 020, 046 | [021](021-first-cli-only-release.md) |

### Phase 16 — Release distribution and adopter updates

Closes the gaps left by Phase 5: plugin version drift, behavior tests missing
from CI, unenforced `protocolVersion`, no defined distribution/update channel
for adopters, and a manual-only release procedure.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 046 | Keep `.claude-plugin/plugin.json` version in sync with `VERSION` | 🔴 P1 | 051 | [046](046-sync-plugin-manifest-version.md) |
| `[ ]` | 047 | Run the unit test suite in CI | 🔴 P1 | 051 | [047](047-run-unit-tests-in-ci.md) |
| `[ ]` | 048 | Enforce `protocolVersion` compatibility in the CLI | 🟡 P2 | 015 | [048](048-enforce-protocol-version-compatibility.md) |
| `[ ]` | 049 | Design the distribution and update channel for adopters | 🟡 P2 | 019 | [049](049-design-distribution-and-update-channel.md) |
| `[ ]` | 050 | Automate the GitHub Release from a version tag | 🟢 P3 | 021, 046, 047 | [050](050-automate-github-release-from-tag.md) |

### Phase 13 — Optional structured task identity

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[ ]` | 039 | Design an opt-in structured task-identity policy | 🟡 P2 | 051 | [039](039-design-opt-in-task-identity-policy.md) |

## 🧪 Quick Tasks (No File)

None currently. The three pre-queue uncommitted working-tree edits flagged at
project start are all resolved: task 001 shipped the output-bound rewrite,
task 002 filled the `[policy]` placeholder with a default number, and task 004
committed the `AGENTS.md` change-summary line as its own drift proof case,
then folded it into the regenerated `CLAUDE.md`.

All completed task and phase records are in `tasks/QUEUE_ARCHIVE.md`; this
operational queue contains only non-terminal work.

*Last updated: 2026-09-26*
