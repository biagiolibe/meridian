# Task 064 — Remove the primary-checkout review conflict

> **ID**: `064`
> **Category**: Bugfix / Workflow Safety
> **Priority**: 🔴 P1
> **Estimate**: ~2–4h
> **Assigned to**: unassigned
> **Session**: 2026-09-27 repeated Claude review misrouting

## 🎯 Objective

Remove the contradictory Governed SDD review instructions that tell a reviewer
both to switch the primary checkout to the task branch and to use the dedicated
task worktree without touching the primary checkout.

Make the task-worktree verification the first mandatory action of
`Review <TASK-ID>` and deliver the correction to existing adopters through a
versioned migration. A reviewer must fail closed before inspecting the task
diff when the registered task worktree cannot be identified and verified.

## 📋 Acceptance Criteria

- [ ] `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` contains no
      instruction to review in the primary checkout, leave the primary checkout
      on the task branch, run `git switch <task-branch>` there, or use a
      primary-checkout fast-forward merge as part of review.
- [ ] The `implementer-reviewer-handoff` capability is revised so it records
      only the durable handoff and sequential ownership needed by the current
      linked-worktree protocol. It no longer embeds the retired checkout,
      ancestry, integration, or cleanup procedure.
- [ ] The task-worktree review procedure begins with a fail-closed preflight,
      before reading implementation files or computing a diff: read the
      completion handoff, obtain the recorded absolute worktree path and task
      branch, locate the same entry in `git worktree list --porcelain`, and
      verify path, branch, HEAD, cleanliness, validated task commit, and base
      commit.
- [ ] When the reviewer session starts in the primary checkout, every review
      read and command is explicitly rooted in the verified task worktree. The
      procedure never treats the session's initial current directory as the
      task checkout and never switches the primary checkout to compensate.
- [ ] A missing handoff, missing or unregistered worktree, branch/HEAD/path
      mismatch, dirty task worktree, active implementer, or unavailable
      validated commit returns `BLOCKED` before substantive review and
      preserves all task, branch, and worktree state.
- [ ] The procedure remains compatible with Task 056: until
      `meridian worktree check` exists it uses the bounded read-only Git and
      handoff checks above; after Task 056 lands, the managed procedure may
      route the same invariant through that command without changing review
      semantics.
- [ ] The correction is applied consistently to the canonical Governed SDD
      review procedure and any router, review prompt, lifecycle, or policy text
      that repeats the checkout selection rule. Lean Delivery retains its own
      review policy and receives no Governed lifecycle states.
- [ ] Protected capability markers and marker baselines are bumped for every
      changed managed block. A new migration upgrades existing adopters and
      replaces the contradictory protected text rather than merely appending a
      third instruction that claims to supersede it.
- [ ] Upgrade fixtures prove that a project containing the current
      `implementer-reviewer-handoff v1` and
      `task-worktree-review-procedure v2` blocks receives the corrected blocks
      while project-owned text outside markers remains unchanged.
- [ ] Repository checks or focused tests reject any managed Governed review
      procedure that contains the retired primary-checkout review phrases,
      including `uses that same primary checkout`,
      `git switch <task-branch>`, or `leave the primary checkout ... on the task
      branch`.
- [ ] Tests cover a reviewer launched from the primary checkout, a valid task
      worktree, an absent worktree, a mismatched branch or HEAD, a dirty
      worktree, and a handoff/path disagreement. Only the valid registered task
      worktree reaches substantive diff inspection.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | Contains the contradictory protected legacy and current review procedures. |
| `templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md` | Reviewer entry prompt that must enforce the same worktree-first boundary. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Canonical Governed worktree and reviewer contract. |
| `templates/workflows/governed-sdd/AGENTS.md`, `templates/workflows/governed-sdd/CLAUDE.md` | Command routers for `Review <TASK-ID>`. |
| `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json` | Protected-block versions and hashes. |
| `migrations/` | Versioned correction for existing adopters. |
| `tests/test_meridian_cli.py` | Upgrade preservation and capability migration coverage. |
| `tests/test_check_repository.py` | Regression check for retired contradictory instructions. |
| `tasks/056-add-bounded-worktree-lifecycle-commands.md` | Later mechanical `meridian worktree check`; not implemented here. |

## 🧩 Technical Context

The current Governed review template retains
`implementer-reviewer-handoff v1`, which says to leave the primary checkout on
the task branch and directs the reviewer to run `git switch <task-branch>` in
that checkout. A later `task-worktree-review-procedure v2` block says it
supersedes those steps and forbids switching the primary checkout.

The same contradiction is already installed in Palimpsest. Claude has twice
followed the earlier, concrete primary-checkout instruction and searched
`main` for task changes instead of reviewing the registered linked worktree.
An instruction that merely says a later block supersedes an earlier one is not
a reliable safety boundary; the obsolete action must be removed through the
managed capability and migration mechanism.

## 🔨 Suggested Implementation

1. Rewrite and version-bump `implementer-reviewer-handoff` so it contains only
   current handoff facts and sequential ownership, with no checkout or
   integration algorithm.
2. Make the task-worktree preflight the first operational section of the
   review procedure and version-bump its capability when its protected text
   changes.
3. Check all managed Governed review entry points for repeated checkout
   selection language and make the verified absolute worktree path explicit.
4. Add the migration, regenerate marker baselines, and test an upgrade from the
   currently distributed conflicting blocks.
5. Add a repository invariant that rejects the exact retired instructions so a
   later template merge cannot restore them.

## ⚠️ Constraints and Considerations

- Do not implement `meridian worktree check` or any mutating lifecycle command;
  those belong to Task 056.
- Do not perform substantive review from the primary checkout, even when the
  task branch exists locally or the primary checkout is clean.
- Do not move, recreate, repair, or delete a missing or mismatched task
  worktree during review; return `BLOCKED` with the exact discrepancy.
- Do not weaken independent-review, validation-evidence, review-record,
  acceptance, integration-lease, or forge requirements.
- Do not modify Palimpsest directly in this task. Deliver the correction via a
  Meridian release and normal consumer upgrade.
- Preserve project-owned text outside managed capability markers.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: a fresh reviewer session uses the registered task worktree
regardless of whether Claude Code, Codex, or another host launches the session
from the project's primary checkout.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Claude Code plugin session | conflicting instructions can route review to `main` | verified absolute task-worktree path is mandatory before review | Updated plugin/framework, migrated workflow, and a stopped implementer with a clean registered worktree. | Return `BLOCKED`; never review `main` as a substitute. |
| Codex project | textual worktree rule exists but legacy primary-checkout steps remain | the same worktree-first preflight applies | Migrated workflow and access to the registered worktree. | Return `BLOCKED` with the failed path/branch/HEAD check. |
| Host-neutral workflow | later text claims to supersede dangerous earlier text | obsolete actions are absent from the effective procedure | Capability migration and baseline verification pass. | Fail repository or upgrade validation if retired phrases remain. |

## 🔗 Dependencies

- **Depends on**: 051, 063
- **Blocks**: safe Governed SDD review in upgraded consumer projects.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/064-remove-primary-checkout-review-conflict.md)"$'\n\nExecute this task in the current project.'
```
