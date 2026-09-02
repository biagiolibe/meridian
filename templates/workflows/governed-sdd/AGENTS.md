# [Project Name] — Agent Rules

Read `PROJECT_WORKFLOW.md` before acting. It defines the canonical task lifecycle, review rules, roles, and Git workflow.

Work only on the explicitly assigned task. Before implementation, read the assigned task, its cited authority, its expected code surface, and `git status --short`; state a short plan and stop if unrelated changes or an unresolved higher-precedence conflict exist.

Run the task validation plus the project baseline checks recorded in `CLAUDE.md`/project documentation. Never claim completion when required validation fails.

## Execution policies

Apply `docs/CONTEXT_BUDGET_POLICY.md` for task-first context loading, progressive expansion, and reasoning selection. Use `tasks/TASK_BLUEPRINT.md` for new or materially revised tasks and `docs/COMPLETION_REPORT_TEMPLATE.md` for the completion handoff.

These documents define operating detail; this file remains the source for stable agent-wide rules and project invariants.

## Implementer-to-reviewer handoff

After validation, create the task commit and push the task branch exactly once. The completion handoff must record the branch name, implementation commit, and base `main` commit. Leave the primary checkout clean and on the task branch; do not switch back to `main`.

The reviewer-integrator uses that same primary checkout in a fresh agent session that did not write the implementation. If the reviewer session starts on clean `main`, run `git switch <task-branch>`. If the branch is missing locally, or a dirty checkout prevents switching, return `BLOCKED` with the exact condition.

For `Review: REQUIRED`, the reviewer must never push the task branch. Before changing either status record, run `git merge-base --is-ancestor main <task-branch>`. If it fails, do not mark the task `ACCEPTED`; return `BLOCKED` with no fetch, rebase, non-fast-forward merge, or force-push recovery. If it passes, create the local status-only `ACCEPTED` commit, switch to `main`, fast-forward merge the task branch, push `main` exactly once, and delete the local task branch. For `Review: NOT_REQUIRED`, the implementer performs the same acceptance commit and main integration after validation. Owner acceptance is status-only and does not automatically integrate the branch.

## Reviewer-integrator identity on a single-operator project

Both controls are mandatory and neither substitutes for the other:

- Review runs in a fresh agent session that did not write the code. Re-derive evidence from the actual diff and cited sources; do not trust the implementation report.
- Only for the `ACCEPTED` commit, use the project-scoped reviewer author override below, with the project's actual name and slug:

  ```bash
  git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
  ```

Keep the operator's normal committer identity. Do not change global or repository Git config. The override applies only to the `ACCEPTED` commit and can be verified with `git log --format='%an <%ae>'`.
