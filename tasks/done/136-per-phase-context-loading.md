# Task 136 — Load workflow context by phase and point agents to bounded readers

> **ID**: `136`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Context-cost analysis of Palimpsest and Meridian, 2026-10-03

## Objective

Governed SDD roles read their whole document set at the start, and the
implementation workflow does not tell the agent to use the bounded readers
(`meridian context authority`, `meridian adr show`) that avoid opening a
921 KB ADR log. Use the measurements from tasks 134 and 135 to cut avoidable
startup reading without weakening any gate: load documents when the phase that
needs them begins, and point agents to the bounded readers.

## Acceptance Criteria

- [x] Before editing, record in the handoff the 134 and 135 figures that justify
  each change (which document, its size, and when the agent needs it). A change
  with no measured justification is not made.
- [x] The Governed SDD implementation and review workflow documents state, per
  document, whether it is read at start or at the phase that needs it (for example
  the completion report template at completion, the code-organization rules when a
  production source change is first planned, the evidence profile before the first
  validation). The set and the order stay deterministic.
- [x] The implementation, review, remediation, and status workflow documents tell
  the agent to read ADRs and specifications through `meridian context authority`
  and `meridian adr show` and never to open the whole ADR log or the whole queue,
  and name the queue briefing as the way to read the queue.
- [x] No acceptance criterion, gate, role, or review rule is removed or relaxed;
  a reviewer can show every gate remains reachable. The change is limited to
  when a document is read and how ADRs are read.
- [x] `meridian context size` (task 134) shows the startup read set of each role
  reduced against the recorded baseline, and the new figures are in the handoff.
- [x] Changes to managed template text are additive or reordering within managed
  capability blocks, follow the capability-marker and migration rules, and the
  release carrying them is template-changing.
- [x] Lean Delivery is measured and reported; it is changed only where task 134 or
  135 shows an avoidable cost, and no change is made speculatively.
- [x] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass, including the
  template ceilings introduced by task 134.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/workflows/*.md` | Phase-based reading instructions. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Router and always-read content. |
| `templates/workflows/lean-delivery/` | Measured only unless justified. |
| `docs/CONTEXT_BUDGET_POLICY.md` and templates | Policy wording. |

## Technical Context

- Palimpsest's implementation and workflow documents do not mention
  `meridian context` or `meridian adr` (searched on 2026-10-03), although the
  commands exist and produced about 18 KB of excerpts for a real task against a
  921 KB log.
- The measured first-call context was 18,000 tokens (Codex, Lean) and 29,000
  (Codex, Governed); most of the growth to a 65,000 to 115,000 token average per
  call happens later in the session, so phase loading is one lever among several.
- Other levers outside this task: fewer model calls per task, bounded tool output
  (task 120), and avoiding polling.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Archiving or truncating a project's queue or ADR log, changing gates or roles,
a new tokenizer, and a Lean Delivery rewrite without measured evidence.

## Dependencies

- **Depends on**: 134, 135
- **Blocks**: none
