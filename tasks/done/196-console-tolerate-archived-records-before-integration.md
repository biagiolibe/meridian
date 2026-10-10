# Task 196 — Tolerate archived task records in the console before integration

> **ID**: `196`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Task 194 validation failure after archival, 2026-10-10
> **Origin**: friction

## Objective

Closing a task archives its record into `tasks/done/` on the task branch. The
queue link keeps pointing at the original path until `meridian worktree
integrate stage` updates `tasks/QUEUE.md` on the merged tree. This is the
prescribed intermediate state, because a task branch never edits the queue.

In that state, `_task_path` in `scripts/project_console.py` follows the queue
link, does not find the file, and raises `Task <id> file is unavailable within
the project`. `tests/test_project_console.py::ProjectConsoleTest::test_one_shot_against_repository`
runs the console against the live repository (`--project ROOT --once`), so it
fails on any task branch after archival.

Make the console resolve an archived record in that state, and make the suite
independent of the live repository's governance state.

## Acceptance Criteria

- [x] When a queue row has a link whose target lies in a task root but does not exist,
  `_task_path` searches the task roots for a record with the same file name as the link
  target, using the scan and exclusions of `RecordResolver`. It uses the result only when
  there is exactly one match whose heading names the same task. With zero or several
  matches, the existing error stays.
- [x] A link that leaves the project, or a link that is not unambiguous,
  remains an error as today.
- [x] A fixture whose record was moved to `tasks/done/`, with a queue row that
  still links the original path, produces a valid snapshot that resolves the
  archived record.
- [x] Without any matching record, the snapshot still fails with an explicit
  error. The same holds for a link outside the project and for two matches.
- [x] `test_one_shot_against_repository` no longer depends on the live
  repository's governance state. It still proves that the one-shot command
  works, but on a controlled copy or fixture, or a dedicated test covers the
  intermediate state. Its existing assertions are not weakened.
- [x] The suite passes both before and after a record is archived.
- [x] The `done` count and the behavior introduced by task 195 do not change.
- [x] `python3 scripts/check_repository.py`, the parallel unit suite, and `git
  diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/project_console.py` | `_task_path` (around line 404) and `RecordResolver.find_by_name`. |
| `tests/test_project_console.py` | `test_one_shot_against_repository` and the new fixture tests. |

## Technical Context

- Evidence: after the archival rename in `05fad02`, task 194 stopped with
  `BLOCKED VALIDATION_FAILED`, exit 1, and empty stderr. Tasks 192 and 193 did
  not hit it only because they validated before archiving.
- `RecordResolver.find` matches only exact `<ID>.md` names. Linked-record
  fallback uses `find_by_name` with the existing cached scan and exclusions;
  ID-based and branch-ref resolution remain unchanged.
- Task 195 changes the same file, so this task is serialized after it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Changing who updates the queue or when, changing `integrate stage`, renaming
or moving existing records, and any other console change.

## Dependencies

- **Depends on**: 195
- **Blocks**: none
