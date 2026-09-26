# Task 055 — Avoid duplicate full validation during worktree integration

> **ID**: `055`
> **Category**: Architecture / Workflow
> **Priority**: 🔴 P1
> **Estimate**: ~3–5h
> **Assigned to**: unassigned
> **Session**: 2026-09-26 integration-cost design

## 🎯 Objective

Remove the unconditional second full validation pass from final task-worktree
integration. A task must still complete its task-specific validation and
applicable project baseline checks in its isolated worktree, but integration
should reuse that evidence when it still describes the candidate tree and run
only a bounded integration gate by default.

Full combined-tree validation becomes an explicit escalation for material
interaction risk, stale evidence, or a task that declares it necessary. This
reduces repeated cost without treating a conflict-free merge as proof that the
combined behavior is correct.

This task changes the integration contract established by Task 051 and must
land before Task 054 extends the same worktree lifecycle.

## 📋 Acceptance Criteria

- [ ] Task completion records the validated task commit, its validated base
      `main` commit, the validation commands, and their successful evidence.
      Integration rejects missing evidence or a task branch whose relevant
      tree changed after validation.
- [ ] When current `main` still equals the validated base, integration reuses
      the task-worktree evidence and does not rerun the complete project
      baseline on the combined tree.
- [ ] Every integration still acquires the exclusive lease, verifies handoff
      and ancestry, requires clean participating worktrees, performs
      `git merge --no-ff --no-commit`, rejects conflicts, and runs a bounded
      integration gate before creating the merge commit.
- [ ] The default bounded gate contains `git diff --check` plus an optional
      project-declared fast integration smoke command. Absence of a smoke
      command is explicit and does not silently expand back to the complete
      baseline.
- [ ] Full combined-tree validation runs only when the task explicitly
      requires it, validation evidence is stale or cannot be matched to the
      candidate, current `main` has advanced with a material interaction in
      the task's declared files/dependencies/behavioral surface, or the bounded
      gate reports a failure requiring broader diagnosis.
- [ ] The contract defines material interaction conservatively and
      deterministically. An implementation may return `BLOCKED` when it cannot
      establish independence; it must not infer safety solely from Git's lack
      of textual conflicts.
- [ ] If current `main` advanced without a material interaction, integration
      records the comparison evidence and uses the bounded gate instead of the
      complete baseline.
- [ ] A failed bounded or full integration gate aborts the merge, releases the
      lease after the clean abort, and retains the task branch and worktree.
      Successful integration and cleanup semantics remain unchanged.
- [ ] Lean Delivery and Governed SDD use the same evidence-reuse and escalation
      semantics without weakening Governed SDD review independence, acceptance
      evidence, or forge gates.
- [ ] Tests cover unchanged-base evidence reuse, advanced-main independent
      changes, advanced-main interacting changes, stale task commits, missing
      smoke configuration, smoke failure, required full validation, and clean
      merge abort. They prove that the complete baseline is not invoked on the
      default evidence-reuse path.
- [ ] Managed-template changes include the required migrations, capability
      marker updates, and baseline updates for existing adopters.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | Local completion and integration contract. |
| `templates/workflows/lean-delivery/` | Lean validation-evidence and integration-gate contract. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Governed integration and acceptance rules. |
| `templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md` | Lifecycle integration authorization and failure behavior. |
| `templates/workflows/governed-sdd/docs/PULL_REQUEST_POLICY.md` | Combined-tree gate and forge boundary. |
| `templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md` | Reviewer-integrator instructions. |
| `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | Review-to-integration routing. |
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Validated commit, base, commands, and evidence handoff. |
| `scripts/meridian.py` | Any mechanical evidence comparison or integration preflight helper. |
| `tests/test_task_worktree_isolation.py` | Integration evidence-reuse and escalation scenarios. |
| `migrations/`, `tests/` | Managed adopter delivery and regression coverage. |

## 🧩 Technical Context

- **Current behavior**: a task runs its stated validation and applicable
  baseline checks in its worktree, then final integration merges with
  `--no-commit` and validates the complete combined tree again before creating
  the merge commit.
- **Cost problem**: the second complete pass is unconditional even when
  current `main` is exactly the validated base and the merge candidate has the
  same content already validated in the task worktree.
- **Safety boundary**: a clean Git merge detects textual conflicts but not all
  semantic interactions. Evidence may be reused only when its commit/base
  identity is known; an advanced `main` needs a deterministic interaction
  assessment and an explicit escalation path.
- **Desired behavior**: full validation remains mandatory before task
  completion, while integration normally performs only provenance checks,
  merge-conflict rejection, whitespace/diff hygiene, and an optional fast
  smoke check.

## 🔨 Suggested Implementation

1. Extend the durable handoff/completion evidence with validated task and base
   commits plus the commands and results already required for completion.
2. Define a small integration decision function with `REUSE`, `BOUNDED`,
   `FULL`, and `BLOCKED` outcomes and test its inputs independently from Git.
3. Replace unconditional combined-tree validation in both workflow modes and
   governed routing documents with that decision and its failure semantics.
4. Extend temporary-repository integration tests to observe which validation
   command ran for unchanged, independent, interacting, and stale candidates.
5. Deliver the managed text and schema changes through the normal migration
   and capability-baseline mechanism.

## ⚠️ Constraints and Considerations

- Do not remove task-worktree validation or permit completion with missing
  validation evidence.
- Do not equate a conflict-free merge or disjoint filenames with semantic
  independence when dependency, generated-file, configuration, schema, or
  shared-governance surfaces overlap.
- Do not run the full baseline merely because no smoke command is configured;
  report that the bounded gate consisted only of its mandatory checks.
- Do not create a merge commit after any integration gate fails.
- Keep the default path cheap, deterministic, and observable in the handoff or
  integration report.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED
Policy outcome: Host agents reuse valid task evidence and avoid an
unconditional complete validation rerun while preserving a deterministic
integration safety gate.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Host-neutral Meridian workflow | enforced | enforced | Updated workflow contract, evidence fields, and migration are installed. | Return `BLOCKED` when evidence identity or interaction safety cannot be established. |
| Claude Code plugin session | advisory | advisory | Updated plugin prompts and templates are installed. | Follow the project workflow manually without claiming runtime enforcement. |
| Codex trusted project session | advisory | advisory | Updated project instructions and rules are trusted and loaded. | Follow the project workflow manually; retain approval and sandbox boundaries. |

Evidence plan:
- Static: decision-table, template, migration, and marker tests cover every integration outcome.
- Host execution: temporary Git repositories prove command selection, clean abort, and evidence reuse across real worktrees.
- Manual activation: inspect one generated Lean project and one generated Governed SDD project after initialization or upgrade.

Completion evidence:
- Host-neutral Meridian workflow: unverified until the decision and real-Git integration tests pass.
- Claude Code plugin session: retained advisory.
- Codex trusted project session: retained advisory.

## 🔗 Dependencies

- **Depends on**: 051
- **Blocks**: 054 and transitively every other open task

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/055-avoid-duplicate-full-integration-validation.md)"$'\n\nExecute this task in the current project.'
```
