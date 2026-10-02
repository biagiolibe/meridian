# Task 111 — Let `integrate stage` accept the exact archive rename of the task record

> **ID**: `111`
> **Status**: `DONE`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 101 closure blocked at `integrate stage`

## Objective

`meridian worktree integrate stage` blocks a task whose closure commit archives
its own record, although the workflow requires that archive. Task 101 ended with
`BLOCKED: the task-relevant tree changed or cannot be proven unchanged after
validation`, and the diff between the validated commit and the closure commit
contained only lifecycle records:

```text
M  PROJECT_PLAN.md
M  tasks/QUEUE.md
R100 tasks/101-closure-status-command.md tasks/done/101-closure-status-command.md
A  tasks/handoffs/101.md
```

Make `stage` recognize that archive as an allowed lifecycle change, derived from
the task's identity and nothing else, without widening what else may change
after validation. Nothing was left active by the failed run: no lease, no merge,
no change to `main`.

## Acceptance Criteria

- [ ] A failing regression test is written first from the real sequence above:
  a validated task commit followed by a closure commit that modifies the queue
  and plan, adds the handoff, and renames the task record into `tasks/done/`.
  It fails on the current code for the stated reason before the fix.
- [ ] The allowed lifecycle paths are derived from the resolved task identity,
  not from the evidence file: the active record path, the archive path
  `tasks/done/<same file name>`, the queue, the handoff, the review record,
  `PROJECT_PLAN.md`, and `tasks/QUEUE_ARCHIVE.md`. The evidence fields
  `task_paths`, `task_dependencies`, and `task_behavioral_surfaces` keep their
  current role in the interaction analysis only.
- [ ] The comparison uses rename-aware Git output (`git diff --name-status -z
  --find-renames=100%` between the validated commit and the current task commit)
  instead of a plain list of names.
- [ ] The archive is accepted only as one exact rename: status `R` with
  similarity 100%, old path equal to the active record path, new path equal to
  the archive path of the same task. Every other combination is blocked: a
  deletion of the active record without that rename, an addition under `tasks/`
  or `tasks/done/` without the matching deletion, a rename whose content changed
  (similarity below 100%), a rename to any other destination, and any path that
  belongs to a different task.
- [ ] A task already archived at the validated commit (the record is at the
  archive path in both commits) is accepted with no rename required, and a
  task that is not archived accepts only changes to the active record path.
- [ ] A blocked result names the offending path or paths, for example `BLOCKED:
  paths changed after validation: <paths>`, instead of only the generic message.
- [ ] Validation evidence is not modified or reinterpreted: a task validated
  before the fix keeps its recorded commits and results, and the fix needs no
  new evidence field.
- [ ] `stage` remains read-only until it acquires the lease: when the result is
  blocked, a test shows that no lease, integration, or lifecycle state file
  exists, no reference changed, no merge was started, and the primary checkout
  is unchanged.
- [ ] Existing stage tests keep passing, including the `REUSE`, `BOUNDED`, and
  `FULL` decisions.
- [ ] `docs/WORKTREE_LIFECYCLE.md` states which paths may change after
  validation and that the archive is accepted only as the exact rename.
- [ ] `CHANGELOG.md` records the fix under `[Unreleased]` as a CLI-only fix.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass; where the
  full suite cannot finish in the agent host, the handoff records the validation
  state per the rules in force at that time.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `stage_task_integration` (the `allowed` set built after `validated_is_ancestor`) and `decide_integration_validation`. |
| `tests/test_meridian_cli.py` | `WorktreeLifecycleCliTest` and the stage tests to extend. |
| `docs/WORKTREE_LIFECYCLE.md` | Evidence boundary section. |
| `CHANGELOG.md` | `[Unreleased]` entry. |

## Technical Context

- **Current code**: after confirming that the validated commit is an ancestor of
  the task commit, `stage` runs `git diff --name-only` between them and accepts
  the result only if it is a subset of five paths: the task path, queue, handoff,
  review record, and `PROJECT_PLAN.md`. The task path comes from one resolved
  identity, so an archive that moves the record leaves one of the two paths
  outside the set. `tasks/QUEUE_ARCHIVE.md` is not in the set either. I have not
  reproduced the failure; the first test must.
- **Why this is a bridge**: Tasks 103 and 104 move queue, plan, and archive
  updates into `stage`, so task branches stop carrying them and this rename
  disappears from the diff. Keep the fix small enough to remove then.
- **Ordering**: this task and Task 102 change the same function. Integrate this
  one first.
- **Bootstrap**: a task that archives its own record cannot use the unfixed
  `stage`, and this task is no exception. Close it with the archive rename left
  out of the task branch and applied in a separate record-only commit on `main`
  after integration, or by the alternative the developer chooses and records.
  This is a recorded, one-time deviation, not a bypass of the check.
- Lean Delivery applies: a CLI fix with no new public surface.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest -v tests.test_meridian_cli.WorktreeLifecycleCliTest`
- Evidence tier: path decisions, blocked messages, and the absence of lifecycle
  state are program-computed and asserted; no manual evidence is required.

## Out of scope

Changing the shape of the validation evidence, applying queue, plan, or archive
updates inside `stage` (Tasks 103 and 104), the main-advance facts (Task 102),
and Task 101's own content.

## Dependencies

- **Depends on**: 055, 063
- **Blocks**: integration of Task 101; Task 102 must integrate after this task
