# Code Review and Integration Prompt

```text
Review and integrate <TASK-ID> as an independent reviewer-integrator.

Read PROJECT_WORKFLOW.md, AGENTS.md/CLAUDE.md, the assigned task, its governing documents, implementation report, and the exact diff against the base branch. Confirm `Review: REQUIRED` and `READY_FOR_REVIEW` in both task and queue.

Review scope, dependencies, non-goals, acceptance criteria, validation evidence, project invariants, and unrelated changes. Report only actionable findings with P0/P1/P2 priority and file/line evidence.

Return APPROVE, CHANGES_REQUESTED, or BLOCKED. After APPROVE only, update exactly the task and queue status to ACCEPTED, commit `docs: accept <TASK-ID>`, push, and merge the existing PR only if all required checks and forge gates pass. Never modify implementation code, bypass protections, or approve a PR under the author identity.
```
