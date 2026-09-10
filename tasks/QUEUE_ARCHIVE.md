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

*Archived: 2026-09-10*
