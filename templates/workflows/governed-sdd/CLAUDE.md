# [Project Name]

Read `PROJECT_WORKFLOW.md` before acting. It defines the governed SDD lifecycle, review policy, roles, and Git workflow for this project.

Follow `docs/CONTEXT_BUDGET_POLICY.md` for task-first context loading and reasoning selection. Use the assigned task as the navigation map, and use `docs/COMPLETION_REPORT_TEMPLATE.md` for the final handoff.

## Commands

```bash
# Fill in run, test, lint, and format commands for this project.
```

## Project invariants

- Add domain- and stack-specific invariants here.
- Treat accepted ADRs and task acceptance criteria as binding.

## Implementer-to-reviewer handoff

After validation, create the task commit and push the task branch exactly once. Record the branch name, implementation commit, and base `main` commit in the completion handoff. Leave the primary checkout clean and on the task branch; do not switch back to `main`.

The reviewer-integrator uses that same primary checkout in a fresh agent session that did not write the implementation. If the reviewer session starts on clean `main`, run `git switch <task-branch>`. If the branch is missing locally, or a dirty checkout prevents switching, return `BLOCKED` with the exact condition.

For `Review: REQUIRED`, the reviewer must never push the task branch. Before changing either status record, run `git merge-base --is-ancestor main <task-branch>`. If it fails, do not mark the task `ACCEPTED`; return `BLOCKED` with no fetch, rebase, non-fast-forward merge, or force-push recovery. If it passes, create the local status-only `ACCEPTED` commit, switch to `main`, fast-forward merge the task branch, push `main` exactly once, and delete the local task branch. For `Review: NOT_REQUIRED`, the implementer performs the same acceptance commit and main integration after validation. Owner acceptance is status-only and does not automatically integrate the branch.

## Reviewer-integrator identity on a single-operator project

Review independence and Git identity separation are both mandatory controls; neither substitutes for the other. The review session must not have written the code and must re-derive evidence from the actual diff and cited sources rather than trusting the implementation report. Only for the `ACCEPTED` commit, use the project-scoped reviewer-specific author override:

```bash
git commit --author="<PROJECT_NAME> Reviewer-Integrator <reviewer-integrator@<project-slug>.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
```

Keep the operator's normal committer identity. Do not change global or repository Git config. The override applies only to the `ACCEPTED` commit and can be verified with `git log --format='%an <%ae>'`.
