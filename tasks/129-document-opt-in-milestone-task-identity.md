# Task 129 — Document and activate the opt-in milestone task identity

> **ID**: `129`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Palimpsest nomenclature review, 2026-10-03

## Objective

The milestone task-identity mode (`M<milestone>-<WORKSTREAM>-<ordinal>`) is
implemented and selectable through `.meridian/task-identity.json`, but its
policy document still says "design proposal", no shipped guide explains how to
activate it, and nothing tells a project what changes. A rehearsal on a copy of
the Palimpsest task records showed that its 302 IDs resolve with no error under
`milestone` mode (141 structured, 161 legacy-opaque), so the mode already fits
a real Governed SDD project. Make the option discoverable and safe to adopt,
without changing its behavior or its opt-in default.

## Acceptance Criteria

- [ ] `docs/TASK_IDENTITY_POLICY.md` states the real status: implemented, with
  the delivering tasks and the current behavior of `meridian task identity
  check`. Statements that were true only of the proposal are corrected.
- [ ] The document gains an activation procedure for a project: create the
  one-line declaration `{"version": 1, "mode": "milestone"}`, run `meridian task
  identity check <ID> --format json` on representative IDs, and review which
  existing IDs become `legacy-opaque`. It states that nothing is renamed and that
  reverting means deleting the file.
- [ ] It states plainly that the declaration is never distributed: no template,
  `init`, `lock`, or `upgrade` creates `.meridian/task-identity.json`, so a new
  or existing project opts in by creating it by hand (or, later, through an
  assisted command). Absence is the supported default and is not an error.
- [ ] It documents the consequences for new IDs in `milestone` mode: only the
  canonical grammar is accepted; the milestone has no leading zero (`M7-…`
  parses, `M07-…` does not); the ordinal is three digits; and an ID with no
  ordinal, such as a recurring `M38-VERIFY`, is rejected for new tasks while an
  existing one stays `legacy-opaque`. The recommended workaround (`M38-VERIFY-001`)
  is stated, and the grammar is not extended.
- [ ] The rehearsal result is recorded as an example, with the method (copy the
  task records to a scratch directory, add the declaration, run the check over
  every ID) and its counts, attributed to the date of the run and not presented
  as a guarantee for other projects.
- [ ] Optional queue and location guidance for Governed SDD is documented as a
  convention, not a requirement: one task folder per milestone
  (`docs/tasks/<milestone>/`), and a queue section per milestone, both already
  resolved by the existing location and queue handling. Before writing this,
  confirm with a fixture that the console and the queue parser accept a
  per-milestone section layout with `Order` and `Estimate` columns, and record
  any gap as a follow-up instead of fixing it here.
- [ ] The Governed SDD template and `README.md` gain a short pointer to the
  guide. If a managed template block changes, the task follows the capability
  marker and migration rules and is limited to additive wording; if that cannot
  be done within this task, the pointer goes only in `README.md` and the
  decision is recorded in the handoff.
- [ ] Workflow neutrality is preserved and stated: the mode is independent of the
  workflow, Lean Delivery can use it too, and no behavior is added or restricted
  per workflow.
- [ ] No resolver, schema, parser, or CLI behavior changes. A diff of
  `scripts/` is empty except for any text the repository check requires.
- [ ] One changelog fragment is added per `CONTRIBUTING.md` if a user-visible
  document or managed template changes.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/TASK_IDENTITY_POLICY.md` | Status correction and activation guide. |
| `README.md` | Pointer to the guide. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Existing `task-identity-policy` block; additive pointer only if feasible. |
| `scripts/meridian.py` | Read only: resolver and the `STRUCTURED_TASK_ID` grammar. |
| `tests/test_meridian_cli.py` | Existing identity tests, for reference. |

## Technical Context

- The grammar is `M(?P<milestone>[1-9][0-9]*)-<WORKSTREAM>-<ordinal 001..999>`
  (`scripts/meridian.py`); the mode is declared only in
  `.meridian/task-identity.json`, whose absence selects `opaque`.
- A `milestone` project keeps pre-existing non-matching IDs as `legacy-opaque`
  and rejects unknown non-matching IDs, so existing history is never renamed.
- Observed in the Palimpsest rehearsal (copy in a scratch directory, the
  project itself untouched): 46 `M…` IDs are legacy, namely the zero-padded
  `M02`–`M09` integration tasks and the ordinal-less `Mnn-VERIFY` tasks.
- The follow-up of an assisted activation command that prints the same
  classification and writes the declaration only on explicit apply is out of
  scope here and is recorded as a candidate task in the handoff.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the grammar, the resolver, the schema, or the CLI; creating the
declaration in any project including Palimpsest; the assisted activation
command; and publishing a release.

## Dependencies

- **Depends on**: —
- **Blocks**: none
