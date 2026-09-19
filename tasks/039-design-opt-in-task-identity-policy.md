# Task 039 — Design an opt-in structured task-identity policy

> **ID**: `039`
> **Category**: Design
> **Priority**: 🟡 P2
> **Estimate**: ~1–2h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Define a project-selectable task-identity policy that lets a milestone-driven
consumer use meaningful IDs such as `M30-INSPECT-001` without imposing that
syntax on projects whose linear `TASK-023` IDs are sufficient. The framework
must retain opaque task IDs as its default and must not make an identifier a
second source of truth for status, dependencies, scope, or priority.

This task is design-only. It decides the declaration location, minimal schema,
semantics, and verification boundary before any template, migration, CLI, or
audit implementation is authorized.

## 📋 Acceptance Criteria

- [ ] A design note at `docs/TASK_IDENTITY_POLICY.md` defines two modes:
      `opaque` (the backwards-compatible default) and one opt-in structured
      milestone mode. It states that a project can opt in without renaming
      historical tasks.
- [ ] The structured mode defines the semantic tuple represented by an ID
      (milestone, workstream, ordinal), a concrete grammar, case rules, and
      how task filename, queue row, branch name, handoff path, review path,
      and budget key derive from the canonical ID. It explicitly distinguishes
      those mechanical derivations from the task record's authoritative status,
      dependencies, scope, and priority.
- [ ] The design selects one declaration location that is project-owned and
      upgrade-safe, identifies the corresponding managed-template pointer (if
      any), and explains how a consumer with a customised queue location is
      resolved without duplicating the declaration.
- [ ] The design states whether the first delivery includes a CLI/audit check.
      If it does, define its exact command, success/failure behaviour, and
      backwards-compatible handling for `opaque` projects. If it does not,
      state the evidence that makes a documentation-only policy sufficient and
      file the mechanical validation as a separately bounded follow-up.
- [ ] The design names the required implementation follow-up task or tasks,
      each with a bounded surface, migration/capability-marker implications,
      and validation. It does not silently create those tasks or implement
      them.
- [ ] The note explains why generic names such as `VERIFY`, `SPIKE`, and
      `PRESENT` remain project-selected workstream labels rather than a
      Meridian-reserved taxonomy.
- [ ] `git diff --check` passes.

## 📁 Relevant Files

| File | Role |
|------|------|
| `PROJECT_WORKFLOW.md` | Defines the generic/project-local precedence and location-extension model. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Candidate managed pointer for an opt-in policy; inspect before proposing a migration. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | Defines the generic `<TASK-ID>` contract that must remain backwards compatible. |
| `scripts/meridian.py` | Resolves task, queue, handoff, review, and budget locations; inspect only if deciding a mechanical check. |
| `hooks/queue-briefing.sh` | Candidate consumer of any opt-in identity diagnostic; do not change in this task. |
| `docs/TASK_IDENTITY_POLICY.md` | New design-note deliverable. |

## 🧩 Technical Context

Palimpsest's local milestone specifications and queue deliberately use IDs
such as `M30-INSPECT-001` and a milestone checkpoint named `M30-VERIFY`.
Those names make its milestone/workstream/slice structure legible, but they
are not Meridian protocol: the generic task blueprint accepts an arbitrary
`<TASK-ID>`, and other consumers legitimately use linear IDs.

The abstraction must therefore be an opt-in project policy, not a parser that
infers architecture from a string. A broad user-supplied regular-expression
language is out of scope for the first design because it would create an
unbounded configuration and diagnostic surface. Prefer one small declared
structured form, with explicit delimiters and token rules, if the evidence
shows mechanical checking is warranted.

## 🔨 Suggested Approach

1. Compare the generic task blueprint and location resolver with Palimpsest's
   milestone queue/spec structure and one linear-ID consumer.
2. Write the design note, selecting the opt-in declaration and an intentionally
   narrow structured grammar; record any unresolved compatibility boundary.
3. Split any template/migration work from any CLI or hook validation work, and
   leave both as follow-ups rather than modifying framework behaviour here.

## ⚠️ Constraints and Considerations

- Keep `TASK-023`, `M30-INSPECT-001`, and every other existing task ID valid.
- Do not require an ADR, milestone, `VERIFY` task, workstream taxonomy, or
  task renaming for a project that chooses `opaque` mode.
- Do not derive lifecycle state, dependencies, scope, priority, review policy,
  or authority from an ID token.
- Do not change templates, migrations, CLI commands, hooks, consumer files,
  or capability baselines in this design task.
- Repository text is English-only.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: any implementation of structured task-identity policy support.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/039-design-opt-in-task-identity-policy.md)"$'\n\nExecute this task in the current project.'
```

