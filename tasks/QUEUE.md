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

Ordered by return, not by effort. Phases 1, 2, 2b, 3, 3b, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, and 22
are fully closed — see `tasks/QUEUE_ARCHIVE.md`.

### Phase 24 — Review worktree routing correction

Removes contradictory Governed SDD instructions that can send a fresh
reviewer to the primary checkout instead of the task's registered linked
worktree, and migrates the correction to existing adopters.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 064 | Remove the primary-checkout review conflict | 🔴 P1 | 051, 063 | [064](done/064-remove-primary-checkout-review-conflict.md) |

### Phase 23 — Shared task identity resolver

Implements the opt-in identity policy designed by Task 039 as one
host-neutral resolver. Projects remain opaque by default, while structured
milestone adopters gain deterministic task, path, branch, handoff, review, and
budget identities for the worktree lifecycle to consume.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 063 | Implement the task-identity declaration and resolver | 🔴 P1 | 039 | [063](done/063-implement-task-identity-resolver.md) |

### Phase 19 — Proportional integration validation

Removes the unconditional duplicate full-baseline run from task integration.
Validated task evidence is reused when safe; integration defaults to a bounded
gate and escalates to full validation only for explicit or material risk.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 055 | Avoid duplicate full validation during worktree integration | 🔴 P1 | 051 | [055](done/055-avoid-duplicate-full-integration-validation.md) |

### Phase 18 — Codex worktree access

Completes the host-integration side of the isolated-worktree contract: task
worktrees use a shared repository-qualified root, Codex can configure that root
with explicit user consent, and filesystem access remains separate from
protected Git metadata and command policy.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 054 | Configure Codex access for isolated task worktrees | 🔴 P1 | 055 | [054](done/054-configure-codex-worktree-access.md) |

### Phase 16 — Release distribution and adopter updates

Closes the gaps left by Phase 5: plugin version drift, behavior tests missing
from CI, unenforced `protocolVersion`, no defined distribution/update channel
for adopters, and a manual-only release procedure.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 046 | Keep `.claude-plugin/plugin.json` version in sync with `VERSION` | 🔴 P1 | 054 | [046](done/046-sync-plugin-manifest-version.md) |
| `[x]` | 047 | Run the unit test suite in CI | 🔴 P1 | 054 | [047](done/047-run-unit-tests-in-ci.md) |
| `[x]` | 048 | Enforce `protocolVersion` compatibility in the CLI | 🟡 P2 | 015 | [048](done/048-enforce-protocol-version-compatibility.md) |
| `[/]` | 049 | Design the distribution and update channel for adopters | 🟡 P2 | 019 | [049](049-design-distribution-and-update-channel.md) |
| `[ ]` | 050 | Automate the GitHub Release from a version tag | 🟢 P3 | 021, 046, 047 | [050](050-automate-github-release-from-tag.md) |
| `[ ]` | 065 | Rename the marketplace and document the pinned install | 🟡 P2 | 049 | [065](065-rename-marketplace-and-document-pinned-install.md) |
| `[ ]` | 066 | Add `meridian self-check --check-latest` | 🟢 P3 | 049, 050, 065 | [066](066-add-self-check-latest-command.md) |
| `[ ]` | 067 | Enforce the adopter-facing release-notes contract | 🟢 P3 | 049, 050 | [067](067-enforce-release-notes-contract.md) |
| `[ ]` | 068 | Document and test the upgrade support policy | 🟢 P3 | 049 | [068](068-document-and-test-support-policy.md) |
| `[ ]` | 069 | Document Codex install from a tagged checkout | 🟢 P3 | 049 | [069](069-document-codex-install-from-tagged-checkout.md) |

### Phase 17 — Consumer workflow integrity

Fixes found while repairing a consumer's generated entry routers: the upgrade
planner merges templates into generated `AGENTS.md`/`CLAUDE.md`, and tracked
records carry machine-specific absolute paths.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 052 | Make the upgrade planner aware of generated entry routers | 🔴 P1 | 015 | [052](done/052-router-aware-upgrade-planner.md) |
| `[ ]` | 053 | Remove machine-specific absolute paths from tracked records | 🟡 P2 | 054 | [053](053-remove-machine-specific-absolute-paths.md) |

## 🧪 Quick Tasks (No File)

None currently. The three pre-queue uncommitted working-tree edits flagged at
project start are all resolved: task 001 shipped the output-bound rewrite,
task 002 filled the `[policy]` placeholder with a default number, and task 004
committed the `AGENTS.md` change-summary line as its own drift proof case,
then folded it into the regenerated `CLAUDE.md`.

All completed task and phase records are in `tasks/QUEUE_ARCHIVE.md`; this
operational queue contains only non-terminal work.

*Last updated: 2026-09-26*
