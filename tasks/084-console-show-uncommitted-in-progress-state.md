# Task 084 — Show uncommitted in-progress task state in the console

> **ID**: `084`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Estimate**: ~2–4h
> **Assigned to**: unassigned
> **Session**: 2026-10-01 developer report: console stays on TODO while a task is being worked

## 🎯 Objective

Make the project console reflect that a task is in progress as soon as its
worker has changed the task's queue row, not only after the worker commits it.

The developer reported that the console state does not update when a task goes
to in progress, observed while Task 082 was being worked. Reading the code
shows a likely cause, not a reproduced one: effective state is read from the
committed queue on the task branch, while the first reservation edit lives only
in the task worktree until it is committed. Until then the console shows `TODO`
with at most an "active writer" marker.

## 📋 Acceptance Criteria

- [ ] The report is reproduced first and the result is recorded in the handoff:
      prepare a task worktree, change the task's queue row to `[/]` without
      committing, and capture what the console shows before the fix. If the
      defect is not reproduced, record exactly what was tried and stop with the
      task still `[/]` and the blocker stated.
- [ ] In a Lean Delivery project, a task whose registered worktree is dirty and
      whose working-tree queue row is `[/]` is shown as in progress even though
      the branch commit still says `[ ]`. The row's source indicates that the
      state is uncommitted.
- [ ] The same behavior holds for Governed SDD (`QUEUED` to `IN_PROGRESS`) using
      that profile's tokens and phases.
- [ ] A clean worktree whose branch equals `main` (prepared, nothing written) is
      not shown as in progress. It stays `TODO`, with a distinct, non-error
      indication that a worktree is registered.
- [ ] A working-tree row that is behind the committed branch row, or a
      working-tree queue file that cannot be parsed, never advances or
      regresses the state silently: it falls back to the committed state and
      reports a mismatch where the existing rules already report one.
- [ ] The console remains strictly read-only: it reads the working-tree queue
      file only, never writes, stages, or runs project commands in a worktree.
      Reads stay bounded and do not reintroduce the refresh latency fixed in
      Task 078.
- [ ] Tests cover: uncommitted `[/]` in both workflow profiles, clean prepared
      worktree, committed state ahead of the working tree, unparsable working
      tree queue, a missing worktree directory for a registered branch, and
      refresh timing for a project with several worktrees.
- [ ] `python3 -m unittest discover -s tests`,
      `python3 scripts/check_repository.py`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/console_workflow.py` | `effective_state`, `BranchFacts`, profile phases. |
| `scripts/project_console.py` | `_branch_facts`, `load_snapshot`, row flags and detail rendering. |
| `tests/` | Console and workflow-profile coverage. |

## 🧩 Technical Context

- **Current behavior**: `_branch_facts` reads the queue with
  `git show refs/heads/<branch>:<queue>` and takes `dirty` from
  `git status --porcelain` in the worktree. When the branch row equals the
  primary row, `effective_state` reports the primary status and only sets
  `active_writer`. The console therefore cannot show an uncommitted `[/]`.
- **Observed at report time**: the Task 082 worktree was clean and level with
  `main`, so the console was accurate at that instant. The defect is therefore
  unconfirmed and the first acceptance criterion requires reproduction.
- **Desired behavior**: the effective state also considers the working-tree
  queue row when the worktree is dirty, using the same phase-ordering rules
  that already compare the branch row with the primary row, and labels the
  source as uncommitted.
- **Design options considered**: reading the working-tree row (preferred, one
  bounded file read); using the lifecycle state written by
  `meridian worktree prepare` under the Git common directory as a separate
  "prepared" signal (optional, only for the clean-worktree indication); and a
  UI-only emphasis of the existing active-writer marker (rejected, it does not
  change the displayed state).

## 🔨 Suggested Implementation

1. Write the reproduction as a test fixture using a temporary repository and a
   linked worktree.
2. Extend the branch facts with the working-tree queue row, read only when the
   worktree is dirty.
3. Extend `effective_state` with the uncommitted source and the fallback rules.
4. Render the uncommitted source in the list and detail views.
5. Add the listed tests and a timing check for several worktrees.

## ⚠️ Constraints and Considerations

- Do not write to, stage in, or execute commands inside any worktree.
- Preserve the existing mismatch semantics and the Governed SDD
  `READY_FOR_REVIEW` consistency checks.
- Keep refresh cost bounded; do not read every worktree file on each refresh
  when the worktree is clean.
- Repository artifacts are English-only.

## 🔗 Dependencies

- **Depends on**: 076, 078, 079, 082.
- **Blocks**: none. Task 077 launches agents from the console; the developer may
  prefer to order this task before it, which this record does not decide.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/084-console-show-uncommitted-in-progress-state.md)"$'\n\nExecute this task in the current project.'
```
