# Task 115 — Record the validation-timeout and stage-whitelist decisions in the closure design

> **ID**: `115`
> **Category**: Architecture / Design
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Task 101 closure blocked by validation timeout and the stage whitelist

## Objective

Task 100 produced `docs/TASK_CLOSURE_DESIGN.md`. Closing Task 101 exposed two
causes it did not cover: a required validation that exceeds the agent host's
command limit, and `integrate stage` blocking the archive rename that the
workflow requires. Record both decisions in the design and align its follow-up
table, so Tasks 108 to 114 are implemented against one written source.

This task edits the design document and the queue rows it names. It changes no
script, template, or migration.

## Acceptance Criteria

- [ ] The closure-stop survey gains two causes with their evidence and counts at
  task time: a required validation that cannot finish within the host command
  limit (Task 101, the reported limit of about 30 seconds against a suite of about
  90 seconds), and the `stage` whitelist blocking the archive rename (Task 101,
  and the earlier integration `BLOCKED` of Task 063 as a related but different
  cause). Each is labelled observed, reported, or unverified.
- [ ] A new decision defines the validation states `VALIDATION_RUNNING`,
  `VALIDATION_UNAVAILABLE`, `VALIDATION_FAILED`, and `VALIDATION_PASSED`, and the
  proof levels `T1_CI`, `T2_SHARDED`, and `T3_ATTESTED`, with what each proves and
  does not prove. It states which levels allow integration, that a partial run, a
  targeted test, or an interrupted run with no exit status never does, and that
  `T3_ATTESTED` is allowed only when `T1_CI` and `T2_SHARDED` are impossible and
  is labelled in the handoff.
- [ ] The decision states that Meridian provides a read-only verifier and a
  sharded test runner but no generic command executor, and that the evidence is
  an attestation bound to a commit and a tree, not an unforgeable proof.
- [ ] The decision records whether pushing the task branch is covered by the
  standing authorization of Decision 1, which `T1_CI` needs. If it is covered, it
  adds the exact sentence for the rule text; if not, it states that `T1_CI` is
  then unavailable until the developer pushes.
- [ ] A new decision defines the lifecycle paths allowed after validation: derived
  from the task identity, the archive accepted only as an exact 100% rename,
  idempotent for an already archived task, every other deletion or addition
  blocked, and `stage` read-only until the lease. It states that this is a bridge
  until Tasks 103 and 104 remove queue, plan, and archive edits from task
  branches.
- [ ] The decision on the Task 101 closure sequence records the one-time
  bootstrap: a task that archives its own record cannot use the unfixed `stage`,
  so Task 111 and Task 101 close with the archive applied in a record-only commit
  on `main` after integration, or by an alternative the developer records.
- [ ] The follow-up table lists Tasks 111 to 114 with their dependencies and
  states the execution order: 111, then 101, then 102, 112, 113, 114, 103, 104,
  108, 105, 106, 107, 109, 110, with the reason for each constraint.
- [ ] The queue rows of Tasks 108, 109, and 110 gain the dependency on Task 113,
  and Task 102 gains the dependency on Task 111, in `tasks/QUEUE.md`, with no
  other row changed.
- [ ] Rejected alternatives are added: a generic `meridian validation run`
  executor, allowing any post-validation change under `tasks/`, a whitelist taken
  from the evidence file, and treating a timeout as a pass or as a skip.
- [ ] Claims about host behavior (the command limit, whether a detached process
  survives it) stay labelled reported or unverified.
- [ ] `python3 scripts/check_repository.py` passes. The task is documentation-only
  and the unit tests may be skipped, with the skip recorded in the handoff.

## Relevant Files

| File | Role |
|------|------|
| `docs/TASK_CLOSURE_DESIGN.md` | Survey, new decisions, follow-up table, rejected alternatives. |
| `tasks/QUEUE.md` | Dependency changes for Tasks 102, 108, 109, and 110 only. |
| `tasks/111-stage-accepts-exact-task-archive-rename.md` to `tasks/114-ci-on-task-branches-and-evidence-lookup.md` | Source of the decisions. |

## Technical Context

- **Run this after Task 101 is integrated.** It edits `tasks/QUEUE.md`, which
  Task 101's closure also edits, and doing both at once is the governance-file
  conflict that Task 100 describes.
- Decision 6 of the design covers a named sandbox skip (Task 099). It does not
  cover a command that is cut off by the host with no exit status.
- The stage whitelist cause is observed in the Task 101 report and in
  `scripts/meridian.py` (`stage_task_integration`); it was not reproduced when
  this task was written.

## Validation

- `python3 scripts/check_repository.py`
- Documentation-only: build and unit-test commands are skipped and the skip is
  recorded in the handoff.
- Evidence tier: the dependency edits are structural and checked against the
  queue; the rest is reviewed text.

## Out of scope

Implementing any follow-up, changing workflow templates or migrations, and
revisiting the decisions of Task 100 that this addendum does not touch.

## Dependencies

- **Depends on**: 100, 101
- **Blocks**: none
