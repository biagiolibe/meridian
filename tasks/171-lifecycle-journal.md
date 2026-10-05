# Task 171 — Record lifecycle command results in a local journal

> **ID**: `171`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Rigidity measurement follow-up to ADR stops and denials, 2026-10-05

## Objective

Meridian cannot measure its own friction. Nothing records how often a
lifecycle command stops, with which code, or how long a task takes from
preparation to integration. `docs/ADR_STOPS_AND_DENIALS.md` lists a lifecycle
journal as a follow-up. Without that measurement, whether a change reduces
rigidity stays an opinion.

Add an append-only local journal that every lifecycle command writes to.

## Acceptance Criteria

- [ ] `prepare`, `check`, `closure-status`, `evidence`, `integrate stage`,
  `integrate finalize`, `integrate abort`, and `cleanup` each append one JSON
  line to `<git-common-dir>/meridian-journal.jsonl`.
- [ ] Each line has `version` (1), `ts` (ISO-8601 UTC), `command`, `task`
  (canonical ID), `step` when known, `result` (`ok`, `blocked`, or `error`),
  `stop_code` when blocked, and `exit`. It contains no absolute path, no
  command-line text supplied by the agent, and no message content.
- [ ] The journal is untracked and shared by all worktrees of the repository.
  The file is rotated to `meridian-journal.1.jsonl` when it exceeds 5 MB, and
  only one previous file is kept.
- [ ] A journal write that fails never changes a command's result or exit
  status. It prints one warning to standard error.
- [ ] Concurrent appends from two worktrees produce whole lines; a test proves
  it.
- [ ] `docs/WORKTREE_LIFECYCLE.md` documents the journal, its fields, and its
  privacy boundary.
- [ ] Tests cover one line per command, a blocked result with its registered
  code, rotation, a write failure, and the absence of absolute paths.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Lifecycle commands, `canonical_git_common_dir`, the stop helper from task 162. |
| `docs/WORKTREE_LIFECYCLE.md` | Journal documentation. |
| `tests/test_meridian_cli.py` | Journal tests. |

## Technical Context

- Lifecycle state already lives under the Git common directory
  (`meridian-worktrees/`, `meridian-integration.lock`,
  `meridian-integration.json`); the journal follows that naming.
- Stop codes come from `capabilities/stop-codes-v1.json` through the helper
  added by task 162. Record the code, not the message.
- `meridian usage` already reports token counters without reading message
  content; keep the same privacy rule.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Reporting (task 172), host hooks (task 173), and sending the journal anywhere.

## Dependencies

- **Depends on**: —
- **Blocks**: 172, 173, 174
