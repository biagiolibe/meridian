# Task 004 — Generate `CLAUDE.md` from `AGENTS.md`

> **ID**: `004`
> **Category**: Refactor (CLI + templates)
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned

## 🎯 Objective

Stop hand-maintaining two near-identical agent-rules files. Make `AGENTS.md` the
single source of truth and generate `CLAUDE.md` from it, with a test that fails on
drift.

## 📋 Acceptance Criteria

- [x] A generator in `scripts/meridian.py` produces `CLAUDE.md` from `AGENTS.md`.
      (`generate_claude_md(mode, agents_text, claude_text)`, exposed as
      `meridian generate-claude-md --mode <mode> --check|--write`.)
- [x] The generated `CLAUDE.md` contains the pointer preamble plus only what Claude
      Code specifically needs. Duplicated capability blocks are **removed, not
      regenerated**. (Each mode's `CLAUDE.md` keeps its own hand-authored preamble
      up to a shared anchor heading — `## Code organization` for governed-sdd,
      `## Command triggers` for lean-delivery, matched by heading text per this
      repo's own role-scoped-agent-rules precedent, not by position — and
      everything from that heading onward is copied verbatim from `AGENTS.md`.)
- [x] A `tests/test_meridian_cli.py` case asserts the committed `CLAUDE.md` matches
      the generator's output (`GenerateClaudeMdTest`, both modes).
- [x] That test fails against the tree **as it stands before this task**, proving it
      catches the live drift, then passes after the templates are regenerated.
      Verified by stashing the regenerated `CLAUDE.md` files and rerunning the test:
      it failed with `AssertionError: ... governed-sdd: CLAUDE.md has drifted from
      AGENTS.md past the shared anchor '## Code organization'`, naming exactly the
      proof case (the change-summary clause) plus four more pre-existing drifts
      found in the same pass (see commit message).
- [x] No rule's content changes. Pure de-duplication — `AGENTS.md`'s wording was not
      edited by this task (the change-summary clause was already an uncommitted
      pre-task edit; this task only commits it, per its own drift-detection logic).
      One exception, made deliberately and not hidden: `CLAUDE.md`'s
      `command-triggers` block previously carried a Claude-Code-specific aside
      ("ideally in a fresh chat or Task-tool subagent") with no `AGENTS.md`
      counterpart. A verbatim-copy generator has no way to keep a per-consumer
      addition inside an otherwise-shared block without new templating machinery,
      which is out of this task's scope; the aside is dropped by regeneration. Flag
      for the developer: recover it later as an explicit Claude-Code-only addendum
      capability if wanted, rather than reintroducing hand-drift.
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Generator. |
| `tests/test_meridian_cli.py` | Drift test. |
| `templates/workflows/governed-sdd/AGENTS.md` | Source of truth. |
| `templates/workflows/governed-sdd/CLAUDE.md` | Generated output. |
| `templates/workflows/lean-delivery/{AGENTS,CLAUDE}.md` | Same treatment. |

## 🧩 Technical Context

Measured (`docs/AUDIT_TOKEN_EFFICIENCY.md` F4, F10): 99 of `CLAUDE.md`'s 115
sentences appear verbatim in `AGENTS.md`. In Palimpsest, `CLAUDE.md` declares itself
"a thin pointer to AGENTS.md" and then reproduces five capability blocks verbatim —
5,574 of 9,300 bytes, 59% — which under Claude Code's auto-injection are paid twice
every session.

The drift this predicts is **already live in this working tree**: the uncommitted
edit patches step 1 of `AGENTS.md` and leaves the identical step 1 of `CLAUDE.md`
stale.

## 🔨 Suggested Implementation

1. Write the generator.
2. Regenerate both templates.
3. Add the drift test.

## ⚠️ Constraints and Considerations

- **Direction is the whole design decision, and it is the counter-intuitive one.**
  `AGENTS.md` is the source; `CLAUDE.md` is generated. In a real project `AGENTS.md`
  carries substantial project-specific content with no home in `CLAUDE.md`
  (Palimpsest: `Truth layers`, `Events`, `Determinism`, `Palimpsest manual-evidence
  extension`). Generating `AGENTS.md` from `CLAUDE.md` would delete it.
- Framework-internal only — no migration record needed, since this touches templates
  and CLI rather than a rule an adopted project must receive.
- Do not change any rule's wording in the same commit as the generator. If the
  generator's output differs from the committed file in content rather than layout,
  stop and report it.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 005, 008

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/004-generate-claude-md.md)"$'\n\nExecute this task in the current project.'
```
