# Task 045 — Enforce host-impact declarations at lifecycle gates

> **ID**: `045`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Make `meridian execution preflight` and `ready-check` reject malformed or
incomplete host-impact records after Task 044 has distributed their shape.

## Host impact

Classification: REQUIRED
Policy outcome: A governed-SDD task cannot claim an `enforced` host outcome
without durable profile-specific evidence.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Host-neutral Meridian CLI | advisory | enforced | Task 044 declaration is present; the task runs through `meridian execution`. | Preflight returns `BLOCKED` with the missing field or evidence item. |
| Claude Code plugin session | advisory | advisory | The CLI declaration check runs before a task uses the host. | A missing or unverified host probe remains explicit; no host claim is promoted. |
| Codex project session | advisory | advisory | The CLI declaration check runs before a task uses the host. | A missing or unverified host probe remains explicit; no host claim is promoted. |

Evidence plan:
- Static: parser and decision-table tests cover both declaration shapes and every rejection path.
- Host execution: a governed-SDD fixture runs `meridian execution preflight` and `ready-check` with valid and invalid records.
- Manual activation: run the named CLI gates from a project subdirectory; no Claude or Codex runtime claim is changed by this task.

## Acceptance Criteria

- [ ] `execution preflight` requires a non-empty `NOT_APPLICABLE` rationale,
      or a complete `REQUIRED` declaration with profile states, activation
      preconditions, fallback, and all three evidence-plan categories.
- [ ] `ready-check` rejects every `enforced` completion claim that lacks a
      named completion-evidence entry for the same profile.
- [ ] A task may retain `unverified`, `advisory`, or `unsupported` profiles
      without falsely blocking completion when it does not claim enforcement.
- [ ] Failures identify the missing declaration field or profile evidence and
      preserve the existing execution-evidence and handoff semantics.
- [ ] Tests cover valid not-applicable, malformed required, missing enforced
      evidence, retained unverified state, and backwards-compatible handling
      for pre-migration task records as selected by the implementation.
- [ ] Applicable repository validation and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/HOST_IMPACT_GATE_DESIGN.md` | Lifecycle decision and evidence semantics. |
| `scripts/meridian.py` | Preflight and ready-check implementation. |
| `tests/test_meridian_cli.py` | CLI fixture and decision-table coverage. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | Task 044 declaration source. |
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Completion-evidence record format, if an explicit field is needed. |

## Constraints

- Do not infer host impact from arbitrary source diffs.
- Do not require interactive host probes for `NOT_APPLICABLE` work.
- Do not promote a repository test into a Claude or Codex enforcement claim.
- Preserve every existing budget, validation, handoff, and review gate.

## Dependencies

- **Depends on**: Task 044.
- **Blocks**: none.
