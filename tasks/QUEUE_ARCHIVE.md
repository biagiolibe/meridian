# Task Execution Queue — Archive

Closed phases and sections moved out of `tasks/QUEUE.md` once every row in them is
`[x]`, to keep that file's reading cost low. Mirrors `QUEUE.md`'s own table
structure.

Authority for this queue: [docs/AUDIT_TOKEN_EFFICIENCY.md](../docs/AUDIT_TOKEN_EFFICIENCY.md)
(evidence) and [docs/PLAN_TOKEN_EFFICIENCY.md](../docs/PLAN_TOKEN_EFFICIENCY.md)
(rationale and sequencing).

## Priorities

| Code | Meaning |
|------|---------|
| 🔴 P1 | Blocking / Critical |
| 🟡 P2 | Important feature |
| 🟢 P3 | Optimization / Polish |

### Phase 1 — Cost reduction (~2–3 days)

`001` and `002` are ~2h each and land the same day. `006` is the item that matters:
phases 1–2 of the plan reduce the *size* of each iteration, but only `006` reduces
their *number*, which is the quadratic term.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 001 | Output bounds belong in the command string | 🔴 P1 | — | [001](done/001-output-bounds-in-command.md) |
| `[x]` | 002 | Ship default numeric budgets, not empty brackets | 🔴 P1 | — | [002](done/002-default-numeric-budgets.md) |
| `[x]` | 006 | Budget state, CLI, and hook echo | 🔴 P1 | 002 | [006](done/006-budget-cli-and-hook.md) |

### Phase 2 — Correctness and drift (~1 day)

Little token value on their own; each fixes a rule that does not currently reach the
session meant to obey it. Zero risk, and nothing depends on them.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 003 | Close the probe / escape-hatch composition | 🔴 P1 | — | [003](done/003-probe-escape-hatch.md) |
| `[x]` | 004 | Generate `CLAUDE.md` from `AGENTS.md` | 🔴 P1 | — | [004](done/004-generate-claude-md.md) |
| `[x]` | 005 | Stop instructing sessions to read both files | 🟡 P2 | 004 | [005](done/005-prompts-read-one-file.md) |

### Phase 2b — Found in the field

Not planned from the audit: surfaced while reconciling Palimpsest onto 1.1.19.
Ahead of phase 3 because every adopted project that receives an inline
capability version bump silently accumulates a contradictory pair.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 012 | `append_only_new_markers` treats a version bump as a new capability | 🔴 P1 | — | [012](done/012-marker-supersession.md) |

### Phase 3 — The cause

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 010 | A `SPIKE` task class | 🟡 P2 | — | [010](done/010-spike-task-class.md) |

### Phase 3b — Route work away from manual evidence

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 014 | The `CLAUDE.md` generator altered protected marker content | 🔴 P1 | — | [014](done/014-generator-altered-protected-blocks.md) |
| `[x]` | 013 | Evidence tiers and a routing rule for `Manual verification` | 🔴 P1 | — | [013](done/013-evidence-tiers-and-routing.md) |

`013` shipped together with `011` (Phase 4), per `011`'s bundling constraint,
both in migration `024-evidence-tiers-and-routing` (VERSION `1.1.21`).

### Phase 4 — Stop the ratchet

Buys no tokens directly. It is what keeps phases 1–3 from being undone by the next
few upgrades.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 011 | Warn about the head/SIGPIPE/pipefail trap in the template | 🟡 P2 | — | [011](done/011-sigpipe-trap-in-template.md) |
| `[x]` | 007 | A retirement path for capabilities | 🟡 P2 | — | [007](done/007-capability-retirement-path.md) |
| `[x]` | 008 | Retire `role-scoped-agent-rules` | 🟢 P3 | 004, 007 | [008](done/008-retire-role-scoped-rules.md) |
| `[x]` | 009 | Bound the queue read | 🟡 P2 | — | [009](done/009-bound-the-queue-read.md) |

`011` shipped bundled with `013` (Phase 3b), per its own bundling constraint —
listed here too since it is formally a Phase 4 item.

### Phase 5 — SemVer version split

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|------------|-----------|
| `[x]` | 015 | Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner | 🔴 P1 | 054 | [015](done/015-split-workflow-baseline-version.md) |

Phase 5 remains active; its open tasks stay in `tasks/QUEUE.md`.

### Phase 6 — Agent instruction routing

