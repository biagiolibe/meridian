# Task 019 — `releases/<version>.json` immutable release ledger + `check_releases()`

> **ID**: `019`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: 2026-09-12/13 ADR design session

## 🎯 Objective

Add a new append-only `releases/<version>.json` record per framework
release, starting at the first release cut after this task lands (no
historical backfill). It is the only mechanically checkable trace that a
given release did or did not move `workflowBaselineVersion` — the fact a
CLI-only release otherwise leaves nowhere but changelog prose. Add
`check_releases()` to `scripts/check_repository.py` to validate it.

## 📋 Acceptance Criteria

- [ ] `releases/<version>.json` schema implemented with exactly these
      fields: `version`, `releaseDate`, `gitTag`, `protocolVersion`,
      `workflowBaselineVersion`, `baselineChanged`, `migrations` (no
      `summary` field — it would duplicate `CHANGELOG.md` and rot
      independently).
- [ ] `check_releases()` in `scripts/check_repository.py` validates:
      - a record exists for the current `VERSION`;
      - each record's `version` field matches its filename;
      - release versions are monotonically increasing across files;
      - no release record carries a prerelease/build suffix;
      - the latest record's `workflowBaselineVersion` equals the value
        derived from `migrations/*.json` (the `latest_migration_to` helper
        from task 015);
      - `baselineChanged` is `true` iff `migrations` is non-empty, and each
        listed migration's `to` equals the record's `workflowBaselineVersion`.
- [ ] `check_releases()` is called from `main()` in `check_repository.py`
      alongside the existing checks.
- [ ] Test fixtures in `tests/test_check_repository.py`: missing record for
      current `VERSION`, filename/version mismatch, non-monotonic version,
      `baselineChanged` inconsistent with `migrations`, prerelease/build
      suffix present (one failing case each), plus a passing baseline
      fixture.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | Add `check_releases()`, wire into `main()`. |
| `releases/` | New directory, created by this task (first record deferred to task 021's release cut, or a placeholder record for the version at the time this task lands — decide during implementation and note the choice in the PR). |
| `tests/test_check_repository.py` | Add the new fixtures. |

## 🧩 Technical Context

- **Current behavior**: no machine-checked release ledger exists;
  `CHANGELOG.md` is the only record of what shipped in each version, and it
  is prose, not structured data.
- **Desired behavior**: `releases/<version>.json` is the machine-checked
  ledger, `CHANGELOG.md` remains the prose record — the same division of
  labor the repository already uses between `migrations/*.json` and
  `CHANGELOG.md` (see `CHANGELOG.md`'s own header note).

## 🔨 Suggested Implementation

1. Define the JSON schema (see fields above) and document it briefly in
   `migrations/README.md` or a new `releases/README.md`.
2. Implement `check_releases()` using `meridian.latest_migration_to()` /
   `meridian.version_key()` for comparisons.
3. Decide whether this task itself writes the first `releases/<VERSION>.json`
   record (for the current, already-released `VERSION`) or leaves the
   directory empty until task 021's actual release cut — recommended: write
   one record for the current `VERSION` now, so `check_releases()` has
   something to validate against immediately and CI does not go red the
   moment this task merges.
4. Add the fixtures listed in Acceptance Criteria.

## ⚠️ Constraints and Considerations

- No historical backfill for versions before this task — would be
  speculative reconstruction of intent the repository never recorded as a
  discrete fact.
- Records are append-only; a correction ships as a new release, never an
  edit to a past record (same rule as `migrations/*.json`).

## 🔗 Dependencies

- **Depends on**: 017
- **Blocks**: 020, 021

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/019-releases-ledger.md)"$'\n\nExecute this task in the current project.'
```
