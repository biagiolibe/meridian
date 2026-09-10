# Task 013 — Evidence tiers and a routing rule for `Manual verification`

> **ID**: `013`
> **Category**: Feature (template + migration)
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned

## 🎯 Objective

`Manual verification: required` is free to declare today. Nothing makes the
author ask whether the property could have been asserted as a value instead, so
"it is a UI change" becomes "screenshots", screenshots become an interactive
capture tool, and the session tunes against an image that is evidence for a human
rather than an oracle for a program.

Make the declaration cost one sentence of justification, written against a named
ladder, and check it before the expensive path starts.

## 📋 Acceptance Criteria

- [x] `docs/CONTEXT_BUDGET_POLICY.md` defines the three evidence tiers, in
      stack-agnostic terms, in no more than ten lines.
- [x] `tasks/TASK_BLUEPRINT.md` (`task-blueprint` v6) adds
      `Manual verification rationale:` — mandatory when `Manual verification:
      required`, omitted otherwise — which must name the perceptual criterion no
      tier-1 or tier-2 check can express.
- [x] `manual-verification-precondition` (v3) makes the rationale the **first**
      preflight step, before the probe: if it is missing, or names a property
      that is readable as a value somewhere in the program, return `BLOCKED`
      asking for the task to be re-scoped rather than running the probe.
- [x] `docs/CODE_REVIEW_PROMPT.md` has the reviewer confirm the rationale
      matches the evidence actually gathered.
- [x] A migration record ships it, bundled with task 011 per that task's
      constraint.
- [x] `python3 scripts/check_repository.py` and the CLI suite pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | The tier ladder. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | The new field (currently v5). |
| `templates/workflows/governed-sdd/AGENTS.md` | `manual-verification-precondition` (currently v2). |
| `templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md` | Reviewer check. |
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Add one line asking a project to record how each tier is realized in its stack. |

## 🧩 Technical Context

The ladder, stated so it survives any stack:

1. **Structural** — counts, presence, identity, ordering, spawn/despawn
   invariants. Assertable directly.
2. **Derived value** — any observable the program itself computes and can be
   read back: layout geometry, formatted output, serialized state, a colour held
   as a value, a duration. Assertable once you know where to read it.
3. **Perceptual** — exists *only* in the rendered artifact and nowhere as a
   value: shading, font rendering, visual balance, "does it read correctly".

The boundary is the operative part, and it is a question, not a taxonomy:
**can the property be read as a value, or only perceived as an image?** Tier 3 is
what remains when the answer is genuinely the latter.

**Why this is not covered by the existing budgets.** `Diagnostic attempts`,
`Evidence captures` and the probe precondition all cap how long a wrong activity
runs. None of them changes which activity happens. In the incident that motivated
this queue, the capture budget held — the failure was that the task reached
capture at all, and then a layout problem was tuned against a picture with no
success signal. Budgets bound search; this rule replaces search with convergence.

## ⚠️ Constraints and Considerations

- **Stack-agnostic, without exception.** The ladder names no language, UI
  framework, or capture tool. How a project realizes tier 2 belongs in its own
  `EXECUTION_EVIDENCE_PROFILE.md`, and per-stack worked examples in
  `WORKFLOW_GUIDE.md`.
- Keep it short. This lands in an always-loaded file, and a rule that adds bulk
  to every session to prevent an occasional failure is a bad trade. The ladder
  is a decision the author must make, not an explanation they must read.
- The preflight placement is the whole design. The rationale check must come
  *before* the probe, because the probe is already the cheapest of the expensive
  paths — refusing after it has run saves nothing.
- Do not add a fourth tier or a numeric score. Three named rungs and one
  question is the entire mechanism.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none. A project's tier-2 realization may depend on its own spike;
  that is project work, not this task.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/013-evidence-tiers-and-routing.md)"$'\n\nExecute this task in the current project.'
```
