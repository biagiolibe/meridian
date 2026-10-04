# Task 133 — Let a confirmed Resume reach a dirty task worktree

> **ID**: `133`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2.5h
> **Assigned to**: Claude Code (Proceed with 133)
> **Session**: Interrupted task 129 observed on 2026-10-03

## Objective

The console Resume added by task 126 launches `Proceed with <ID>`, and for a
dirty worktree it asks for a second confirmation. But `Proceed with` starts with
`meridian worktree prepare`, and `prepare` refuses any existing dirty task
worktree (`existing task worktree is dirty and was retained`, in
`prepare_task_worktree`). So a task interrupted after it wrote files cannot be
resumed from the console: the developer confirms twice, the agent starts, and it
stops at once with `BLOCKED`. This happened for task 129, whose work (264 lines
of uncommitted changes) had to be committed by hand before `prepare` would
proceed. Resume only works for a clean worktree.

Give `prepare` an explicit, opt-in way to accept a dirty worktree of the same
task, and make the console Resume use it only after the developer has confirmed
that no agent is still active.

## Acceptance Criteria

- [x] `meridian worktree prepare <TASK-ID> --resume` accepts an existing
  canonical worktree of that task that has uncommitted changes. It leaves every
  file and the index untouched, preserves `started_at` and `base_commit`, and
  returns JSON that includes `resumed: true` and `dirty: true`.
- [x] Without `--resume`, behavior is unchanged: a dirty existing worktree is
  still refused with the same message. `--resume` on a task with no existing
  worktree is refused (nothing is created by a resume), and `--resume` never
  creates, moves, removes, or resets anything.
- [x] `--resume` still blocks on every other mismatch that blocks `prepare` today:
  a worktree on a different branch or commit, partial state (branch without
  worktree or the reverse), a path collision, and a lifecycle state that
  disagrees with the branch or worktree. It also blocks while an integration
  lease or staged merge is active for the task.
- [x] The returned JSON gives the agent what it needs to continue safely: the
  branch, the absolute worktree path, `handoff_worktree`, and a short summary of
  the dirty state (count of changed and untracked paths), without file contents.
- [x] The console Resume for a task whose worktree is dirty launches a directive
  that tells the agent to run `prepare --resume`, and for a clean worktree keeps
  using the ordinary directive. The directive text shown by `[copy]` is the same
  string the launch uses.
- [x] The Resume is offered only after the existing liveness confirmation and, for
  a dirty worktree, the existing second confirmation. The console never passes
  `--resume` on its own for a plain launch of a `todo` task, a `Review`, or an
  `Address review`.
- [x] The Lean Delivery and Governed SDD workflow guidance states, in additive
  wording, that a Resume directive starts with `prepare --resume`, that
  `--resume` is allowed only for that directive, and that the agent must read
  `git status` and the diff before continuing. Because this changes managed
  template text, the task follows the capability-marker and migration rules; the
  release that carries it is a template-changing release.
- [x] Fallback if the template change cannot be completed within this task: the
  console does not offer a launch for a dirty worktree and instead shows an
  instruction to open a session inside the worktree and inspect its diff, and the
  decision is recorded in the handoff. Do not ship a dirty-worktree launch that
  `prepare` will refuse.
- [x] Tests cover: `--resume` on a dirty worktree succeeds and changes nothing;
  the dirty message without `--resume`; `--resume` with no worktree refused;
  every mismatch and lease case still blocked; `started_at` preserved; the JSON
  shape; and, end to end, that the directive the console produces for a dirty task
  is one `prepare --resume` accepts.
- [x] A rehearsal on a scratch repository is recorded in the handoff: prepare a
  worktree, edit a file without committing, confirm plain `prepare` refuses,
  confirm `prepare --resume` accepts and the edit is intact.
- [x] `python3 scripts/check_repository.py` and the unit tests pass, and one
  changelog fragment is added per `CONTRIBUTING.md`.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `prepare_task_worktree`, the `worktree prepare` parser, and the dirty check. |
| `scripts/project_console.py` | Resume directive, confirmations, and launch revalidation (task 126). |
| `templates/workflows/*/PROJECT_WORKFLOW.md` and workflow documents | Additive wording for the Resume directive. |
| `docs/WORKTREE_LIFECYCLE.md` | `prepare` contract. |
| `tests/test_task_worktree_isolation.py` | Worktree lifecycle tests. |
| `tests/test_project_console.py` | Resume prompts and directive tests. |

## Technical Context

- The dirty refusal protects against two writers and against losing unsaved work.
  It stays the default; `--resume` is a recorded, explicit choice made by the
  developer through the console's liveness confirmation.
- Task 126 added the Resume action and the two confirmations
  (`project_console.py`, `resume_confirmations`), and its tests cover the
  prompts but not what `prepare` does with the resulting directive.
- Observed: for task 129 the worktree held 8 modified files and one new file with
  no commits on the branch. `prepare` refused it; committing the work in the
  worktree by hand allowed the task to continue.
- The Codex command policy already allows `meridian worktree prepare`; check that
  the `--resume` form is matched by the same rule, and extend the shipped rules
  only if it is not.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`
- The recorded scratch-repository rehearsal.

## Out of scope

Detecting whether an agent is alive, an automatic commit or stash of dirty work,
removing or resetting a worktree, and changing the dirty refusal for any command
other than `prepare --resume`.

## Dependencies

- **Depends on**: —
- **Blocks**: none
