# Autonomous Task Lifecycle Orchestration

<!-- MERIDIAN:BEGIN capability=lifecycle-orchestration v4 -->
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
       -> APPROVE: acceptance commit, validated merge commit on main, push main
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

Before delegation, confirm that the task is assigned and dependency-ready,
that its deterministic branch/worktree names do not conflict, and that the
dedicated task worktree is clean. Create or select that worktree before any
task mutation. The task's declared `Reasoning` value is the exact
permitted effort for both implementer and reviewer, not a minimum: configure
each fresh worker session to that value and stop before delegation if the
effective setting differs or cannot be confirmed. Never escalate either worker
automatically. Use the lowest available reasoning profile for the orchestrator.
Do not run implementation and review concurrently in the same worktree. Stop
the implementer before starting the fresh reviewer against that same task
worktree; neither worker uses the primary checkout.

Continue automatically only while the current task and queue state permit the
next transition. Stop with `BLOCKED` when validation fails, authority is
ambiguous, the task branch or required local handoff commit is unavailable,
the worktree becomes dirty with unrelated changes, its registered branch/path
mapping changes, serialized integration conflicts or fails combined-tree
validation, or an external forge approval is required but unavailable.

After two consecutive `CHANGES_REQUESTED` verdicts, stop and report `BLOCKED`
with the review-record path and unresolved findings. A developer may explicitly
restart the lifecycle after resolving the underlying scope or authority issue.

## Integration and forge gates

The `Run lifecycle` authorization includes the local review-and-status commit,
serialized `--no-ff --no-commit` integration, combined-tree validation, and
the single `main` push only after `APPROVE` and all repository checks pass. The
recorded base must be an ancestor of the task commit; current `main` may have
advanced through another accepted task. A dirty or unavailable primary
checkout blocks integration without changing the task worktree. A merge
conflict or validation failure is aborted and preserves the task branch and
worktree. Only successful integration permits removing the worktree and then
the branch. It does not fabricate an external approval. If the
forge requires an approval from a distinct authorized identity, leave the PR
open and report `BLOCKED` unless that independent identity has actually
approved it.

## Token discipline

The orchestrator reads only task status, the latest commit, and the latest
review-record attempt. Workers use task-first context loading. Do not recreate
prior chat context, repeat successful validation without a changed relevant
surface, or add a summarization agent between workers.
<!-- MERIDIAN:END -->

<!-- MERIDIAN:BEGIN capability=rejected-attempt-restart v3 -->
## Rejected-attempt restart after authority change

Use this procedure only when a `CHANGES_REQUESTED` finding explicitly cannot be
remediated without new or amended authority or task scope, and the developer
explicitly authorizes restart. Before any ref or status mutation, verify the
original branch, rejected exact tip, review record, handoff, validation evidence,
clean checkout, and available target names; also verify a separate tech-design
change amended authority and scope, received required independent review, is
`ACCEPTED`, and is integrated into `main`. Otherwise return `BLOCKED` with no
ref or status mutation.

In one atomic ref transaction, retain `archive/rejected/<normalized-task-id>-<attempt>`
at the rejected tip and create `retry/<normalized-task-id>-<attempt>` from accepted
`main`. Retain the archive and original branch with the review record, handoff, and
validation evidence. The retry's restart-handoff commit contains only that governance
evidence, applicable task/queue `IN_PROGRESS` state, the archive ref/tip, accepted
design commit, and an explicit statement that no rejected implementation artifact was
copied. Implement and validate afresh: never reset, rebase, amend, force-push,
cherry-pick, merge, or copy rejected implementation commits or artifacts. Independently
review the retry against its main base; resolve the authority finding only with the
accepted design commit and independently recreated implementation. Retain archive and
original branch after integration; only the retry branch has ordinary cleanup.

### Operator sequence

The reviewer first completes its local review-handoff commit on the rejected
task branch and leaves that branch intact. Once the checkout is clean, switch
to the current `main` with `git switch main`. Create the separate tech-design
branch from that current `main`, review and integrate its authority/scope
amendment, then invoke `Restart rejected <TASK-ID>` from the updated `main`.
The retry therefore starts from the accepted design base, not from the rejected
task branch.
<!-- MERIDIAN:END -->
