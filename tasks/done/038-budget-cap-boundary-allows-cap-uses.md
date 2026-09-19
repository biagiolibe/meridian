# Task 038 — Make a budget cap admit exactly `cap` uses

> **ID**: `038`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1-2h
> **Assigned to**: unassigned
> **Session**: 2026-09-18, follow-up to a consumer agent's boundary report

## 🎯 Objective

`budget_spend()` in `scripts/meridian.py` rejects a spend when
`count >= cap`, so a cap of N admits only N-1 uses. `Diagnostic attempts: 3`
reads as three attempts but permits two; a task override of `1` permits none;
the default `Evidence captures: 2` permits one capture; a scope-2
investigation under `Investigation scope: 2` is rejected outright. A consumer
agent was blocked at its third diagnostic attempt for exactly this reason.

Change the boundary so a cap of N admits exactly N recorded uses and the
(N+1)th is rejected with `BLOCKED`. This is a deliberate semantics change,
not an accident fix: the current boundary is pinned by tests and described in
`docs/PLAN_TOKEN_EFFICIENCY.md` ("`spend` returns non-zero once the declared
cap is reached"). The field names (`Diagnostic attempts`, `Evidence
captures`, `Context expansions`, `Investigation scope`) and the "cap, not a
target" wording promise a count of allowed uses, so the code should match
them.

## 📋 Acceptance Criteria

- [x] `budget_spend()` rejects only when `count > cap`. For cap N, spends
      1..N succeed and print `<task>: <kind> N/N` on the Nth; the (N+1)th
      exits non-zero.
- [x] The rejection message still names `BLOCKED` and still says not to
      raise the cap, and it states the rejected count against the cap
      unambiguously (for example that N of N allowed uses are already
      recorded), so it no longer reads as if the cap-th use were the
      forbidden one.
- [x] A rejected spend still leaves `.meridian/budget.json` unchanged (the
      task 033 guarantee), including for a multi-unit `amount` such as an
      investigation scope of 2 against a remaining allowance of 1.
- [x] A task override cap of `1` admits exactly one use; the default
      `Investigation scope: 2` admits a single scope-2 investigation.
- [x] Every test that pins the old boundary is updated to the new one, in
      `tests/test_meridian_cli.py`:
      `test_spend_increments_and_reports`,
      `test_spend_returns_non_zero_and_names_blocked_once_cap_reached`,
      `test_spend_respects_task_override_cap`,
      `test_spend_rejected_by_cap_leaves_state_unchanged`, and any
      `execution evidence` / `investigate` test whose expected `count/cap`
      or exhaustion behavior changes. Add a case for a multi-unit spend
      that would cross the cap.
- [x] The design text that states the old boundary is corrected:
      `docs/PLAN_TOKEN_EFFICIENCY.md` ("returns non-zero once the declared
      cap is reached").
- [x] Template wording is checked against the new behavior. The candidates
      are `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md`
      ("reaching one requires `BLOCKED`", and the `Diagnostic attempts`
      bullet) and `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md`
      ("exhausting it requires `BLOCKED`"). Record in the task's completion
      notes whether each still reads correctly. Reword only what
      contradicts N-uses-allowed, and state the count explicitly where it
      helps (for example "three attempts are allowed; a fourth requires
      `BLOCKED`").
- [x] If any managed template text changes, the change ships with a real
      migration record under `migrations/` (next free number, `from` the
      latest migration's `to`, `to` the new `VERSION`) plus a
      `CHANGELOG.md` entry, following `CONTRIBUTING.md`. If the edited text
      sits inside a `MERIDIAN:BEGIN capability=...` block (the
      `task-blueprint` block in `TASK_BLUEPRINT.md` is one), the migration
      must bump that capability and declare a scoped `delta`, and
      `python3 scripts/check_repository.py --write-marker-baselines` must
      be run deliberately. If no template text needs to change, no
      migration is added and the `CHANGELOG.md` entry says the behavior
      change is CLI-only.
- [x] `python3 scripts/check_repository.py` passes.
- [x] `python3 -m unittest discover -s tests -v` passes.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `budget_spend()` (comparison at `count >= cap`), `budget_show()`, `record_execution_event()` and `record_investigation()` callers. |
| `tests/test_meridian_cli.py` | Tests pinning the boundary (around lines 2293-2340) and any evidence/investigate tests that read `count/cap`. |
| `docs/PLAN_TOKEN_EFFICIENCY.md` | States the old boundary in the CLI description. |
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Cap wording (top paragraph and the `Diagnostic attempts` bullet). Mostly unmarked prose. |
| `templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md` | Cap wording inside the `task-blueprint` marker. |
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | `Budget usage: used/cap` line; check it still reads correctly when `used == cap` is now reachable. |
| `hooks/queue-briefing.sh` | Echoes the caps (`On exhaustion: return BLOCKED`); check wording only. |

## 🧩 Technical Context

- **Current behavior**: `count = stored + amount; if count >= cap: raise`.
  The persisted counter therefore never shows `cap/cap` (a rejected spend
  is not written), so `meridian budget show` prints `2/3` and gives no hint
  that the next attempt is refused.
- **Desired behavior**: `if count > cap: raise`. `cap/cap` becomes a valid
  persisted state meaning "fully used; the next use is `BLOCKED`". Budgets
  for existing projects become one unit more permissive, which is the
  intended reading of the declared numbers.
- **Investigations**: `record_investigation()` calls
  `budget_spend(..., "investigations", amount=scope)`, so it has the same
  off-by-one for multi-unit amounts; verify the message and tests there.
- **Interaction with the version split (tasks 015-021)**: independent. A
  code-only fix ships as a CLI-only release under the new model; a template
  wording change is a real migration under either model. Check
  `VERSION` and `migrations/` at implementation time rather than assuming
  numbers.

## 🔨 Suggested Implementation

1. Read `budget_spend()` and its tests; run the current suite to record the
   baseline.
2. Change the comparison to `count > cap` and rewrite the error message.
3. Update the pinned tests and add the multi-unit crossing case; confirm the
   rejected-spend-leaves-state-unchanged test still passes for the new
   boundary.
4. Correct `docs/PLAN_TOKEN_EFFICIENCY.md`.
5. Audit the template wording listed above; decide per file whether a
   change is needed, and if so add the migration/marker steps.
6. Run both validation commands and record whether a migration was added.

## ⚠️ Constraints and Considerations

- Do not change cap defaults or field names; only the boundary semantics.
- Do not weaken the guarantee that a rejected spend is never persisted.
- Repository text is English-only.
- The CLI change reaches every project immediately through `MERIDIAN_ROOT`,
  while template wording reaches a project only on upgrade. During that
  window an un-upgraded project's docs may still say "reaching one requires
  `BLOCKED`". The wording is ambiguous rather than wrong under the new
  boundary, so this is acceptable; note it in the `CHANGELOG.md` entry.
- Out of scope: any change to reasoning caps, the read-guard threshold, or
  attempt/remediation bookkeeping in `resolve_budget_key()`.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/038-budget-cap-boundary-allows-cap-uses.md)"$'\n\nExecute this task in the current project.'
```

## ✅ Completion Notes

- **Code**: `budget_spend()` now rejects only when `stored + amount > cap`.
  The rejection reads `<Field> exhausted for <task>: <stored> of <cap> allowed
  uses already recorded, <amount> more requested; return BLOCKED, do not raise
  the cap`. The persisted counter is written only after the check, so a
  rejected spend (including a multi-unit one) leaves `.meridian/budget.json`
  unchanged.
- **Tests** (`tests/test_meridian_cli.py`): updated
  `test_spend_increments_and_reports` (adds the 3/3 use and `budget show`),
  `test_spend_returns_non_zero_and_names_blocked_once_cap_is_used` (renamed),
  `test_spend_respects_task_override_cap` (cap 1 admits one use),
  `test_spend_rejected_by_cap_leaves_state_unchanged` (persisted counter stays
  at `cap`); added
  `test_multi_unit_spend_crossing_the_cap_is_rejected_without_writing`
  (default scope-2 investigation admitted; scope 2 against a remaining
  allowance of 1 rejected without writing; the remaining unit still
  spendable). `test_handoff_rejects_fabricated_validation_and_requires_recorded_investigation`
  now investigates at scope 2 under the default cap through the CLI.
- **Design doc**: `docs/PLAN_TOKEN_EFFICIENCY.md` W2.1 CLI paragraph corrected.
- **Template audit — no template text changed, so no migration**:
  - `EXECUTION_EVIDENCE_PROFILE.md` top paragraph ("reaching one requires
    `BLOCKED`"): ambiguous, not contradictory; it reads correctly as "having
    used the cap, needing more requires `BLOCKED`". Unmarked prose, left as is.
  - `EXECUTION_EVIDENCE_PROFILE.md` `Diagnostic attempts: 3 per failure`
    bullet: reads as a count of allowed attempts; correct under the new
    boundary. Unchanged.
  - `TASK_BLUEPRINT.md` (`task-blueprint` marker, "exhausting it requires
    `BLOCKED`"): "exhausting" matches the CLI's own "exhausted" message once
    all N uses are recorded. Unchanged; rewording would have forced a
    `task-blueprint` capability bump, migration, and baseline rewrite for an
    ambiguity the task's constraints accept.
  - `COMPLETION_REPORT_TEMPLATE.md` (`used/cap`) reads correctly with
    `used == cap`; `hooks/queue-briefing.sh` ("On exhaustion: return BLOCKED")
    reads correctly. Both unchanged.
- **Changelog**: `[Unreleased]` entry states the change is CLI-only and notes
  the un-upgraded-docs window.
- **Validation**: `python3 -m unittest discover -s tests` — 152 tests OK;
  `python3 scripts/check_repository.py` — passed.
