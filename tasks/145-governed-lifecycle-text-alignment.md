# Task 145 — Align Governed lifecycle capability text with the closure design and the CLI

> **ID**: `145`
> **Category**: Documentation
> **Priority**: 🔴 P1
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D1–D4, D6, D7, D9, D11, D13, design approved 2026-10-04

## Objective

A Governed SDD consumer whose policy treats every managed block as authoritative
found managed blocks that contradict each other and the CLI. Correct the text to
the approved decisions:

- **D1** Task branches never edit the queue, queue archive, or plan; Governed
  `IN_PROGRESS`, `READY_FOR_REVIEW`, and `CHANGES_REQUESTED` live in the task
  record; `integrate stage` applies the queue row (`TASK_CLOSURE_DESIGN.md`,
  Decision 2).
- **D2** The task branch is the `branch` value returned by `meridian worktree
  prepare`, never a literal `task-<TASK-ID>` pattern.
- **D3** A task-branch push happens only to obtain `T1_CI`, at most once per
  review attempt, never by the reviewer, and not at all without CI. `Proceed with`
  authorizes the first attempt's push; `Address review` authorizes the next one.
- **D4** `.meridian/candidate-validation.json` is the only candidate-validation
  declaration; the `Project integration smoke command:` line is removed.
- **D6/D7** Text names resolved locations (`meridian locations`) and the reviewer
  author from `meridian project show --field reviewer-author`; no placeholders.
- **D9** `Accept <TASK-ID>` appends an owner `APPROVE` attempt to the review record,
  sets the task record to `ACCEPTED`, and continues at C6 under the `Proceed with`
  authority; a manual merge is never permitted.
- **D11** The reviewer verifies the absolute path resolved at runtime from the
  recorded `handoff_worktree`.
- **Spike** A spike integrates only its deliverable and never merges production
  code (behavior shipped by task 142).
- **D13** `code-organization` v1 says the project module map belongs "not in this
  file", while projects keep it in `docs/CODE_ORGANIZATION.md` and tasks cite it as
  Authority. The intent is only to keep project architecture out of the managed
  block: the map may live in the project's architecture documentation or in a
  `## Project module map` section after the block. No project move or citation
  migration is required.

## Acceptance Criteria

- [ ] New Governed capability versions with the corrected text: `git-workflow` v9,
  `roles` v3, `review-mode-boundary` v2, `review-remediation-record` v3,
  `implementer-reviewer-handoff` v4, `task-worktree-integration` v4,
  `owner-acceptance-workflow` v2, `task-worktree-boundary` v7,
  `task-worktree-review-procedure` v9, `execution-command-gate` v2,
  `lifecycle-orchestration` v8, `review-policy` v3, `task-lifecycle` v3,
  `execution-assets` v3, `reviewer-integrator-identity` v2, `code-organization` v2.
  Lean `git-workflow` v9 carries D2 and D3 only.
- [ ] `code-organization` v2 replaces the "not in this file" sentence with: the
  project records its layered module map and dependency direction either in its
  architecture documentation or in a `## Project module map` section after this
  managed block, never inside the block. A test proves `meridian context authority`
  resolves `docs/CODE_ORGANIZATION.md#Project module map` from a section after the
  block, and upgrade preserves that section unchanged.
- [ ] `task-worktree-boundary` v7 states the order: before `prepare` only the
  router read set may be read; no task material and no mutation; `prepare` is the
  only command before `check`.
- [ ] No managed block in either template says a task branch, reviewer, or owner
  edits a queue row, and none names a literal queue, queue-archive, review, or
  handoff path except as a default in `execution-assets`. A repository check
  enforces both statements.
- [ ] No template contains `task-<TASK-ID>`, `<PROJECT_NAME>`, `<project-slug>`,
  or the hard-coded `meridian Reviewer-Integrator` identity; the reviewer identity
  rule appears in exactly one managed block.
- [ ] The `Project integration smoke command:` line is removed from both
  `PROJECT_WORKFLOW.md` templates and this repository's copy; nothing reads it.
- [ ] The unmarked prose in `tasks/QUEUE.md` (Governed template) and
  `docs/CODE_REVIEW_PROMPT.md` matches D1 and D3.
- [ ] `audit-prompt` v3 checks 10–12 match D1, D3, and D9.
- [ ] The changes are recorded in one unreleased template-changing migration,
  shared with tasks 133 and 137 if those have not been released; confirm
  `VERSION` and pending migrations first. Marker baselines and managed-copy
  digests are refreshed.
- [ ] Tests or repository checks prove an owner-accepted task passes
  `integrate stage` (latest verdict `APPROVE` by owner) and that `Accept` text and
  stage agree.
- [ ] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | `git-workflow`, `roles`, `review-policy`, `task-lifecycle`, `execution-assets`. |
| `templates/workflows/governed-sdd/docs/workflows/*.md` | Implementation, review, remediation, lifecycle blocks. |
| `templates/workflows/governed-sdd/docs/PULL_REQUEST_POLICY.md`, `LIFECYCLE_ORCHESTRATION.md`, `AUDIT_PROMPT_READ_ONLY.md`, `CODE_REVIEW_PROMPT.md` | Integration, orchestration, audit, review prompt text. |
| `templates/workflows/governed-sdd/tasks/QUEUE.md` | Queue prose. |
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md`, `PROJECT_WORKFLOW.md` | Lean `git-workflow` v9 and the smoke line. |
| `migrations/`, `capabilities/`, `scripts/check_repository.py` | Migration, marker baselines, new checks. |

## Technical Context

- The full corrected wording for each block was drafted in the design session of
  2026-10-04; use it as the starting point and keep each block self-contained.
- Capability versions are keyed per workflow mode (migration 059 format), so a
  Governed-only version bump is valid.
- Branches in flight that still edit queue rows close under the old rule; stage is
  idempotent for an already `ACCEPTED` row.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Marker restructuring of `CODE_REVIEW_PROMPT.md`, `WORKTREE_LIFECYCLE.md` status,
audit digest checks, and consumer profiles (task 146); CLI behavior (tasks
142–144).

## Dependencies

- **Depends on**: 142, 143, 144
- **Blocks**: 146
