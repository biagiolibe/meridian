# Task 008 — Retire `role-scoped-agent-rules`

> **ID**: `008`
> **Category**: Refactor (capability retirement)
> **Priority**: 🟢 P3
> **Estimate**: ~1h
> **Assigned to**: unassigned

## 🎯 Objective

Remove the `role-scoped-agent-rules` capability from `CONTEXT_BUDGET_POLICY.md` and
every asset carrying it. First real exercise of task 007's retirement path.

## 📋 Acceptance Criteria

- [ ] The capability block is gone from every managed path.
- [ ] A `migrations/NNN-*.json` record uses task 007's `removes` field.
- [ ] Running `meridian upgrade` on a fixture project removes the block cleanly and
      leaves a locally modified copy untouched with a reported conflict.
- [ ] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 🧩 Technical Context

`docs/AUDIT_TOKEN_EFFICIENCY.md` F5. Under Claude Code's `CLAUDE.md` auto-injection
the file enters the session in full before the rule is ever read, so it saves nothing
for `CLAUDE.md`.

The rule is not target-less — `AGENTS.md` survives task 004 as the source of truth and
is 29 KB in Palimpsest, so a harness loading it by explicit read could in principle
use it. **The case for retiring it is reliability, not absence of a target**: its own
closing clause ("if the mapping is otherwise unclear, read the whole file instead")
means it degrades to the unoptimized behavior under exactly the conditions where a
session is least sure what it is reading. A conditional saving that vanishes under
uncertainty, costing ~1.4 KB of always-loaded policy text, is a bad trade.

## ⚠️ Constraints and Considerations

- If task 007's retirement path cannot handle this case cleanly, that is a finding
  against 007 — report it rather than hand-editing the templates.

## 🔗 Dependencies

- **Depends on**: 004, 007
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/008-retire-role-scoped-rules.md)"$'\n\nExecute this task in the current project.'
```
