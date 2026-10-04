# Task 152 — Read project declarations from the primary checkout, keep budget state out of it, and state Review's closure authority

> **ID**: `152`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2.5h
> **Assigned to**: unassigned
> **Session**: Palimpsest review of F1-BEVY-001, 2026-10-04

## Objective

A reviewer-integrator in Palimpsest (Meridian 1.2.7) reached `APPROVE` for
F1-BEVY-001 and stopped before the `ACCEPTED` commit for three framework reasons:

1. `meridian project show --field reviewer-author` returned
   `BLOCKED: project declaration key 'project' is required`. `meridian setup`
   had proposed and written `.meridian/project.json` with `locations` only; it
   never proposes `project`, so the identity stayed in workflow prose. After the
   developer added `project` on `main`, the command still read the stale copy,
   because `project show` (and `locations`) read `.meridian/project.json` from the
   current directory, and a task worktree holds the file as of its base commit.
2. `.meridian/budget.json`, which `meridian budget` and the execution commands
   write as runtime state, is tracked and was modified in the primary checkout
   with an entry for the task under review. Integration stages only from a clean
   primary checkout, so it would have stopped at `PRIMARY_DIRTY`.
3. The reviewer would not push `main` without separate confirmation: the
   `git-workflow` authority paragraph names only `Proceed with`, while
   `docs/workflows/REVIEW.md` and `git-workflow` say the reviewer-integrator
   "performs C6 through C10 after approval". The authority is intended but not
   stated for the `Review` trigger.

## Acceptance Criteria

- [ ] `meridian project show` and `meridian locations` resolve the declaration
  from the canonical primary checkout (the first `git worktree list --porcelain`
  entry) when run from a linked task worktree or with `--project` pointing at
  one, exactly as lifecycle commands resolve their project. Every internal reader
  of `.meridian/project.json` uses the same resolution. A test proves a worktree
  created before a `project` change on `main` reports the updated reviewer author.
- [ ] `meridian setup --check` proposes a `project` object (name and slug) when it
  is missing, derived deterministically (for example from the repository name)
  and shown for review; `--apply` writes it only after the existing consent flow
  and never overwrites declared values. A declaration that has `locations` but no
  `project` is reported as `advisory-incomplete`, not `present`.
- [ ] Budget runtime state no longer dirties the primary checkout: it is written to
  an untracked location (for example under the Git common directory or an ignored
  `.meridian/` path) and read from there, with a one-time migration that moves an
  existing tracked `.meridian/budget.json` and makes the project stop tracking it.
  If the design keeps a tracked file instead, the handoff explains why and how
  `integrate stage` stays unblocked. `integrate stage` never fails `PRIMARY_DIRTY`
  because of budget state alone.
- [ ] `git-workflow` (Governed SDD) gains, in additive wording within its
  authority paragraph, that after `APPROVE` the `Review <TASK-ID>` trigger carries
  the same authority as `Proceed with` for C6 through C10, including the single
  plain `git push origin main` and `cleanup`, and the same prohibitions.
  `task-worktree-review-procedure` states the same in one sentence. Both get new
  versions in a template-changing migration, with an Upgrade note.
- [ ] `meridian audit` or `setup --check` reports a tracked `.meridian/budget.json`
  and an incomplete project declaration as advisories, without writing.
- [ ] Tests cover: project show and locations from a stale worktree; setup
  proposal and refusal to overwrite; the incomplete-declaration state; budget
  writes leaving `git status` clean in the primary checkout; the budget migration;
  stage with only budget activity not blocked; and the new authority text.
- [ ] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `read_project_declaration`, `resolve_project_locations`, `project` and `locations` commands, `setup --check` proposal (~line 2730), `BUDGET_PATH` (~line 7468) and its readers and writers, `integrate stage` clean-checkout check. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`, `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | `git-workflow` and `task-worktree-review-procedure` text. |
| `migrations/`, `capabilities/` | Template-changing migration and marker baselines. |
| `tests/` | Declaration, setup, budget, stage, and template tests. |

## Technical Context

- Observed on 2026-10-04 in Palimpsest: the review stopped at the `ACCEPTED`
  commit; the developer then declared `project` on `main` (commit `72e176e`) and
  committed the pending `budget.json` entry so the primary checkout was clean.
- Lean Delivery's `git-workflow` has no reviewer role and is unchanged unless a
  shared sentence requires it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing which identity the reviewer uses, the closure steps themselves, budget
semantics, and the `Accept` trigger.

## Dependencies

- **Depends on**: —
- **Blocks**: none
