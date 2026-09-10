# Task 003 — Close the probe / escape-hatch composition

> **ID**: `003`
> **Category**: Bugfix (capability v2 + migration)
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned

## 🎯 Objective

Fix the clearest single framework defect the incident exposed: two capabilities,
each defensible alone, compose into a hole that let a session keep exploring after
its evidence probe had already failed.

## 📋 Acceptance Criteria

- [x] `manual-verification-precondition` becomes v2 and requires an **executable
      probe that actually succeeds** before implementation, replacing "confirm you
      can produce that evidence".
- [x] The deterministic-test escape hatch is narrowed so it suspends the
      *requirement to capture* but never the *stop on a probe already attempted and
      failed*.
- [x] The new text names the forbidden recovery explicitly: do not respond to a
      failed probe by exploring the local environment for an alternative.
- [x] Every asset carrying the capability is updated (`AGENTS.md`, `CLAUDE.md`;
      `check_repository.py` ties no doc to this specific capability — verified by
      grep, nothing else to update).
- [x] A `migrations/022-*.json` record exists with `capabilityVersion: 2`. (Numbered
      `022`, not `023` as drafted: an external refactor collapsed migrations 021/022
      into one `021-concrete-execution-budgets` before this task started, shifting the
      next free slot down by one.)
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/AGENTS.md` | `manual-verification-precondition` block. |
| `templates/workflows/governed-sdd/CLAUDE.md` | Same block, second copy. |
| `/Users/biagioliberto/dev/src/palimpsest/AGENTS.md` | Source wording to promote upward (`## Palimpsest manual-evidence extension`). Read-only reference. |
| `migrations/023-*.json` | New migration record. |

## 🧩 Technical Context

- Palimpsest's local extension already requires a probe that *actually succeeds* and
  mandates `BLOCKED` if it cannot. The consumer project is ahead of the framework
  here; adopt its wording.
- The framework's `manual-verification-precondition` says a deterministic test may
  serve as primary evidence, making visual confirmation "a secondary check, not the
  only gate" — and its literal example is "a geometry or layout assertion", which is
  precisely the incident's task.
- **Current behavior**: the GPU probe's failure was demoted from a `BLOCKED` trigger
  to a failed secondary check, and nothing then bounded the exploration that followed.
- **Desired behavior**: a failed probe always routes to the developer, whatever the
  evidence tier.

## 🔨 Suggested Implementation

1. Promote Palimpsest's executable-probe wording into the template capability.
2. Separate the two things the escape hatch conflates, along these lines:

   > A probe that has been attempted and failed is positive evidence about the
   > environment. Report it and request the evidence channel from the developer
   > before continuing, whatever the evidence tier. Never respond to a failed probe
   > by exploring the local environment for an alternative.

3. Write the migration record.

## ⚠️ Constraints and Considerations

- Do not widen the change into a general rewrite of manual-verification policy. The
  defect is the composition of two rules, not either rule alone.
- Per `CONTRIBUTING.md`, trace the affected path from initialization through task
  creation, implementation, review, acceptance, and upgrade, and name every asset
  updated in the report.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/003-probe-escape-hatch.md)"$'\n\nExecute this task in the current project.'
```