The framework first made protected capability moves conflict-safe and compacted
its generic entry points. The phase closed only after Palimpsest applied the
release, preserved its customized rules, and supplied measured routed-session
evidence for status/design, implementation, and review.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 023 | Define capability-move and bootstrap-router contract | 🔴 P1 | — | [023](done/023-capability-move-router-contract.md) |
| `[x]` | 024 | Add managed role procedures and move-aware upgrade support | 🔴 P1 | 023 | [024](done/024-additive-role-procedures.md) |
| `[x]` | 025 | Compact entry points and retire duplicate role procedures | 🔴 P1 | 024 | [025](done/025-compact-entry-points.md) |
| `[x]` | 026 | Roll out routing to Palimpsest and measure initial context | 🟡 P2 | 025 | [026](done/026-palimpsest-routing-rollout.md) |

### Phase 7 — Shared consumer entry routers

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 027 | Add generated shared entry-router support | 🔴 P1 | 025 | [027](done/027-generated-entry-router-support.md) |
| `[x]` | 028 | Add routed-read fixtures and adoption audit | 🟡 P2 | 027 | [028](done/028-router-route-fixtures-and-audit.md) |
| `[x]` | 029 | Map and additively extract Palimpsest router procedures | 🟡 P2 | 026, 028 | [029](done/029-palimpsest-router-additive-extraction.md) |
| `[x]` | 030 | Generate compact Palimpsest entry routers and retire copies | 🟡 P2 | 029 | [030](done/030-palimpsest-generated-router-retirement.md) |
| `[x]` | 031 | Publish the consumer router-adoption playbook | 🟢 P3 | 030 | [031](done/031-consumer-router-adoption-playbook.md) |

### Phase 8 — Language-policy salience

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 032 | Add Claude language-policy briefing adapter | 🟡 P2 | — | [032](done/032-language-policy-briefing-adapter.md) |

### Phase 9 — Budget-state integrity

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 033 | `budget_spend()` durably consumes budget before the cap check can reject it | 🔴 P1 | — | [033](done/033-budget-spend-write-before-check.md) |

### Phase 10 — Context-enforcement second pass

Authority: [docs/PROPOSAL_CONTEXT_ENFORCEMENT.md](../docs/PROPOSAL_CONTEXT_ENFORCEMENT.md)
(§3, M1/M2 — highest-yield items of the proposal; independent of each other).

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 034 | Add `meridian adr show` and `meridian context authority` | 🟡 P2 | — | [034](done/034-authority-excerpt-command.md) |
| `[x]` | 035 | `PreToolUse` guard against unranged large-file reads | 🟡 P2 | — | [035](done/035-pretooluse-read-guard.md) |

### Phase 11 — Long-lag consumer upgrade safety

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 036 | Plan capability moves correctly across long-lag consumer upgrades | 🔴 P1 | — | [036](done/036-long-lag-capability-move-upgrades.md) |
| `[x]` | 037 | Let a long-lag consumer stop an upgrade before retirement | 🔴 P1 | 036 | [037](done/037-stop-before-retirement-upgrade.md) |

### Phase 12 — Budget cap semantics

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 038 | Make a budget cap admit exactly `cap` uses | 🟡 P2 | — | [038](done/038-budget-cap-boundary-allows-cap-uses.md) |

### Phase 14 — Codex execution-policy support

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 040 | Ship Codex command-approval rules as a managed governed-SDD template file | 🟡 P2 | — | [040](done/040-codex-command-approval-rules-template.md) |
| `[x]` | 041 | Codex `PreToolUse` read guard, gated by an empirical probe | 🟡 P2 | 040 | [041](done/041-codex-read-guard-hook.md) |
| `[x]` | 042 | Deny over-budget absolute reads outside the project root | 🟡 P2 | 041 | [042](done/042-codex-external-read-guard-paths.md) |

### Phase 15 — Host-impact governance

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 043 | Design the host-impact task contract and completion gate | 🔴 P1 | — | [043](done/043-design-host-impact-gate.md) |
| `[x]` | 044 | Distribute the governed-SDD host-impact task declaration | 🔴 P1 | 043 | [044](done/044-distribute-host-impact-declaration.md) |
| `[x]` | 045 | Enforce host-impact declarations at lifecycle gates | 🔴 P1 | 044 | [045](done/045-enforce-host-impact-lifecycle-gates.md) |

### Phase 17 — Per-task worktree isolation

This phase establishes a dedicated linked worktree as the mandatory execution
boundary for every Lean Delivery and Governed SDD task, with serialized,
non-rewriting final integration.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 051 | Enforce isolated worktrees for every task | 🔴 P1 | — | [051](done/051-enforce-isolated-task-worktrees.md) |

*Last updated: 2026-09-26*
