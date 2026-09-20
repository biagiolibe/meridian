# Task 044 — Distribute the governed-SDD host-impact task declaration

> **ID**: `044`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned

## Objective

Distribute the Task 043 `Host impact` declaration to new governed-SDD task
records without changing lifecycle enforcement yet.

## Host impact

Classification: REQUIRED
Policy outcome: New governed-SDD tasks declare whether a change can affect a
host contract before they claim profile-specific behavior.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Claude Code plugin session | advisory | advisory | Consumer upgrades the managed task blueprint. | Existing task contract remains valid. |
| Codex project session | advisory | advisory | Consumer upgrades the managed task blueprint. | Existing task contract remains valid. |

Evidence plan:
- Static: managed-template and migration tests cover the declaration shape.
- Host execution: no enforced host adapter is claimed by this task.
- Manual activation: not required; completion retains `advisory` for both profiles.

## Acceptance Criteria

- [ ] The governed-SDD task blueprint contains the `NOT_APPLICABLE` and
      `REQUIRED` shapes defined by `docs/HOST_IMPACT_GATE_DESIGN.md`.
- [ ] Routed implementation guidance explains the classification and directs a
      host-sensitive task to stop when required evidence cannot be obtained.
- [ ] A next-contiguous migration distributes every changed managed file,
      preserves unmodified consumer customizations, and is listed by managed
      file enumeration.
- [ ] Capability-marker baselines and generated artifacts remain consistent.
- [ ] Template and migration tests prove both shapes are present after a clean
      governed-SDD upgrade.
- [ ] Applicable repository validation and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/HOST_IMPACT_GATE_DESIGN.md` | Accepted declaration and evidence contract. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | Managed declaration source. |
| `templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md` | Routed worker guidance. |
| `migrations/` | Managed consumer distribution record. |
| `scripts/meridian.py` | Managed-file enumeration and migration behavior. |
| `tests/test_meridian_cli.py` | Template and clean-upgrade coverage. |

## Constraints

- Do not add lifecycle parsing or block task execution; that is Task 045.
- Do not rewrite historical consumer task records.
- Preserve `NOT_APPLICABLE` as a compact rationale-only path.
- Do not claim host enforcement merely because a managed task template exists.

## Dependencies

- **Depends on**: Task 043.
- **Blocks**: Task 045.
