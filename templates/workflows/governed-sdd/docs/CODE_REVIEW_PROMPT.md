# Code Review and Integration Prompt

```text
Review and integrate <TASK-ID> as an independent reviewer-integrator.

Read PROJECT_WORKFLOW.md, AGENTS.md/CLAUDE.md, the assigned task, its cited authority, the concise completion report, and the exact diff against the base branch. Follow `docs/CONTEXT_BUDGET_POLICY.md`: load only evidence needed for acceptance criteria and expand context only with a recorded reason. Confirm `Review: REQUIRED` and `READY_FOR_REVIEW` in both task and queue.

Review scope, dependencies, non-goals, acceptance criteria, validation evidence, project invariants, and unrelated changes. Read only task-cited documents and the exact diff. Report only actionable findings with P0/P1/P2 priority and file/line evidence; omit style-only commentary.

Return APPROVE, CHANGES_REQUESTED, or BLOCKED. End the handoff with the fields from `docs/COMPLETION_REPORT_TEMPLATE.md` plus the verdict. After APPROVE only, update exactly the task and queue status to ACCEPTED, commit `docs: accept <TASK-ID>`, push, and merge the existing PR only if all required checks and forge gates pass. Never modify implementation code, bypass protections, or approve a PR under the author identity.

Keep the final review report within ten lines unless findings require more detail.
```
