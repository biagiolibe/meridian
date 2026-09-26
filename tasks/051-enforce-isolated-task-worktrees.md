# Task 051 — Enforce isolated worktrees for every task

> **ID**: `051`
> **Category**: Architecture
> **Priority**: 🔴 P1
> **Estimate**: ~4–6h
> **Assigned to**: unassigned
> **Session**: 2026-09-26 task-isolation design

## 🎯 Objective

Make a dedicated Git worktree a mandatory execution boundary for every task in
both Lean Delivery and Governed SDD. An implementer, reviewer, remediation
session, or lifecycle worker must never depend on the developer's primary
checkout remaining on a particular branch. Multiple dependency-independent
tasks must be able to run in parallel without sharing a checkout, while final
integration into `main` remains serialized and evidence-backed.

This task is a global delivery prerequisite. No other open Meridian task may
start until this task is complete and integrated.

## 📋 Acceptance Criteria

- [ ] The local Meridian workflow and both generated workflow templates define
      one task branch and one linked worktree per active task, with one writer
      per worktree. They identify the primary checkout as a coordination and
      final-integration surface, never an implementation or review surface.
- [ ] The procedure defines deterministic branch and worktree naming from the
      canonical task ID, records the task branch, worktree path, base `main`
      commit, and current task commit in the durable handoff, and rejects an
      existing conflicting branch or worktree instead of reusing it silently.
- [ ] `Proceed with <TASK-ID>` creates or selects the task's dedicated
      worktree before any task mutation. Implementation, validation,
      remediation, and task-local status changes run only there.
- [ ] Governed SDD review runs in a fresh agent session against the same
      dedicated task worktree after the implementer has stopped. Review never
      switches the developer's primary checkout to the task branch and never
      runs concurrently with an implementer in that worktree.
- [ ] Changing the branch in the developer's primary checkout while a task is
      being implemented or reviewed cannot change the task worktree's `HEAD`,
      index, or files. If the primary checkout is dirty or unavailable at
      integration time, integration returns `BLOCKED` while preserving the
      task branch and worktree intact.
- [ ] The integration protocol supports two independent task branches created
      from the same `main` commit. It preserves reviewed task commits without
      rebase, amend, cherry-pick, or force-push; serializes `main` integration;
      rejects conflicts; and validates the combined tree before completing an
      integration. Replace the current fast-forward-only rule where necessary
      so integrating the first task does not make the second task
      unrecoverably stale.
- [ ] Queue/task transitions for concurrently active work do not lose another
      task's state. The procedure defines where reservation, completion,
      review, and archive mutations occur and how conflicts in shared
      governance files are handled.
- [ ] Worktree cleanup happens only after successful integration: remove the
      linked worktree and then the local task branch. Failure, review changes,
      cancellation, or blocked integration retains recoverable task state and
      documents the permitted cleanup path.
- [ ] Automated tests create two temporary task worktrees, modify them
      independently, switch the primary checkout's branch during one task,
      and prove that both task branches can be validated and integrated
      serially without cross-worktree changes or lost governance state.
- [ ] Managed-template changes include the required migration and capability
      marker/baseline updates so existing adopters receive the new behavior
      through `meridian upgrade`, not only through fresh initialization.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | Meridian's local Lean Delivery execution and Git contract. |
| `templates/workflows/lean-delivery/` | Generated Lean Delivery task and Git procedure. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Governed roles, Git workflow, and integration contract. |
| `templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md` | Worktree creation and implementation boundary. |
| `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | Review/remediation use of the isolated task worktree. |
| `templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md` | Orchestrator routing, ownership, and cleanup. |
| `templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md` | Reviewer checkout and integration instructions. |
| `templates/workflows/governed-sdd/docs/PULL_REQUEST_POLICY.md` | Parallel-safe integration and forge rules. |
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Durable branch, worktree, base, and commit handoff. |
| `scripts/meridian.py` | Any bounded helper needed to prepare, verify, integrate, or clean up worktrees. |
| `migrations/`, `tests/` | Adopter delivery and automated parallel-worktree scenarios. |

## 🧩 Technical Context

- **Current Lean Delivery behavior**: no branch or worktree is required, so an
  agent may implement directly in the developer's checkout.
- **Current Governed SDD behavior**: the workflow says "dedicated
  branch/worktree", but then instructs the implementer and reviewer to share
  the implementer's primary checkout and to use `git switch`. The contract
  neither creates nor verifies a linked worktree, so a developer branch switch
  can alter the active agent's filesystem.
- **Current integration behavior**: Governed SDD requires `main` to be an
  ancestor of the task branch and permits only fast-forward integration. If
  two branches start from the same `main`, integrating either one advances
  `main` and makes the other fail the ancestry gate with no permitted recovery.
- **Desired behavior**: worktree isolation protects active work; dependency
  gates decide what may run concurrently; and a serialized, non-rewriting
  integration protocol combines independently reviewed branches safely.

## 🔨 Suggested Implementation

1. Define the shared worktree lifecycle and naming contract once, then route
   both workflow modes to it without importing Governed SDD review states into
   Lean Delivery.
2. Add the smallest mechanical helper needed to create and verify linked
   worktrees and to refuse checkout/branch mismatches. Keep Git operations
   explicit and testable; do not rely on host-specific worktree allocation.
3. Replace primary-checkout implementation/review instructions throughout the
   Governed SDD routing documents. Preserve fresh-session review and
   one-writer ownership.
4. Define a serialized integration transaction that preserves reviewed task
   commits, validates the combined tree, and aborts cleanly on conflict or
   failure.
5. Add temporary-repository integration tests, then ship the template changes
   through the normal migration/capability-baseline mechanism.

## ⚠️ Constraints and Considerations

- Worktree isolation must not imply that dependency-related or overlapping
  tasks are safe to run concurrently. Dependency readiness and relevant-file
  collision checks remain separate gates.
- Do not delete a task worktree or branch when implementation, review,
  validation, or integration is incomplete.
- Do not make the primary checkout's current branch an invariant during
  implementation or review.
- Do not weaken Governed SDD's independent-review, evidence, or forge gates.
- Do not add reviewer roles or governed lifecycle states to Lean Delivery.
- Because this task changes deterministic workflow and integration behavior,
  resolve the `PROJECT_WORKFLOW.md` mode requirement before implementation;
  do not silently implement a Governed SDD-class change under ambiguous Lean
  Delivery authority.
- Repository text is English-only.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 015, 039, 046, 047, and transitively every other open task

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/051-enforce-isolated-task-worktrees.md)"$'\n\nExecute this task in the current project.'
```
