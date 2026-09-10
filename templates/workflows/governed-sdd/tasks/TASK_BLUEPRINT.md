# Task [ID] — [Title]

<!-- MERIDIAN:BEGIN capability=task-blueprint v4 -->
Priority: [P0 / P1 / P2]
Status: QUEUED
Review: REQUIRED
Manual verification: [none / required]
Dependencies: [none / TASK-ID, ...]
Reasoning: [low / medium / high / xhigh]
Reasoning justification: [required for high; for xhigh, include the developer's explicit authorization; omit for low/medium]
Diagnostic attempts: [optional; overrides the profile's default cap]
Evidence captures: [optional; overrides the profile's default cap]
Context expansions: [optional; overrides the profile's default cap]

`Reasoning` is this task's exact permitted runtime cap, not a minimum or a
suggestion. Before implementation, remediation, or review, the worker's
configured reasoning effort must equal this value. A mismatch requires a fresh
session configured at the declared value; a worker must never raise its effort
automatically. See `docs/CONTEXT_BUDGET_POLICY.md` for the preflight rule.

`Diagnostic attempts`, `Evidence captures`, and `Context expansions` are
optional per-task caps; omit any of them to inherit
`docs/EXECUTION_EVIDENCE_PROFILE.md`'s default. Each is a cap, not a target:
exhausting it requires `BLOCKED`, not a silently raised cap. Setting one
above the profile's default requires a one-line rationale in this task, the
same way `Reasoning justification` documents `high`/`xhigh`.

## Authority

- [Path to ADR/specification that governs this task.]

## Goal

[Concrete outcome.]

## Expected code surface

- Add or change: [exact module, file, documentation path, or bounded component.]
- Preserve: [interfaces, invariants, and adjacent areas that must not change.]
- Evidence needed: [tests, checks, manual inspection, or handoff evidence.]

## Out of scope

[Adjacent work that must not be implemented.]

## Acceptance criteria

- [Measurable observable outcome.]
- [Measurable invariant or test condition.]

## Validation

- `[project validation command]`

## Completion

- For `Review: REQUIRED`, set this task and its queue row to `READY_FOR_REVIEW` only after validation passes.
- For `Review: NOT_REQUIRED`, set this task and its queue row to `ACCEPTED` only after validation passes.
<!-- MERIDIAN:END -->
