# Task 001 — Output bounds belong in the command string

> **ID**: `001`
> **Category**: Feature (template + migration)
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned

## 🎯 Objective

Change the execution-evidence profile contract so a project records the **complete
literal validation command including its output bound**, instead of a bare command
plus prose asking for concise output.

Highest cost-reduction-per-hour item in the plan. Measured in
`docs/AUDIT_TOKEN_EFFICIENCY.md` (F1b): ~19 KB of command output enters context in
full and the harness backstop sits well above 20 KB, so a typical `cargo test
--workspace` run (5–50 KB) lands whole. Tokens are billed when the tool result
returns and re-sent every turn thereafter, so "expose at most the first 120 lines"
can only govern whether the model *re-prints* them — a rounding error against the
quadratic term.

## 📋 Acceptance Criteria

- [x] `EXECUTION_EVIDENCE_PROFILE.md` asks for the literal command string including
      its output bound, and states why a bare command plus a prose bound does not work.
- [x] The template stays **stack-agnostic**: it states the contract and the shell
      mechanics, and names no language, build tool, or test runner.
- [x] The exit-status rule is explicit — `set -o pipefail` (or `${PIPESTATUS[0]}`)
      with a note on why a pipeline otherwise reports success.
- [x] The project chooses its own bound value; the template does not prescribe a
      line count.
- [x] Per-stack worked examples land in `WORKFLOW_GUIDE.md` (repo documentation,
      not copied into projects), not in the template.
- [x] `CONTEXT_BUDGET_POLICY.md`'s "use the profile's concise success-output form"
      becomes "run the profile's literal declared command string; do not run the bare
      command and summarize afterwards."
- [x] A `migrations/021-*.json` record exists, following `020-reasoning-budget-contract.json`'s shape.
- [x] `python3 -m unittest discover -s tests -v` passes.
- [x] `python3 scripts/check_repository.py` passes.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Contract to change. |
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | "Execution evidence discipline" wording. |
| `WORKFLOW_GUIDE.md` | Per-stack worked examples. Repo documentation, not shipped into projects. |
| `migrations/021-*.json` | New migration record. |
| `migrations/020-reasoning-budget-contract.json` | Shape to copy. |

## 🧩 Technical Context

- **Current behavior**: the profile collects `[commands]` and separately asks for a
  "concise success-output form"; the failure section says "expose at most the first
  120 lines". None of this binds at the point the tokens are billed.
- **Desired behavior**: the command string itself truncates, so bounded output is
  the only output that ever enters the context.

## 🔨 Suggested Implementation

1. Rewrite the profile's "Successful validation output" section around a literal
   command string, in the neutral shape the template must use:

   ```bash
   set -o pipefail
   <project validation command> 2>&1 | tail -<project-chosen bound>
   ```

2. Amend `CONTEXT_BUDGET_POLICY.md`.
3. Add per-stack worked examples to `WORKFLOW_GUIDE.md`, outside `templates/`.
4. Write the migration record.

## ⚠️ Constraints and Considerations

- **`set -o pipefail` is not optional.** A bare `cargo test … | tail -40` returns
  *`tail`'s* exit status, always 0. That silently defeats the profile's own
  "Preserve each command and its exit status" and `CODE_REVIEW_PROMPT.md`'s rule
  against accepting a validation claim without a command/exit-status behind it.
  Shipping without it makes every future failing validation look green. Where a
  shell lacks `pipefail`, capture `${PIPESTATUS[0]}` explicitly.
- **Do not put a language, build tool, or test runner into any file under
  `templates/`.** The profile's own opening sentence declares it the application of a
  "stack-agnostic" discipline, and today the only stack name anywhere in `templates/`
  is a fill-in hint in `TECH_DESIGN.md`. `set -o pipefail` and `| tail -N` are *shell*
  mechanics and belong in the template; `cargo`, `npm` and `pytest` do not. If an
  example seems necessary to make the contract clear, use a `<placeholder>` in the
  template and put the real example in `WORKFLOW_GUIDE.md`.
- Validation **coverage** must not change. Only the volume entering context does.
- Documentation-only diff: skip the full build/test/lint suite per the
  validation-scoping rule, but the two checks listed above do apply (they cover
  `migrations/`).

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/001-output-bounds-in-command.md)"$'\n\nExecute this task in the current project.'
```
