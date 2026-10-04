# Task 159 — Retire the reasoning budget contract

> **ID**: `159`
> **Category**: Refactor
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Palimpsest executions blocked by the reasoning directive, 2026-10-04

## Objective

The Governed SDD templates require each task to carry a `Reasoning` field that
is "the exact permitted runtime cap", and require a worker to confirm that its
configured reasoning effort equals it before implementation, remediation, or
review; if it differs or cannot be confirmed, the worker must stop and start a
fresh session. Agents cannot read their effective level, so the directive stops
every execution that carries it. Meridian's CLI never enforced it
(`execution_preflight` states it does not inspect a chat's reasoning setting),
so the text only blocks and cannot be satisfied. The developer's decision is to
remove reasoning management from Meridian entirely.

Retire the contract, its task fields, and its operator guidance from the managed
templates, with a migration that removes it from adopted projects.

## Acceptance Criteria

- [x] The managed `reasoning-budget-contract` block is removed from
  `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md`, together with
  every sentence of that file and of the other Governed SDD templates that
  requires choosing, recording, matching, confirming, or escalating a reasoning
  level (`PROJECT_WORKFLOW.md`, `tasks/TASK_BLUEPRINT.md`,
  `docs/OPERATOR_PROMPTS.md`, `docs/PULL_REQUEST_POLICY.md`, workflow procedures,
  and the lifecycle-orchestration paragraph). Mentions that only describe
  context size, not a reasoning level, stay.
- [x] `TASK_BLUEPRINT.md` no longer has `Reasoning` and `Reasoning
  justification` fields. Existing tasks that still carry them are not an error:
  no check requires or rejects the fields.
- [x] A migration whose `to` is the next release retires the capability using the
  existing retirement mechanism for protected marker blocks, so
  `upgrade --check` on a project with the 1.2.8 text shows the block removal and
  `upgrade` applies it without touching local text. The catalog, the capability
  marker documents, and the marker baselines are updated consistently;
  `meridian-audit` reports no stale marker for the retired capability.
- [x] Lean Delivery templates are unchanged unless they mention reasoning levels
  (none were found).
- [x] No acceptance criterion, check, or hook anywhere reads, requires, or
  compares a reasoning level. The test that asserts the exact-cap contract
  (`test_reasoning_budget_contract_uses_an_exact_cap_without_auto_escalation`)
  and the marker-pair expectation naming `reasoning-budget-contract` are removed
  or replaced by a test that the retired block is absent.
- [x] `scripts/project_console.py` and its tests keep reading
  `model_reasoning_effort` only as a display value, unchanged.
- [x] `VERSION`, `.claude-plugin/plugin.json`, and the release ledger are bumped
  for the template-changing release in this task's commits, as `CONTRIBUTING.md`
  requires; nothing is tagged or published.
- [x] One changelog fragment states the removal under `Removed` and the required
  action under `Upgrade notes`.
- [x] `meridian upgrade --check` on copies of the Palimpsest and Fusa manifests
  reports the block removal and no `BLOCKED`; results go in the handoff.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | The `reasoning-budget-contract` block (~173) and reasoning wording (~1, ~157, ~199). |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | `Reasoning` fields. |
| `templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md` | "Choose the reasoning level" section and related lines. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`, `docs/PULL_REQUEST_POLICY.md` | Mentions of reasoning profiles. |
| `capabilities/catalog-v1.json`, `migrations/CAPABILITY_MARKERS.md`, `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json` | Capability registration. |
| `migrations/020-reasoning-budget-contract.json`, `migrations/021-concrete-execution-budgets.json` | Historical migrations; never edited. |
| `tests/test_meridian_cli.py` | Marker and contract tests (~2324, ~4366, ~4381). |

## Technical Context

- Where the directive lives: a protected marker block, a blueprint field pair,
  and operator guidance. The CLI has no code for it.
- Removing a protected block from consumer projects needs a retirement-stage
  migration; see how earlier retirements (for example migration 038) declare
  `stage: "retirement"` and how `first_retirement_migration` orders them. This
  has to be read before writing the migration.
- Decision recorded here: remove the contract and its fields, not replace them
  with advice. A project that wants a reasoning policy writes its own outside the
  managed blocks.
- Sequencing: this is template-changing and shares the next release with task
  158 only if both are integrated before publishing; the order between them is
  free.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Publishing the release, changing host-side model or effort settings, and editing
historical migrations.

## Dependencies

- **Depends on**: —
- **Blocks**: none
