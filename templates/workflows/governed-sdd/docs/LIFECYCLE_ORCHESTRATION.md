# Autonomous Task Lifecycle Orchestration

<!-- MERIDIAN:BEGIN capability=lifecycle-orchestration v2 -->
`Run lifecycle <TASK-ID>` authorizes an orchestrator to carry one dependency-ready
task through implementation, independent review, requested-change remediation,
acceptance, and `main` integration without further developer prompts. It does
not authorize work outside that task or bypass a repository or forge gate.

The orchestrator is a coordination-only role. It does not edit implementation
artifacts, perform the substantive review, or reinterpret findings. It starts
an implementer and a reviewer-integrator as distinct sessions. The reviewer
session must be fresh and must not receive the implementer's conversation or
reasoning; it re-derives evidence from repository artifacts.

```text
Run lifecycle <TASK-ID>
  -> implementer: Proceed with <TASK-ID>
  -> reviewer: Review <TASK-ID>
       -> APPROVE: acceptance commit, fast-forward main, push main
       -> CHANGES_REQUESTED: implementer: Address review <TASK-ID>
                              -> reviewer: Review <TASK-ID>
       -> BLOCKED: stop and report the exact condition
```

The task file, queue row, Git commits, completion report, and the declared
review record (see `PROJECT_WORKFLOW.md`'s canonical locations) are the only
handoff interface. Worker messages
must be concise and structured as: verdict or state, task ID, commit SHA,
review-record path when present, validation result, and blocker when present.
The orchestrator passes only that information to the next worker; it never
copies findings between chats.

## Preconditions and stop conditions

Before delegation, confirm that the task is assigned, dependency-ready, and
that the checkout is clean. Use the task's declared reasoning profile for the
implementer and reviewer; use the lowest available reasoning profile for the
orchestrator. Do not run implementation and review concurrently in the same
worktree.

Continue automatically only while the current task and queue state permit the
next transition. Stop with `BLOCKED` when validation fails, authority is
ambiguous, the task branch or required local handoff commit is unavailable,
the worktree becomes dirty with unrelated changes, the ancestry check fails,
or an external forge approval is required but unavailable.

After two consecutive `CHANGES_REQUESTED` verdicts, stop and report `BLOCKED`
with the review-record path and unresolved findings. A developer may explicitly
restart the lifecycle after resolving the underlying scope or authority issue.

## Integration and forge gates

The `Run lifecycle` authorization includes the local review-and-status commit,
fast-forward integration, and the single `main` push only after `APPROVE` and
all repository checks pass. It does not fabricate an external approval. If the
forge requires an approval from a distinct authorized identity, leave the PR
open and report `BLOCKED` unless that independent identity has actually
approved it.

## Token discipline

The orchestrator reads only task status, the latest commit, and the latest
review-record attempt. Workers use task-first context loading. Do not recreate
prior chat context, repeat successful validation without a changed relevant
surface, or add a summarization agent between workers.
<!-- MERIDIAN:END -->
