# Task 022 — Design a bounded agent-instruction router

> **ID**: `022`
> **Category**: Architecture spike
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: Codex

## Objective

Design a migration path that stops implementation, review, and read-only
sessions from loading a monolithic `AGENTS.md` before the task or request type
is known, while preserving Meridian's workflow guarantees, capability-marker
audit, and conflict-safe upgrades.

## Acceptance Criteria

- [ ] Measure the current template and Palimpsest entry-point sizes and identify
      the marker-bearing workflow sections that cause unconditional loading.
- [ ] Define a compact bootstrap contract and an on-demand routing layout for
      implementation, review, remediation, lifecycle, and read-only work.
- [ ] Define how capability markers, `meridian audit`, and three-way upgrades
      migrate without silently losing a locally customized rule.
- [ ] Record phased implementation tasks, validation, rollout, and rollback
      criteria in a durable spike report.
- [ ] No runtime, workflow, template, or upgrader behavior changes are made by
      this spike.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/AGENTS.md` | Current monolithic Codex entry point. |
| `templates/workflows/governed-sdd/CLAUDE.md` | Current Claude Code entry point. |
| `scripts/meridian.py` | Managed-file, marker-audit, and upgrade implementation. |
| `docs/AUDIT_TOKEN_EFFICIENCY.md` | Existing measured context-cost evidence. |

## Validation

- `git diff --check`
- Confirm the scope is limited to this task, queue state, and its spike report.
- Skip the Python suite: this spike changes only documentation and creates no
  runtime or framework behavior.

## Out of Scope

- Moving any capability marker or changing its text.
- Changing generated project workflow behavior.
- Editing Palimpsest or any other consumer project.
