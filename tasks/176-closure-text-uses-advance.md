# Task 176 — Replace the closure procedure in managed text with `advance`

> **ID**: `176`
> **Category**: Refactor
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Closure simplification follow-up to ADR stops and denials, 2026-10-05

## Objective

After tasks 174 and 175, the ten-step closure procedure in the managed
`git-workflow` block is no longer needed. Agents only need to run `advance`
and do what it returns. Shrink the managed text so that the procedure lives in
code and not in prose.

## Acceptance Criteria

- [ ] In the managed `git-workflow` block of both workflows, and in the Lean
  router copies and this repository's copies, the closure order and the
  per-step stop list are replaced by a short rule. The rule tells the agent to:
  - run `meridian worktree advance <TASK-ID>`;
  - perform exactly its `action_required`;
  - rerun it with the results;
  - report its `BLOCKED` line when it stops.
  The deny list, the authority of `Proceed with`, the governance-file
  ownership rule, and the rules from task 164 stay.
- [ ] The block is measurably shorter. The handoff records the byte size of
  each changed managed block before and after, and each block shrinks.
- [ ] `docs/WORKTREE_LIFECYCLE.md` keeps the single-step commands as the
  documented path for diagnosis and manual recovery.
- [ ] The capability marker version is bumped through a migration whose `to` is
  the next release. `upgrade --check` on copies of the Palimpsest and Fusa
  manifests shows the update and no `BLOCKED`; the results go in the handoff.
- [ ] The Codex and Claude Code skill assets for both modes stay in parity.
- [ ] `VERSION`, `.claude-plugin/plugin.json`, and the release ledger are bumped
  only if no earlier unreleased task has done so for the same release.
- [ ] One changelog fragment states the change under `Changed` and the action
  under `Upgrade notes`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/lean-delivery/{PROJECT_WORKFLOW,AGENTS,CLAUDE}.md` | Lean block and router copies. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Governed block. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | This repository's copies. |
| `docs/WORKTREE_LIFECYCLE.md` | Manual path. |
| `migrations/`, `migrations/CAPABILITY_MARKERS.md`, `migrations/marker-baselines/` | Marker delivery. |
| `skills/` | Skill parity. |

## Technical Context

- Task 164 changes the same block first. Read its final text before writing
  this change.
- Governed SDD keeps its review gate. `advance` reports `REVIEW_REQUIRED` as
  a `human` action, so the text does not restate it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Removing the single-step commands, shrinking the routers in other ways, and
changing the deny list.

## Dependencies

- **Depends on**: 164, 175
- **Blocks**: none
