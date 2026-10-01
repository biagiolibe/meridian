# Task 100 — Design hands-off task closure

> **ID**: `100`
> **Category**: Architecture / Design
> **Priority**: 🔴 P1
> **Estimate**: ~2.5h (decisions only; split the follow-ups if the survey grows)
> **Assigned to**: unassigned
> **Session**: Developer report that task closure and integration keep stopping

## Objective

The developer wants one assigned task to run to completion without manual
intervention: implementation, validation, completion records, integration into
`main`, the required `main` push, and cleanup. In practice the agent stops at
closure for many different reasons, and the developer has to repair or resume
the task by hand. Produce `docs/TASK_CLOSURE_DESIGN.md`: the evidence-based list
of why closure stops, and a decision for each cause, so that follow-up tasks can
implement a closure that finishes by itself and, when it cannot, stops once with
one named reason and a resumable state.

This task writes a design and the follow-up task records only. It changes no
script, template, migration, or workflow rule.

## Acceptance Criteria

- [ ] The design opens with a closure-stop survey built from repository
  evidence re-collected at task time (handoffs in `tasks/handoffs/`, commit
  history, and the developer's reports), counted per cause. It must include at
  least these observed causes and say how many tasks each affected: the
  `osacompile` XPC failure in the agent sandbox (handoffs 086, 094, 095, 098);
  integration `BLOCKED` by a conflict in `PROJECT_PLAN.md` and `tasks/QUEUE.md`
  after `main` advanced (handoff 063); handoff facts made stale by a rebase or
  by `main` advancing (the "refresh … after rebase" and "restore … base commit"
  repair commits); a handoff commit field that cannot contain its own SHA
  (Task 088); a worktree that was never prepared (Task 097); the publish
  workflow lookup race (Task 096); and the agent stopping to ask for
  authorization before integrating.
- [ ] **Authorization model.** The design decides, with the rule text it would
  add to `PROJECT_WORKFLOW.md`, whether `Proceed with <TASK-ID>` is the
  developer's standing authorization for the whole lifecycle through
  integration into `main`, the required push of `main`, and cleanup, when every
  gate passes. It records that `.codex/rules/meridian.rules` already allows
  `git push` and `meridian worktree integrate stage|finalize|abort`, so the
  stop is a missing statement of authority and not a missing command rule. It
  lists the actions that are never covered by that authorization: pushing or
  moving tags, publishing a release, force-pushing, rewriting history, deleting
  unmerged branches, and bypassing a required independent review.
- [ ] **Shared governance files.** The design decides whether task branches stop
  editing `tasks/QUEUE.md`, `tasks/QUEUE_ARCHIVE.md`, and `PROJECT_PLAN.md`, with
  queue status, archival, and plan updates applied once, deterministically, on
  the integrated tree during serialized integration instead of merged textually
  from each branch. It states how `[/]` in-progress state is represented (for
  example derived from the branch and the task record, as the console already
  does) and what it costs for tasks already in flight.
- [ ] **Integration when `main` has advanced.** The agent rule forbids `git
  rebase`, `git reset`, and `git cherry-pick`. The design decides how a task is
  integrated when `main` moved after validation (re-stage by the existing merge
  path, which facts are recomputed by `integrate stage` instead of hand-edited in
  the handoff, and when full combined-tree validation is required) so no step
  needs a rebase.
- [ ] **Handoff facts.** The design decides which handoff facts are collected
  by a command instead of typed (task, base, and validated commits, validation
  commands with exit codes), and how a commit can be identified without naming
  its own SHA, aligned with Task 088.
- [ ] **Closure procedure.** The design defines the complete ordered closure
  sequence, from the validated task commit to cleanup, as one procedure with
  named stop points, an idempotent resume rule for each, and one `BLOCKED`
  reason per stop. It respects the existing constraint that lifecycle commands
  never run task-controlled commands: validation of the candidate is run by the
  agent between `integrate stage` and `integrate finalize`, not inside a
  lifecycle command.
- [ ] **Validation environment.** The design decides how closure validation
  behaves where the sandbox cannot run a test (Task 099's named skip), what the
  handoff must record for a skip, and whether the developer's full-suite run
  outside the sandbox is a gate or only a recorded confirmation.
- [ ] **Review gates.** The design states that a Governed task with
  `Review: REQUIRED` still stops for the independent review (a gate, not a
  request for authorization), that Lean Delivery and `NOT_REQUIRED` tasks run to
  the end, and what the console and the next-action text show at each stop.
- [ ] **Rollout.** The design lists which workflow templates, migrations, CLI
  commands, and docs change; how tasks already in flight and adopters on older
  baselines are handled; and that the change is template-changing for both
  workflow modes (Lean Delivery and Governed SDD).
- [ ] **Rejected alternatives** are recorded with the reason, including at least:
  a `merge=union` attribute for the governance files; letting the agent rebase;
  moving closure into one lifecycle command that runs the tests; and requiring a
  fresh developer confirmation at every closure step.
- [ ] The design ends with a table of follow-up implementation tasks, each
  created as a numbered task file and added to `tasks/QUEUE.md` and
  `PROJECT_PLAN.md` with dependencies, in the style of Task 049. No follow-up is
  larger than about two hours.
- [ ] Claims that depend on host behavior (what an agent does without a stated
  authorization) are labelled as observed reports or unverified, and nothing is
  presented as proven that was not run.
- [ ] `python3 scripts/check_repository.py` passes. The task is
  documentation-only, so the unit test suite may be skipped, and the handoff
  records that skip.

## Relevant Files

| File | Role |
|------|------|
| `docs/TASK_CLOSURE_DESIGN.md` | New design document (the deliverable). |
| `docs/WORKTREE_LIFECYCLE.md` | Current `prepare`, `check`, `integrate`, and `cleanup` semantics. |
| `PROJECT_WORKFLOW.md`, `templates/workflows/*/PROJECT_WORKFLOW.md` | Current completion and integration rules to be quoted accurately. |
| `.codex/rules/meridian.rules` | Command approval rules the design must not contradict. |
| `tasks/handoffs/` | Evidence for the survey (063, 067, 068, 086, 087, 094, 095, 098). |
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | Style and structure reference for a design task. |

## Technical Context

- **Developer report**: closure "does not run automatically and stops for the
  most varied reasons"; the agent often stops before integrating only because it
  wants authorization.
- **Current rules**: `PROJECT_WORKFLOW.md` says reservation, completion,
  review, and archive edits are committed on the task branch, that a conflict in
  a shared governance file is an integration conflict that ends as `BLOCKED`, and
  that final integration is serialized in the primary checkout through
  `integrate stage`, separately recorded validation, and `integrate finalize` or
  `abort`, followed by `cleanup` after any required `main` push. No sentence says
  that the `Proceed with` trigger authorizes the push of `main` or the
  integration.
- **Observed evidence**: Task 063's handoff records `Integration decision:
  BLOCKED` because `main` advanced with a commit that added Task 064 and edited
  `PROJECT_PLAN.md` and `tasks/QUEUE.md`, and `git merge --no-ff --no-commit
  task-063` conflicted. Eleven handoff-repair commits appear in the history
  since 2026-09-20.
- **Constraint to keep**: one writer per task worktree, serialized integration,
  no force-push, no history rewriting by agents, and lifecycle commands that
  never run task-controlled code.
- **Hypothesis to test, not assume**: new tasks committed to `main` while other
  tasks are in flight contribute to the governance-file conflicts.

## Validation

- `python3 scripts/check_repository.py`
- Documentation-only: build and unit-test commands are skipped and the skip is
  recorded in the handoff.
- Evidence tier: the survey counts are program-derivable from the repository and
  are recorded with the commands that produced them; no manual evidence is
  required.

## Out of scope

Implementing any part of the design, changing workflow templates or migrations,
the console, the release command, and Task 097, 099, 088, or 096, which this
design may depend on but does not replace.

## Dependencies

- **Depends on**: 088, 097, 099 (read for their findings; the design is written
  against their intended outcome and updated if they change)
- **Blocks**: the follow-up tasks this design creates
