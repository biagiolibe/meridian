# Task 025 — Compact entry points and retire duplicate role procedures

> **ID**: `025`
> **Category**: Refactor
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned

## Objective

Ship the retirement release after task 024: make `AGENTS.md` and `CLAUDE.md`
compact routers and remove only the now-proven duplicate role procedures.

## Acceptance Criteria

- [ ] Governed-SDD entry points retain only the accepted bootstrap invariants,
      routing instructions, and host-specific requirements within the ADR byte budget.
- [ ] Retired marker blocks are declared through the capability-move metadata;
      their role-procedure copies remain the sole canonical source.
- [ ] `meridian audit` rejects an old locally customized duplicate rather than
      deleting it, and passes upgraded vanilla and explicit-pointer projects.
- [ ] Regression tests prove a request loads only its routed procedure and
      that all lifecycle safeguards remain reachable.

## Constraints

- Do not change lifecycle, review, validation, evidence, or Git semantics.
- Do not combine consumer-project rollout with this framework migration.

## Validation

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/check_repository.py`
- `git diff --check`

## Dependencies

- **Depends on**: 024
- **Blocks**: 026
