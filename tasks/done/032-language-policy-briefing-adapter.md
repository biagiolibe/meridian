# Task 032 — Add Claude Language-Policy Briefing Adapter

> **ID**: `032`
> **Category**: Feature
> **Priority**: P2
> **Assigned to**: Codex

## Objective

Extend the Claude `UserPromptSubmit` briefing so a valid project `LANGUAGE_POLICY.md` is restated at every prompt. Keep the policy file as the only source of the conversation-language value.

## Acceptance Criteria

- The hook emits a compact language-policy block for a valid configured policy, including when no queue exists.
- The block states the configured conversation language and the repository-English invariant.
- Projects with no language policy retain the hook's current silent behavior when they also have no queue.
- Missing, placeholder, or ambiguous language values are not presented as configured values.
- Existing Lean Delivery and Governed SDD queue briefing behavior remains unchanged.
- Regression tests cover the added behavior and all baseline checks pass.

## Relevant Files

| File | Role |
|---|---|
| `hooks/queue-briefing.sh` | Claude prompt hook to extend. |
| `tests/test_queue_briefing.py` | Regression coverage. |
| `README.md` | Host-specific behavior documentation. |
| `hooks/hooks.json` | Plugin hook description. |

## Constraints

- The hook provides salience, not deterministic enforcement.
- Do not duplicate a project-specific language value in templates or host configuration.
- Persistent repository text must be English.

## Validation

- `python3 -m unittest discover -s tests` — passed: 121 tests.
- `python3 scripts/check_repository.py` — passed.
- `git diff --check` — passed.
- `bin/meridian audit --project .` — completed; the local Lean overlay has no capability markers to audit.

## Completion

Implemented the Claude language-policy briefing adapter, regression coverage,
and host-behavior documentation. The queue briefing behavior remains covered by
the existing regression suite.
