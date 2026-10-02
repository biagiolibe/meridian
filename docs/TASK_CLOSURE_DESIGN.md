# Task Closure Design

Status: decided by task 100. This document designs a closure that finishes by
itself; it changes no script, template, migration, or workflow rule. The
implementation follow-ups are listed at the end.

## Problem

The developer reports that closing an assigned task "does not run automatically
and stops for the most varied reasons", and that the agent often stops before
integrating only because it wants authorization. Closure here means everything
after the implementation is written: validation, completion records,
integration into `main`, the required push of `main`, and cleanup.

Goal: after `Proceed with <TASK-ID>`, a task either reaches cleanup without a
human step, or stops exactly once with one named reason and a state from which
one command resumes it.

## Evidence labels

- **Observed**: reproduced from this repository by a command listed in the
  survey method.
- **Reported**: stated by the developer and not reproducible from this
  repository.
- **Unverified**: depends on host behavior that no run in this task exercised.
  Nothing below is presented as proven that was not run.

## Closure-stop survey

Collected on 2026-10-02 at `main` `601e7f7`. Counts are tasks unless stated.

### Survey method

```bash
ls tasks/handoffs/*.md | wc -l                                  # 53
grep -l "Integration decision" tasks/handoffs/*.md | wc -l      # 11
grep -l "osacompile\|XPC" tasks/handoffs/*.md                   # 086 094 095 097 098 099
git log --since=2026-09-20 --format='%h %s' | grep -iE "refresh .*after rebase|restore .*base commit"        # 7
git log --since=2026-09-20 --format='%h %s' | grep -iE "bind .*handoff"                                      # 6
git log --since=2026-09-20 --format='%h %s' | grep -iE "correct task .* handoff|full commit ids|machine-specific|update task .* handoff evidence|reconcile"   # 8
git show --stat 967a735 68269df 3dc19aa
git branch --merged main | grep task-                           # 15 branches
git worktree list                                               # 3 retained task worktrees
```

Each handoff was then read for the lines the commands matched.

### Causes

| # | Cause | Tasks affected | Label | Evidence and status |
|---|-------|----------------|-------|---------------------|
| S1 | `osacompile` fails with an XPC `Connection invalid` in the agent sandbox, so the full suite cannot pass there and the developer confirms the result by hand | 4 (094, 095, 097, 098) | Observed | Each handoff records the failure and a developer confirmation; 097 also records an authorization to treat the full-suite requirement as satisfied. Task 099 skips the test by name (done). Differs from the task statement: handoff 086 introduced the test and records `exit 0, 407 tests OK`, so it is not an instance. |
| S2 | Shared governance files (`PROJECT_PLAN.md`, `tasks/QUEUE.md`) conflict when `main` advanced after the task started | 3 confirmed (063, 086, 097); 1 probable (015); 3 unverified (067, 068, 087) | Observed / Unverified | 063: `Integration decision: BLOCKED`, `git merge --no-ff --no-commit task-063` conflicted in `PROJECT_PLAN.md`, resolved only after explicit developer authorization. 086: rebased onto `68269df` to resolve a `PROJECT_PLAN.md` conflict. 097: merged `main` and resolved plan rows after explicit authorization. 015: the developer authorized preserving both task states after task 054 became a prerequisite on `main`; the conflict is not named. 067, 068, 087 were rebased (`refresh … after rebase`), but their handoffs do not record why. |
| S3 | Handoff facts go stale after a rebase or after `main` advances | 4 (067, 068, 086, 087); 7 commits | Observed | The seven `refresh … after rebase` and `restore … base commit` commits. |
| S4 | A completion handoff cannot contain the SHA of the commit that carries it, so the commit is bound by a later commit | 5 (074, 075, 076, 078, 079); 6 `Bind … handoff to validated completion commit` commits | Observed | Task 088 defined the descriptive form after one adopter report; the 6 commits predate it. Template-only; no CLI generates these facts. |
| S5 | Other handoff corrections | 8 commits (`correct 086 validation evidence`, `use full commit ids 087`, `remove machine-specific path 079`, `reconcile 079`, `update handoff evidence` for 049, 050, 062) | Observed | Reconciling the task's "eleven handoff-repair commits": that figure is not reproducible from any single stated command. With the definitions above the tally is 7 + 6 + 8 = 21 repair commits since 2026-09-20; this design uses the reproducible numbers. |
| S6 | A worktree is never prepared when `Proceed with` is typed into a session in the primary checkout, so the implementer stops at `missing-state` | 3 occurrences in one adopter project | Reported | Quoted in task 097; not reproducible here. Lean Delivery already prepares its own worktree; Governed SDD was fixed by task 097 and migration 056 (done). |
| S7 | The `release.py publish` workflow lookup races the workflow run and reports a false failure after `main` and the tag are pushed | 1 (the v1.2.1 release) | Reported | Task 096 (open). It affects release publication, not task closure; it is listed because it ends the same push sequence with a misleading failure. |
| S8 | The agent stops to ask for authorization before integrating or pushing | not countable | Reported | No handoff records the agent asking. Recorded developer authorizations at closure: conflict resolution (015, 063, 097) and test-environment confirmation (094, 095, 097, 098). Task 054's authorization was for `--apply` on user configuration and is not counted. `PROJECT_WORKFLOW.md` contains no sentence that `Proceed with` authorizes integration or the push of `main`. Observed on this machine: `.codex/rules/meridian.rules` allows `git push` and `meridian worktree integrate stage\|finalize\|abort`, while `~/.claude/settings.json` has no `permissions` and the project's ignored `.claude/settings.local.json` allows only three setup commands, so neither command is allowlisted for Claude Code here. That Claude Code then prompts is Unverified; it is the documented default and was not run. |
| S9 | Closure leaves residue | 15 merged local task branches still exist; 3 task worktrees (067, 094, 099) are still registered | Observed | `cleanup` was not run or not recorded for them. The reason is Unverified. At survey time `main` equals `origin/main`, so no push was pending. |
| S10 | Required validation exceeds the host command limit and is interrupted without an exit status | 1 (101) | Reported | Task 101 reports a host limit of about 30 seconds against a full suite of about 90 seconds; its handoff records a developer-run full suite at 105.431 seconds. This task did not measure the host limit or detached-process survival. |
| S11 | `integrate stage` blocks the task-record archive rename required by the workflow | 1 (101) | Observed | Task 101's recorded `stage` block named the task-relevant tree change; Task 111's regression sequence reproduces the archive-rename cause and implements the exact-rename bridge. Task 063's earlier `BLOCKED` integration was a related but different shared-governance-file conflict (S2), not another archive-whitelist count. |

