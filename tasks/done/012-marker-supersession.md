# Task 012 — `append_only_new_markers` treats a version bump as a new capability

> **ID**: `012`
> **Category**: Bugfix (CLI)
> **Priority**: 🔴 P1
> **Estimate**: ~4h
> **Assigned to**: unassigned

## 🎯 Objective

A capability whose version is bumped is appended to a customized project file
while the previous version stays where it was. The two versions then coexist and
can contradict each other, with the stale one in the position an agent actually
reads.

## 📋 Acceptance Criteria

- [x] `append_only_new_markers` distinguishes an **added** capability from a
      **superseded** one, by capability name rather than by `(name, version)`.
- [x] When the local block for the older version matches the base byte-for-byte
      (the project never edited it), the new version **replaces it in place**,
      preserving all surrounding project-owned text.
- [x] When the local block was modified, the function returns `None` so the file
      falls through to `conflict` and the operator reconciles it. It must never
      silently discard a project's edit to a protected block. (This also covers
      an *unchanged*-version capability: the rewrite initially dropped the
      original inherited-block integrity check for the `old_version ==
      new_version` case — caught by advisor review before commit, restored, and
      covered by a dedicated regression test.)
- [x] `meridian audit` reports `FAIL` when two versions of the same capability
      are present in one managed file, so already-damaged projects are detected
      rather than left to accumulate.
- [x] Tests cover: added capability (appends, unchanged behaviour); bumped
      capability with an unmodified local block (replaces in place); bumped
      capability with a modified local block (returns `None`); an edited
      *unchanged*-version block blocking an otherwise-safe append; a local file
      already carrying two versions of one capability; and the new audit check
      on a file carrying both versions.
- [x] `python3 scripts/check_repository.py` and the CLI suite pass (54 tests).

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py:322` | `append_only_new_markers` — the defect. |
| `scripts/meridian.py:892` | Call site that selects the `append-markers` action. |
| `scripts/meridian.py:355` | `audit_capability_markers` — where the new check goes. |
| `tests/test_meridian_cli.py` | Coverage. |
| `migrations/CAPABILITY_MARKERS.md` | Document supersession alongside insertion. |

## 🧩 Technical Context

The guard is keyed on pairs:

```python
missing = [pair for pair in template_pairs if pair not in local_pairs]
if not missing or any(pair in base_pairs for pair in missing):
    return None
```

With local at `(mvp, 1)`, base at `(mvp, 1)` and template at `(mvp, 2)`, the pair
`(mvp, 2)` is absent from both `local_pairs` and `base_pairs`, so it reads as a
brand-new capability and is appended. The docstring already states the correct
intent — "the target **adds** one or more marker blocks… and no existing marker
is changed" — but pair comparison cannot express it.

This path is the fallback taken when the three-way merge conflicts, so it fires
precisely on heavily customized files, which are the ones whose agent rules
matter most.

**Observed.** Upgrading Palimpsest to 1.1.19 appended
`manual-verification-precondition v2` to the end of `AGENTS.md` and `CLAUDE.md`
and left v1 inside the implementation-workflow step. v1 carries the unrestricted
deterministic-test escape hatch that let a failed evidence probe be demoted to a
passing secondary check; v2 exists specifically to close that hole (task 003).
The fix landed inert, in a position nothing reads, beside the rule it was meant
to replace. Corrected there by hand in commit `a83d88b`.

## ⚠️ Constraints and Considerations

- Do not "fix" this by having the merge overwrite protected blocks generally.
  The conservative refusal is the point: replace in place **only** when the old
  block is provably unmodified, and conflict otherwise.
- This is the same family as task 007 but not the same defect. 007 adds an
  explicit `removes` field for retiring a capability; here no migration declared
  anything wrong — the insertion logic cannot recognise a supersession. 007 does
  not fix this, and this does not remove the need for 007.
- Framework-internal: no migration record, so it ships immediately.
- Any project already upgraded across an inline capability bump may hold a
  contradictory pair. The audit check is what makes that findable.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/012-marker-supersession.md)"$'\n\nExecute this task in the current project.'
```
