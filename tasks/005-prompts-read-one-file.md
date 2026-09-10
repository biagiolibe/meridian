# Task 005 — Stop instructing sessions to read both agent-rules files

> **ID**: `005`
> **Category**: Bugfix (CLI)
> **Priority**: 🟡 P2
> **Estimate**: ~20min
> **Assigned to**: unassigned

## 🎯 Objective

The assisted-adoption and assisted-reviewer prompts both instruct a session to read
`PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md`. After task 004, `CLAUDE.md` is a
generated pointer. Name `AGENTS.md` only.

## 📋 Acceptance Criteria

- [ ] `scripts/meridian.py:548` and `:607` no longer list both files.
- [ ] No other prompt string in `scripts/meridian.py` still lists both.
- [ ] `python3 -m unittest discover -s tests -v` passes; any test asserting the old
      prompt text is updated.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Lines 548 and 607, plus any sibling prompt. |
| `tests/test_meridian_cli.py` | Prompt assertions. |

## 🧩 Technical Context

Roughly 9 KB off every assisted migration and review session
(`docs/AUDIT_TOKEN_EFFICIENCY.md` F10).

## ⚠️ Constraints and Considerations

- Verify with a grep that no third call site exists before declaring done.

## 🔗 Dependencies

- **Depends on**: 004
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/005-prompts-read-one-file.md)"$'\n\nExecute this task in the current project.'
```