### Hypothesis: new tasks committed to `main` drive the governance conflicts

Tested on the three triggering `main` commits that the handoffs identify
(063's `967a735`, 086's `68269df`, 087's `3dc19aa`). All three are task
registration commits: each adds one task file and changes only
`PROJECT_PLAN.md` (+1 line) and `tasks/QUEUE.md` (+10 lines). The hypothesis is
supported for the inspected cases. The 097 trigger was not inspected, and
the share of all `main` commits touching those files (124 of 135 first-parent
commits since 2026-09-20) does not discriminate, because every integration
touches them.

## Decision 1 — Authorization model

`Proceed with <TASK-ID>` is the developer's standing authorization for the
whole lifecycle through integration into `main`, the required push of `main`,
and cleanup, when every gate passes. The stop in S8 is a missing statement of
authority, not a missing command rule: the Codex rules already allow `git push`
and `integrate stage|finalize|abort`.

Rule text for `PROJECT_WORKFLOW.md` (both workflow modes):

> ## Authority of `Proceed with`
>
> `Proceed with <TASK-ID>` authorizes that task's whole lifecycle when every
> gate passes: implementation and validation on the task branch; completion and
> archive records; `meridian worktree integrate stage`, the selected candidate
> validation, and `integrate finalize` or `abort`; one plain `git push origin
> main` of the resulting integration; and `meridian worktree cleanup`. Do not
> ask for confirmation at any of these steps. When a gate fails, stop once with
> `BLOCKED <reason>` and the resume command.
>
> `Proceed with <TASK-ID>` also authorizes one plain `git push origin
> task-<TASK-ID>` when needed to obtain `T1_CI` validation for that task commit.
>
> The authorization never covers: creating, moving, or pushing a tag;
> publishing a release; a force push or any push that deletes or mirrors
> references; rewriting history (amend of pushed commits, rebase, reset,
> cherry-pick); deleting an unmerged branch or removing a worktree by force;
> bypassing a required independent review; resolving a textual conflict; or
> work on any other task.

Consequences recorded for the follow-ups:

- The rule takes effect only when it lands in the workflow documents. Until
  then an agent has no durable authority for the push of `main`, including in
  the session that wrote this design.
- The Codex rule `git push` is broader than the authority: it also matches a
  tag push. The follow-up narrows it to `git push origin main` and leaves other
  pushes to prompt. Rule precedence between a narrow allow and a broad prompt
  is Unverified and the implementing task must test it.
- Claude Code needs a project-scoped allowlist for the same commands (S8). It is
  offered through the existing consented `meridian setup`, never written
  silently.

## Decision 2 — Shared governance files

Task branches stop editing `tasks/QUEUE.md`, `tasks/QUEUE_ARCHIVE.md`, and
`PROJECT_PLAN.md`. A task branch edits only its own task record, its archived
task file under `tasks/done/`, and its handoff. Queue status, plan status, and
phase archival are applied once, on the integrated tree, by `integrate stage`
after its no-commit merge, so the candidate tree that is validated already
contains them. The step is deterministic text editing of known row shapes by
Meridian's own code; it executes no project-provided command.

Why this removes the observed conflicts: S2's triggers are registration commits
that touch only these files. A branch that does not edit them cannot conflict
with them.

Representation of `[/]`: it is derived, not committed. A task is in progress
when its canonical branch exists, its worktree is registered, and its record is
not yet under `tasks/done/`; the console already derives effective state this
way (tasks 076 and 084). The queue file keeps `[ ]` until closure applies `[x]`.
Cost: the queue no longer shows `[/]` to a plain reader of `main`; the console
and `closure-status` do.

Tasks already in flight: a branch that already carries `[/]` or `[x]` edits is
finished under the old rule. The closure step is idempotent: when a row already
holds the target text it is a no-op, and a textual conflict in these files keeps
today's `BLOCKED` behavior. No in-flight branch is rewritten.

Governed SDD keeps its richer statuses in the task record; the same step maps
the integrated outcome to the queue row. Phase archival keeps today's condition:
the section is moved only when every row in it is `[x]` on the integrated tree.

## Decision 3 — Integration when `main` has advanced

No step needs a rebase. Integration already merges the task branch into `main`
with `git merge --no-ff --no-commit`, so a task branch is never rebased onto
`main`. What changes is who computes the facts that a moved `main` makes stale:

- `integrate stage` recomputes, from Git, the validated base, the current `main`
  tip, the paths changed on `main` since the validated base, and their overlap
  with the task's changed paths. Hand-typed `main_advanced_*` fields can only
  raise the validation scope, never lower it.
- No overlap and no declared dependency: `REUSE` or `BOUNDED` as today. Overlap
  with a task path, a declared dependency, or a behavioral surface: `FULL`
  combined-tree validation, run by the agent on the candidate tree.
- A textual conflict outside the closure-owned files is the only remaining
  integration conflict. The agent runs `integrate abort` and stops with
  `BLOCKED integration-conflict <paths>`. It does not resolve the conflict:
  resolving another task's content is outside the authorization (Decision 1).
  The branch and worktree are retained, so the resume is a developer-authorized
  merge-forward of `main` into the task branch followed by revalidation.

## Decision 4 — Handoff facts

Facts a command can derive are collected by a command instead of typed:

| Fact | Source |
|------|--------|
| Task branch, relative worktree, base commit | `meridian worktree prepare` / `check` (existing) |
| Validated task commit, validated base commit, changed paths | A new evidence command reading Git at the moment validation is recorded |
| Validation commands and exit codes | Recorded by the evidence command from values the agent passes after running each command; the command never runs them |
| Full-validation decision | `integrate stage` (Decision 3) |

The machine evidence is an untracked JSON file under the lifecycle state
directory (or the scratchpad), which is already the stage input. Because it is
not committed, it can hold full SHAs without the self-reference problem (S4).
The tracked handoff stays a human-readable summary and uses task 088's
descriptive form for the commit that carries it (`same as the implementation
commit`, or the task commit named by subject and branch); a later lifecycle-only
correction names earlier commits by full SHA and describes only itself. Per
migration 057, `meridian worktree check` and `meridian execution handoff-check`
resolve commits from Git rather than from handoff prose, so removing typed SHAs
from the evidence does not weaken either check. The existing execution evidence
profile (`docs/EXECUTION_EVIDENCE_PROFILE.md`) must be read by the implementing
task before it chooses the command's home.

## Decision 5 — Closure procedure

One ordered procedure runs from the validated task commit to cleanup. Each stop
has one reason and an idempotent resume; rerunning from the top performs only
what Git and lifecycle state show is undone.

| Step | Action | Stop reason | Resume |
|------|--------|-------------|--------|
| C1 | Verify acceptance criteria | `ACCEPTANCE_UNMET` | Fix, rerun C1 |
| C2 | Run task validation and baseline in the task worktree | `VALIDATION_FAILED` (a named sandbox skip is not a failure; Decision 6; timeout evidence follows Decision 7) | Fix, rerun C2 |
| C3 | Commit completion records on the task branch (task file to `tasks/done/`, handoff) | `REVIEW_REQUIRED` when an independent review is declared (Decision 9) | After approval, continue at C4 |
| C4 | `meridian worktree check` from the prepared worktree | `WRONG_WORKTREE` | Restart in the path `prepare` returned |
| C5 | Record machine evidence (Decision 4) | `EVIDENCE_INCOMPLETE` | Record the missing field |
| C6 | In the primary checkout, require a clean tree and `main` equal to `origin/main`; `integrate stage` | `PRIMARY_DIRTY`, `MAIN_BEHIND_ORIGIN`, `LEASE_HELD`, `INTEGRATION_CONFLICT` | Resolve the named condition; an active integration is resumed at C7 or aborted |
| C7 | Run the selected candidate validation outside the lifecycle command | `CANDIDATE_VALIDATION_FAILED` | `integrate abort`; fix on the task branch; rerun from C2 |
| C8 | `integrate finalize` with candidate-bound evidence | `EVIDENCE_MISMATCH` | `integrate abort`; restage at C6 |
| C9 | `git push origin main` | `PUSH_REJECTED` (origin advanced during integration) | No force and no rebase: local `main` is ahead by the merge commit; the developer decides |
| C10 | `meridian worktree cleanup` | `CLEANUP_BLOCKED` | Rerun after the named condition clears; the command is idempotent |

The only stops that need a human decision by design are `INTEGRATION_CONFLICT`
outside closure-owned files, `PUSH_REJECTED`, and a declared review. Everything
else is a failed gate with a mechanical resume. Lifecycle commands never run
task-controlled code: C7's validation is run by the agent between `stage` and
`finalize`, exactly as `PROJECT_WORKFLOW.md` requires today.

A read-only `meridian worktree closure-status <TASK-ID>` derives the current
step, the stop reason if any, and the resume command from Git and lifecycle
state alone, so a resumed session does not rely on the previous session's
memory. Every stop prints one line:
`BLOCKED <REASON>; resume: <command>`.

`MAIN_BEHIND_ORIGIN` turns the push race (`PUSH_REJECTED`) into an earlier,
cheaper check; it cannot remove the race window, so C9 remains.

## Decision 6 — Validation environment

A check that cannot run in the sandbox is handled by a named skip, as task 099
does for `test_split_payload_compiles_as_applescript`. The handoff records
`Validation skips:` with the test name, the stated reason, and the command that
reported it. A skip is accepted only when the skip is named by the test itself
and no acceptance criterion depends solely on the skipped check; otherwise it is
`VALIDATION_FAILED`.

The developer's full-suite run outside the sandbox is a recorded confirmation,
not a gate. The agent never stops to request it. If the developer volunteers
the result it is recorded as a dated line in the handoff. An unnamed failure,
for example an unexpected `osacompile` error that the skip does not match, still
stops closure.

## Decision 7 — Validation states and proof levels

Task 101 reported a host command limit of about 30 seconds, while its required
full suite took about 90 seconds. The host interruption returned no exit status.
This is **Reported** host behavior, not a measured host limit. It is distinct
from an observed failed test and from Decision 6's named, test-specific sandbox
skip. Whether a detached process survives such an interruption is **Unverified**.

The verifier reports one of these states:

| State | Meaning | Integration consequence |
|-------|---------|-------------------------|
| `VALIDATION_RUNNING` | A recorded run has started but has no terminal result. | Never integrates. |
| `VALIDATION_UNAVAILABLE` | Required validation cannot currently be obtained, for example because CI has no run or the host interrupted the command without an exit status. | Never integrates unless a later permitted proof produces `VALIDATION_PASSED`. |
| `VALIDATION_FAILED` | A terminal validation result is non-zero, invalid, or incomplete. | Never integrates. |
| `VALIDATION_PASSED` | A verifier accepted a terminal, commit- and tree-bound record at a permitted proof level. | May integrate, subject to every other closure gate. |

The permitted proof levels are ordered by what they establish, not by trust in a
sentence:

| Level | What it proves | What it does not prove | Integration |
|-------|----------------|------------------------|-------------|
| `T1_CI` | The repository's configured CI reported success for the exact commit and tree. | It does not prove tests omitted by that CI environment, such as macOS-only tests on Linux. | Allowed. A task may use the authorized single `git push origin task-<TASK-ID>` from Decision 1 to obtain it. |
| `T2_SHARDED` | Every deterministic shard for one tree completed successfully with the same total and digest, covering the discovered suite. | It does not prove that a different tree, undiscovered tests, or an external environment passed. | Allowed. |
| `T3_ATTESTED` | The developer made a dated statement about the exact commit and tree. | It is not independently executed, cryptographically signed, or unforgeable proof. | Allowed only when both `T1_CI` and `T2_SHARDED` are impossible; the handoff must label the result `T3_ATTESTED` and state why those levels were impossible. |

A partial run, a targeted test, or an interrupted run with no exit status never
passes at any level. They remain `VALIDATION_RUNNING`,
`VALIDATION_UNAVAILABLE`, or `VALIDATION_FAILED` according to their record; they
cannot be renamed into a skip or a pass.

Meridian provides a read-only verifier and a deterministic sharded test runner;
it provides no generic `meridian validation run` command or other generic
command executor. Its evidence is an attestation bound to a commit and its Git
tree, not unforgeable proof. The verifier checks the supplied record and Git
facts without running a test, shell, hook, network call, or project command.

## Decision 8 — Post-validation lifecycle boundary

After validation, allowed lifecycle paths are derived from the resolved task
identity, never from an evidence file. The active task record may be retained,
or archived only as one exact 100% Git rename to its matching
`tasks/done/<same-file-name>` path. An already archived record is idempotently
accepted. Every other deletion, addition, cross-task path, destination, or
content-changing rename is blocked. The evidence fields remain input to
interaction analysis; they cannot widen this lifecycle boundary.

`integrate stage` computes this boundary read-only before it acquires its lease.
On a blocked comparison it creates no lease or lifecycle state, changes no ref,
and starts no merge. This is a bridge only: Tasks 103 and 104 will move queue,
plan, and phase-archive edits from task branches into `stage`, removing those
post-validation task-branch changes.

There is one bootstrap for records that must archive themselves. Until the
unfixed `stage` can accept the archive rename, Task 111 and Task 101 close with
the archive applied in a record-only commit on `main` after integration, or by
an alternative explicitly recorded by the developer. This one-time sequence is
not a bypass of the boundary and does not authorize a different deletion or
addition.

## Decision 9 — Review gates

A task that declares an independent review requirement (`Review: REQUIRED` in
Governed SDD, or an equivalent declaration in a Lean task record) stops at C3
with `REVIEW_REQUIRED`. This is a gate, not a request for authorization: the
agent states it once and does not ask whether to skip it. Lean Delivery tasks
and Governed `Review: NOT_REQUIRED` tasks run through C10 without stopping.

Display: the console shows the stop reason in the task's state and its next
action (for example `review pending`, `integration-conflict`, `push-rejected`,
`cleanup`). `closure-status` is the single source for both the console and the
agent's final report. The Governed reviewer-integrator keeps its existing
role: it performs C6 to C10 after approving.

## Decision 10 — Rollout

| Surface | Change |
|---------|--------|
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md`, `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | Add the authority rule, the closure procedure, and the governance-file ownership rule; update the git-workflow capability version |
| This repository's `PROJECT_WORKFLOW.md`, `CLAUDE.md`, `AGENTS.md` | Same wording, through the managed-capability path |
| `meridian worktree` | New `closure-status` and an evidence command; `integrate stage` recomputes main-advance facts, checks `main` against `origin`, and applies the closure step |
| `meridian setup` / `codex doctor` | Narrow the push rule; offer the Claude Code allowlist; report missing authority |
| Console | Derive `[/]` and show stop reasons |
| `docs/WORKTREE_LIFECYCLE.md` | Document the new commands, the closure step, and the stop reasons |
| Migrations | One migration per workflow mode (next free number after 057), with marker baselines and upgrade tests |

This is template-changing for both workflow modes (Lean Delivery and Governed
SDD), so the release is a template-changing release with Upgrade notes.
Adopters on older baselines receive the new text through the ordinary migration
chain and keep their old behavior until they upgrade; the CLI changes are
additive and the old hand-written evidence still validates. Tasks in flight are
finished under the rules they started with (Decision 2). The 15 residual merged
branches and 3 retained worktrees from S9 are not touched by this design; the
developer can retire them one task at a time with the existing `cleanup`.

## Rejected alternatives

| Alternative | Reason rejected |
|-------------|-----------------|
| `merge=union` attribute for the governance files | Union merging concatenates both sides of a row edit, so two tasks closing different rows silently produce duplicated or contradictory rows, and a `[ ]`/`[x]` disagreement on one row is kept as two rows. It hides exactly the conflict the workflow must surface, and it does not help archival moves. |
| Letting the agent rebase | The rule forbids `rebase`, `reset`, and `cherry-pick`. A rebase rewrites the validated commit, invalidating every SHA in the evidence (S3), and the merge path already integrates a moved `main` without it. |
| One lifecycle command that runs the tests and closes the task | Lifecycle commands never execute project-provided code; that boundary is what lets hosts allowlist them safely. A command that runs tests would need the sandbox escapes S1 shows are already a problem. |
| A generic `meridian validation run` executor | It would execute an arbitrary project command inside a lifecycle tool, defeating the read-only verifier and the command boundary. |
| Allowing any post-validation change under `tasks/` | It would turn a task archive exception into permission to add, delete, or alter another task's records. The identity-derived exact rename is the narrow bridge. |
| Taking the stage whitelist from an evidence file | Evidence is supplied by the task and describes interaction analysis; it cannot authorize mutable paths. Identity and Git's rename-aware comparison remain authoritative. |
| Treating a timeout as a pass or a skip | A host interruption with no exit status proves neither success nor a named test-specific skip. It must remain unavailable or running until permitted evidence exists. |
| A fresh developer confirmation at every closure step | It is the failure being fixed (S8). One standing authorization with an explicit exclusion list keeps the dangerous actions gated and removes the rest. |
| The agent resolving governance conflicts by reading both sides | It chooses one task's state over another's, which the workflow forbids; Decision 2 makes the conflict structurally impossible instead. |

## Follow-up implementation tasks

Each task is at most about two hours and is queued in Phase 44.

| ID | Task | Depends on | Notes |
|----|------|------------|-------|
| 111 | Let `integrate stage` accept the exact archive rename of the task record | 055, 063 | First: it unblocks Task 101's archive bootstrap and establishes Decision 8's narrow comparison. |
| 101 | Add read-only `meridian worktree closure-status` that reports the closure step, stop reason, and resume command | 100, 111 | After 111 so its own closure can use the archive bridge. |
| 102 | Add the evidence command and make `integrate stage` recompute main-advance facts from Git | 100, 111 | After 101 in the rollout order; 111 and 102 touch the same stage function, so 111's archive boundary lands first. |
| 112 | Add a sharded test runner with a coverage proof | 100 | After 102 in the rollout order; it provides `T2_SHARDED`. |
| 113 | Add the validation evidence record and a read-only verifier | 112 | It verifies the shard proof and defines the four states. |
| 114 | Validate task branches in CI and capture the result as evidence | 113 | It produces `T1_CI` records in the schema that 113 verifies. |
| 103 | Apply queue and plan row status deterministically during `integrate stage` | 102 | Decision 2; idempotent |
| 104 | Apply phase archival to `QUEUE_ARCHIVE.md` during `integrate stage` | 103 | Decision 2 |
| 108 | Add the `Validation skips` handoff field and its check | 099, 100, 113 | After 113 so handoffs can distinguish the new validation evidence from named skips. |
| 105 | Derive `[/]` and show closure stop reasons in the console | 101, 103 | Decisions 2 and 9; after 108 in the rollout order so validation states are stable. |
| 106 | Narrow the Codex push rule and offer the Claude Code allowlist through `meridian setup` | 100 | After 105 in the rollout order; it implements the branch-push authorization boundary from Decision 1. |
| 107 | Block `integrate stage` when `main` is behind `origin` and report a pending push | 101 | After 106 in the rollout order; it completes the closure authority path before rules ship. |
| 109 | Ship the Lean Delivery rules and migration | 101, 102, 103, 104, 106, 107, 108, 113 | Decisions 1, 2, 5, 6, 7, 8; template-changing |
| 110 | Ship the Governed SDD rules and migration | 109, 113 | Decision 9; keeps `REVIEW_REQUIRED` as a gate |

The required execution order is 111, then 101, then 102, 112, 113, 114, 103,
104, 108, 105, 106, 107, 109, and 110. The dependency and rollout reasons in
the table constrain this order; tasks with fewer declared prerequisites remain
ordered here to keep the validation and closure semantics coherent.

## Out of scope

Implementing any part of this design, changing workflow templates or
migrations, the console, the release command, and Tasks 088, 096, 097, and 099,
which this design depends on but does not replace.
