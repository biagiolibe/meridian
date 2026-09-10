# Task 002 — Ship default numeric budgets, not empty brackets

> **ID**: `002`
> **Category**: Feature (template + migration)
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned

## 🎯 Objective

Replace the execution-evidence profile's `[policy]` placeholders with **default
numbers** a project inherits without configuring anything, and add matching optional
per-task override fields to the task blueprint.

## 📋 Acceptance Criteria

- [x] The existing uncommitted line `Diagnostic-attempt budget and the condition
      that requires `BLOCKED`…: `[policy]`` is **filled in, not replaced**. The field
      is already right; only its emptiness is wrong.
- [x] `CONTEXT_BUDGET_POLICY.md`'s "unbounded parameter changes" wording is amended
      to point at the declared budget, so the prose rule and the number refer to the
      same thing.
- [x] The profile declares defaults: `Diagnostic attempts: 3`, `Evidence captures: 2`,
      `Context expansions: 2`, each with a one-line definition of what counts as one.
- [x] Raising a default requires a recorded rationale, in the same shape `Reasoning`
      already uses.
- [x] `TASK_BLUEPRINT.md` gains optional per-task override fields for the same three.
- [x] The text states plainly that these are caps, not targets, and that exhaustion
      requires `BLOCKED` rather than a raised cap.
- [x] A `migrations/022-*.json` record exists.
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Placeholders to replace. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | Per-task override fields. |
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | The "unbounded" wording that this task gives a number to. |
| `migrations/022-*.json` | New migration record. |

## 🧩 Technical Context

The audit's central evidence (`docs/AUDIT_TOKEN_EFFICIENCY.md` F1): in the incident
project, **every budget expressed as a number was respected and every budget
expressed as a sentence was violated**. The controls that would have covered the
gaps did not exist there at all.

- **Current behavior**: `Diagnostic-attempt budget…: [policy]`. A placeholder
  inherits nothing — a project that never fills it has no bound, which is exactly
  the incident's condition.
- **Desired behavior**: an unconfigured project still inherits a working bound.

`Reasoning` is the existing precedent to imitate: the framework already establishes
that a declared task field is an exact permitted runtime value, not a suggestion.

## 🔨 Suggested Implementation

1. Replace the three placeholders with defaults plus definitions.
2. Add the rationale-to-raise rule.
3. Add the blueprint override fields.
4. Write the migration record.

## ⚠️ Constraints and Considerations

- **This task makes the number exist; it does not enforce it.** Enforcement is task
  006. Shipping 002 alone is still worth it — a number in front of a model performs
  very differently from a sentence — but do not describe it as enforcement in the
  completion report.
- Pick defaults that are generous enough not to fire on healthy work. A false
  positive in week one is how a control gets disabled.
- Three edits sit uncommitted in the working tree from before this queue existed.
  Two of them are this task's raw material, not obstacles: the profile's `[policy]`
  field is the line to fill, and `CONTEXT_BUDGET_POLICY.md`'s test-and-tune paragraph
  is the principle the number implements. Do not delete either and start over.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 006

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/002-default-numeric-budgets.md)"$'\n\nExecute this task in the current project.'
```
