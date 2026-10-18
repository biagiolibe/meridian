# Task 235 — Scan only repository files in `check_repository.py`

> **ID**: `235`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Task 232 candidate validation stop, 2026-10-18
> **Origin**: friction

## Objective

Make `python3 scripts/check_repository.py` check only the files of this
repository, so that a host checkout nested in the primary checkout cannot fail
candidate validation.

`check_local_markdown_links`, `check_json`, and `check_bash` walk the
filesystem with `ROOT.rglob(...)`. Claude Code creates its session worktrees
under `.claude/worktrees/` in the primary checkout. Git ignores that directory
through `.git/info/exclude`, but `rglob` does not. Each nested worktree is a
full copy of the repository, and the exemption for `tasks/QUEUE_TEMPLATE.md`
matches only that exact path relative to the root. On 2026-10-18 the candidate
validation of task 232 therefore failed with `BLOCKED
CANDIDATE_VALIDATION_FAILED` on `broken local Markdown link in
.claude/worktrees/meridian-worktree-cleanup-0cc5b9/tasks/QUEUE_TEMPLATE.md:
001-init-ecs.md`, although the candidate tree itself was correct. Any open
Claude Code session in a worktree blocks every integration in the same way.

## Acceptance Criteria

- [x] `check_local_markdown_links`, `check_json`, and `check_bash` select their
  files from one shared helper that lists repository files with `git ls-files
  -z --cached --others --exclude-standard` and keeps only paths that exist as
  files. Tracked, staged, and untracked-but-not-ignored files are still
  checked, so a new file in a task worktree or a staged candidate merge is
  covered.
- [x] A file under a path ignored by `.gitignore` or `.git/info/exclude`, and
  any nested checkout such as `.claude/worktrees/<name>/`, is never checked.
- [x] The helper fails closed: when `git ls-files` exits non-zero, the check
  reports a failure instead of passing with an empty file list.
- [x] Tests in `tests/test_check_repository.py` cover: a broken link in a file
  under an excluded nested directory is ignored; the same broken link in a
  tracked file and in an untracked, non-ignored file still fails; invalid JSON
  and invalid Bash under an excluded directory are ignored.
- [x] The existing exemptions (`templates/`, `tasks/QUEUE_TEMPLATE.md`, and the
  archived-queue-row rule) keep their behavior.
- [x] No file under `templates/` or `migrations/` changes, and no managed file
  of this repository changes.
- [x] Every command under Validation passes.

## Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | `check_local_markdown_links`, `check_json`, `check_bash`; `check_no_machine_paths` already lists files with `git ls-files`. |
| `tests/test_check_repository.py` | Repository-check tests. |

## Technical Context

- The scoped `rglob` calls over `templates/` and the workflow template
  directories stay as they are: they read fixed directories inside the
  repository.
- `git ls-files --others` does not descend into nested Git checkouts, and
  `.claude/worktrees/` is also excluded locally, so the same helper covers
  both cases.
- Cardine has the same defect and fixes it in its own task.

## Out of scope

Any change to the lifecycle CLI, candidate validation commands, or release
records. No changelog fragment: the change is repository tooling only.

## Dependencies

- **Depends on**: none
- **Blocks**: 234

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Completion

Implemented in `fbe8954`. All validation commands passed; the full parallel
suite ran 1116 tests with no failures, errors, or skips. The fixed scans also
passed against the primary checkout while its active Claude Code worktree
remained present. See `handoffs/235.md` for evidence and the additional
candidate acceptance check.
