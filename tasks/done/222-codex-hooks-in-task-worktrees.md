# Task 222 — Run Meridian's Codex hooks in task worktrees

> **ID**: `222`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h (probe first; split if the fix is larger)
> **Assigned to**: unassigned
> **Session**: Codex hook review, 2026-10-15
> **Origin**: friction

## Objective

Meridian's Codex hooks (`meridian hook read-guard --host codex` on
`PreToolUse`, `meridian hook stop-audit --host codex` on `Stop`) live in the
project-level `.codex/hooks.json`. Codex records hook trust per absolute
`hooks.json` path in `~/.codex/config.toml` under `[hooks.state]`. Only the
primary checkouts carry entries there. Every Lean Delivery task session runs in
a fresh worktree under the worktree root, so its `hooks.json` path is new and
never trusted. The read guard and the stop audit therefore appear not to run
during task work, which is where they matter.

A second defect shows at the end of a successful task session. `meridian
worktree cleanup` removes the task worktree, which is the session's working
directory. Codex then starts the `Stop` hook in the removed directory and
reports `Hook failed` with `No such file or directory (os error 2)`. Sessions
for tasks 211, 212, and 221 ended this way on 2026-10-15.

Make the hooks run in task worktree sessions without a per-task trust step,
and stop the end-of-session failure.

## Acceptance Criteria

- [x] Before any change, the handoff records a probe with the Codex version:
  in a session started inside a task worktree, does Codex run the worktree's
  `.codex/hooks.json` hooks, prompt for trust, or skip them? Also record
  whether a user-level `~/.codex/hooks.json` hook runs there after one trust
  step.
- [x] Based on the probe, task worktree sessions run the read guard and the
  stop audit without a trust step per task. The chosen mechanism and its
  reason are recorded in the handoff. If it is a user-level hooks block,
  `meridian setup --check` plans it and `--apply` writes it between Meridian
  markers. Foreign hooks are preserved, and a damaged marker pair stops with
  a registered stop code. `meridian codex doctor` reports it as `ready`,
  `missing`, or `stale`.
- [x] A user-level hook is a no-op with exit code 0 in a directory that is not
  a Meridian project, and in a working directory that no longer exists.
- [x] A successful `Proceed with` session no longer ends with `Hook failed`
  after `meridian worktree cleanup`. Either the hook tolerates a removed
  working directory, or the cleanup leaves the session directory to a later
  step. The handoff records which, with evidence.
- [x] Tests cover the chosen mechanism, the non-Meridian no-op, and the
  removed-directory case.
- [x] README's Codex section documents the hook installation and trust step.
  One changelog fragment states the change under `Fixed`.
- [x] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `.codex/hooks.json` | Current project-level hook definitions. |
| `scripts/meridian.py` | `hook` subcommands, setup, Codex doctor, `worktree cleanup`. |
| `scripts/codex_read_guard.py`, `scripts/stop_audit.py` | Hook implementations. |
| `README.md` | Codex setup documentation. |
| `tests/` | Hook, setup, and doctor tests. |

## Technical Context

- Evidence of 2026-10-15: `~/.codex/config.toml` `[hooks.state]` lists
  `hooks.json` entries for the primary checkouts only, none for paths under
  `~/.meridian/worktrees/`. The released `meridian hook stop-audit --host
  codex` exits 0, and `meridian` resolves on the Codex `PATH`, so the command
  itself is not the cause.
- A manual probe in a scratch directory outside any Meridian project showed
  both hook commands exiting 0 with no output and no files written. The tests
  must establish this; the probe is not evidence of acceptance.
- Task 221 added a managed block to the user's `~/.codex/rules/default.rules`
  through setup. A user-level hooks block can follow the same plan, apply,
  marker, and doctor pattern.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Editing `[hooks.state]` or any trust entry in `~/.codex/config.toml`
programmatically. Claude Code hooks. Changing what the read guard or stop
audit checks.

## Dependencies

- **Depends on**: 221 (setup pattern for user-level Codex files)
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/222-codex-hooks-in-task-worktrees.md)"$'\n\nExecute this task in the current project.'
```

## Completion Evidence

See `tasks/handoffs/222.md` for the pre-change Codex 0.161.0 probe and full
validation. Linked worktrees use the primary checkout's trusted hook source;
no user-level hook block is needed. Cleanup retains an empty session directory,
and hook CLI startup tolerates an inherited deleted working directory.
