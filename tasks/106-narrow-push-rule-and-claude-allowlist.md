# Task 106 — Narrow the Codex push rule and offer a Claude Code allowlist

> **ID**: `106`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Follow-up created by task 100

## Objective

Implement Decision 1's host side: restrict the unattended push to `git push origin main` and offer the matching Claude Code project allowlist through the consented `meridian setup`, with `codex doctor` reporting the gap.

Authority: `docs/TASK_CLOSURE_DESIGN.md`.

## Acceptance Criteria

- [ ] `.codex/rules/meridian.rules` allows `git push origin main` and leaves other pushes, including tag pushes, to prompt; the task tests how the rule engine ranks a narrow allow against a broader prompt rule and records the observed result, or marks it unverified.
- [ ] `meridian setup` can add a project-scoped Claude Code allowlist for `git push origin main` and `meridian worktree integrate stage|finalize|abort|cleanup` only after consent, and never writes silently.
- [ ] The existing `forbidden` rules for force, delete, and mirror pushes are unchanged.
- [ ] `python3 scripts/check_repository.py` passes, and the unit tests pass unless the change is documentation-only.

## Relevant Files

| File | Role |
|------|------|
| `.codex/rules/meridian.rules` | Changed or read by this task. |
| `scripts/meridian.py` | Changed or read by this task. |
| `tests/` | Changed or read by this task. |
| `README.md` | Changed or read by this task. |

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`

## Out of scope

Any other follow-up of `docs/TASK_CLOSURE_DESIGN.md`.

## Dependencies

- **Depends on**: 100
