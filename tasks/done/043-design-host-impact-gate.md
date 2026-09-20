# Task 043 — Design the host-impact task contract and completion gate

> **ID**: `043`
> **Category**: Design
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: Codex

## Objective

Define the minimum task-record contract and lifecycle checks that prevent a
host-sensitive Meridian change from being presented as cross-host enforcement
without profile-specific activation and execution evidence.

This task is design-only. It must choose the declaration shape, applicability
rule, evidence states, and bounded implementation follow-ups before any
template, migration, CLI, hook, or consumer change is authorized.

## Acceptance Criteria

- [x] `docs/HOST_IMPACT_GATE_DESIGN.md` specifies a compact task-record
      shape for both host-impact and not-applicable work.
- [x] The design defines the supported profile identity, permitted adapter
      states, activation preconditions, evidence required to claim
      `enforced`, and the advisory-safe fallback.
- [x] The design selects a first implementation boundary that avoids trying
      to infer host impact from arbitrary source diffs.
- [x] The design names bounded follow-up work for template/migration and
      lifecycle validation, without creating or implementing it.
- [x] The design reconciles current Claude and Codex evidence without
      promoting an untested profile to `enforced`.
- [x] `git diff --check` passes.

## Completion Notes

The design selects an explicit task declaration for every governed-SDD task,
with a compact rationale-only path for ordinary work and a profile/evidence
matrix only for host-sensitive work. The first implementation validates durable
declarations rather than attempting unreliable diff inference or automatic
host probes. On 2026-09-20 the developer completed the external Codex
activation probe: a trusted Palimpsest session denied `cat` of a 401-line
`/private/tmp` file before execution, so that profile is now `enforced`.

## Relevant Files

| File | Role |
|------|------|
| `docs/HOST_CAPABILITY_CONTRACT.md` | Existing host-profile evidence and states. |
| `tasks/TASK_BLUEPRINT.md` | Future generic task contract surface. |
| `PROJECT_WORKFLOW.md` | Lean Delivery lifecycle and completion boundary. |
| `tasks/done/040-codex-command-approval-rules-template.md` | Codex approval evidence. |
| `tasks/done/041-codex-read-guard-hook.md` | Codex hook evidence. |
| `tasks/done/042-codex-external-read-guard-paths.md` | External-path regression evidence. |

## Constraints

- Keep the default no-impact declaration short; do not require host probes for
  ordinary product or documentation work.
- Do not make task status, dependency, scope, or priority depend on a host.
- Do not infer host impact solely from a diff in the first implementation.
- Do not claim marketplace, plugin, or runtime profiles that lack a recorded
  host-session probe.
- Repository text is English-only.

## Dependencies

- **Depends on**: none.
- **Blocks**: implementation of a mandatory host-impact task contract.
