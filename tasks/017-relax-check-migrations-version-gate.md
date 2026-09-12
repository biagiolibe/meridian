# Task 017 — Relax `check_migrations()`'s VERSION equality to `<=`

> **ID**: `017`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~30min
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

`scripts/check_repository.py`'s `check_migrations()` currently asserts the
last migration's `to` equals the repository's `VERSION` exactly. Under the
new split (task 015), a CLI-only release bumps `VERSION` without adding a
migration, so the last migration's `to` legitimately lags behind `VERSION`.
Relax the check accordingly, without weakening migration-sequence
contiguity.

## 📋 Acceptance Criteria

- [ ] `check_migrations()` accepts `version_key(previous_to) <=
      version_key(VERSION)` instead of requiring equality.
- [ ] `check_migrations()` still fails when a migration's `from` does not
      equal the previous migration's `to` (contiguity untouched).
- [ ] `check_migrations()` still fails if the last migration's `to` is
      *greater* than `VERSION` (a migration must never be ahead of the
      release it ships in).
- [ ] A new passing fixture/test case: repository `VERSION` ahead of the
      last migration's `to` (the CLI-only scenario).
- [ ] `python3 scripts/check_repository.py` passes on the real repository
      state at the time this task lands (i.e. do not merge this without
      `VERSION` and `migrations/` staying mutually consistent under the new
      rule).

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | `check_migrations()`. |
| `tests/test_check_repository.py` | Add the new passing/failing fixtures. |

## 🧩 Technical Context

- **Current behavior**: `if previous_to != current_version: fail(...)`.
- **Desired behavior**: `if version_key(previous_to) > version_key(current_version): fail(...)`
  (migration ahead of release — still a hard failure), while
  `previous_to < current_version` is now valid (CLI-only releases in
  between).

## 🔨 Suggested Implementation

1. Reuse `meridian.version_key()` for the comparison instead of a string
   equality check.
2. Update the failure message to describe the new invariant ("a migration
   must never target a version ahead of the current release").
3. Add test fixtures in `tests/test_check_repository.py`: (a) last
   migration `to` strictly less than `VERSION` → pass; (b) last migration
   `to` strictly greater than `VERSION` → fail; (c) non-contiguous `from`/`to`
   chain → fail (regression, unchanged behavior).

## ⚠️ Constraints and Considerations

- This gate protects the whole repository's migration sequence; treat it as
  a risk-bearing change worth its own review even though it is small.
- Depends on task 015: relaxing this check only makes sense once the CLI
  itself actually supports a CLI-only release end to end.

## 🔗 Dependencies

- **Depends on**: 015
- **Blocks**: 019, 020, 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/017-relax-check-migrations-version-gate.md)"$'\n\nExecute this task in the current project.'
```
