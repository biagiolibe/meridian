# Task [ID] — [Title]

<!-- MERIDIAN:BEGIN capability=task-blueprint v7 -->
Priority: [P0 / P1 / P2]
Status: QUEUED
Review: REQUIRED
Class: [omit for a normal task / SPIKE]
Manual verification: [none / required]
Manual verification rationale: [mandatory when Manual verification: required, omitted otherwise; name the tier-3 (perceptual) property that no tier-1 (structural) or tier-2 (derived-value) check can express — see docs/CONTEXT_BUDGET_POLICY.md's evidence tiers]
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

`Manual verification rationale` is checked before the evidence-availability
probe, not after: a missing rationale, or one naming a property assertable at
tier 1 or tier 2, returns `BLOCKED` asking for the task to be re-scoped as a
deterministic check instead.

`Diagnostic attempts`, `Evidence captures`, and `Context expansions` are
optional per-task caps; omit any of them to inherit
`docs/EXECUTION_EVIDENCE_PROFILE.md`'s default. Each is a cap, not a target:
exhausting it requires `BLOCKED`, not a silently raised cap. Setting one
above the profile's default requires a one-line rationale in this task, the
same way `Reasoning justification` documents `high`/`xhigh`.

## Spike shape

A `Class: SPIKE` task replaces `Review`, `Goal`, `Expected code surface`, and
`Acceptance criteria` with:

```text
Class:       SPIKE
Question:    [the thing that is not known]
Budget:      [max iterations / max wall time]
Deliverable: an ADR or a documented reference value — not production code
Branch:      throwaway, never merged
```

The branch may contain code needed to answer `Question` — a probe binary, a
reproduction, a benchmark harness. Only the branch is throwaway, not
everything run on it: the constraint is on what gets merged (nothing) and
what ships (the `Deliverable` alone, committed directly to `main`), not on
what the investigation is allowed to execute.

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

- `<validation-id>`: `<complete literal command, including its output bound and exit-status handling>`

Run source/build validation only through `meridian execution validate <TASK-ID>
<validation-id> --project .`. The command is deliberately stored in this task:
the runner executes no agent-supplied shell text and records its exit status in
`.meridian/execution-evidence.json` for the completion handoff.

Before a budgeted diagnostic, capture, or context expansion, record its
specific evidence gap with `meridian execution evidence <TASK-ID>
<diagnostic|captures|expansions> --gap <reason> --project .`. A capture also
requires its acceptance-criterion ID and artifact path; the command consumes
the corresponding cap and stores the durable evidence record.

## Completion

- For `Review: REQUIRED`, set this task and its queue row to `READY_FOR_REVIEW` only after validation passes.
- For `Review: NOT_REQUIRED`, set this task and its queue row to `ACCEPTED` only after validation passes.
- For `Class: SPIKE`, once `Budget` is exhausted or `Question` is answered, whichever comes first, self-administer `PROJECT_WORKFLOW.md`'s spike close-out gate and set this task and its queue row to `ANSWERED` or `INCONCLUSIVE`.
<!-- MERIDIAN:END -->
