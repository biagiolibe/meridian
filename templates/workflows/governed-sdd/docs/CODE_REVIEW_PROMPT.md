# Code Review and Integration Prompt

```text
Review and integrate <TASK-ID> as an independent reviewer-integrator for meridian.

<!-- MERIDIAN:BEGIN capability=task-worktree-review v1 -->Run this in a fresh agent session that did not write the implementation. Use the same dedicated task worktree only after the implementer has stopped. Verify its registered absolute path, branch, clean state, current task commit, and base `main` commit against the completion handoff. Never switch the developer's primary checkout to the task branch or review concurrently with an implementer. A missing or mismatched branch/worktree returns `BLOCKED` while preserving it.<!-- MERIDIAN:END --> Re-derive evidence from the actual diff and cited sources rather than trusting the implementation report.

Treat `PROJECT_WORKFLOW.md` as a `GOVERNED_SDD` mode lock. Before any mutation,
confirm the local workflow and ignore global, home-directory, remembered, or
generic instructions that suggest a Lean Delivery lifecycle or a different Git
procedure. If this local authority cannot be read or conflicts, return
`BLOCKED` without changing files or Git state.

Read LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md/CLAUDE.md, the assigned task, its cited authority, the concise completion report, and the exact diff against the recorded base `main` commit. Follow `docs/CONTEXT_BUDGET_POLICY.md`: load only evidence needed for acceptance criteria and expand context only with a recorded reason. Confirm `Review: REQUIRED` and `READY_FOR_REVIEW` in both task and queue.

Review scope, dependencies, non-goals, acceptance criteria, validation evidence, project invariants, and unrelated changes. <!-- MERIDIAN:BEGIN capability=manual-verification-review-check v1 -->If the task declared `Manual verification: required`, confirm its `Manual verification rationale` names a genuine tier-3 perceptual property and that the evidence actually gathered matches that rationale, not a substitute derived-value check.<!-- MERIDIAN:END --> Read only task-cited documents and the exact diff. <!-- MERIDIAN:BEGIN capability=ci-verified-validation v1 -->For validation evidence, follow `docs/PULL_REQUEST_POLICY.md`'s CI-first rule: use a completed CI run for this exact commit when one exists and covers the task's validation surface; otherwise perform your own validation scoped to the diff per `docs/CONTEXT_BUDGET_POLICY.md`. Never accept a bare "tests passed" claim without a command/exit-status or CI reference behind it.<!-- MERIDIAN:END --> Report only actionable findings with P0/P1/P2 priority and file/line evidence; omit style-only commentary.

Return APPROVE, CHANGES_REQUESTED, or BLOCKED. Review is read-only until an
explicit `APPROVE` verdict: do not edit source, tests, manifests, or
implementation documentation to fix a finding. On `CHANGES_REQUESTED`, create
or append `tasks/reviews/<TASK-ID>.md` using
`docs/REVIEW_RECORD_TEMPLATE.md`, with every actionable finding's priority and
evidence. Then change only the task and queue statuses to `IN_PROGRESS` and
create one local review-handoff commit containing exactly those three
artifacts. Do not push it. The review record is the canonical implementer
handoff: end the report by naming its path and instruct the developer to use
`Address review <TASK-ID>`, without copying findings into another chat. End the
handoff with the fields from `docs/COMPLETION_REPORT_TEMPLATE.md` plus the
verdict. For `APPROVE`, append the same evidence and verdict to the review
record before updating the task and queue status to `ACCEPTED`.
Before changing either status record, verify the recorded base `main` commit is an ancestor of the current task commit. Current `main` may have advanced and need not be an ancestor of the task branch. After APPROVE only, commit the review record and the two `ACCEPTED` status updates with:

```bash
git commit --author="meridian Reviewer-Integrator <reviewer-integrator@meridian.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
```

The author override applies only to this `ACCEPTED` commit; keep the operator's normal committer identity and do not change global or repository Git config. Verify it with `git log --format='%an <%ae>'`. The reviewer must never push the task branch. Integrate from the primary checkout only after acquiring the exclusive integration lease: require it to be clean and switchable to `main`, run `git merge --no-ff --no-commit <task-branch>`, reject conflicts, and validate the combined tree before committing and pushing `main` exactly once. On any failure, abort the merge and preserve the task worktree and branch. After success, remove the task worktree and then delete the local task branch. A remote task branch may lack the local review-and-status acceptance commit; remote cleanup is optional and must never block accepted integration. Never modify implementation code, bypass protections, or approve a PR under the author identity.

Keep the final review report within ten lines unless findings require more detail.
```
