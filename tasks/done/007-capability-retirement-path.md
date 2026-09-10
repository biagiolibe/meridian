# Task 007 — A retirement path for capabilities

> **ID**: `007`
> **Category**: Architecture (CLI + migration schema)
> **Priority**: 🟡 P2
> **Estimate**: ~1 day
> **Assigned to**: unassigned

## 🎯 Objective

Add the missing inverse of the capability-marker mechanism: a way to retire, merge,
or supersede a capability block instead of only ever appending one.

Buys no tokens itself. It is what makes tasks 001–006 durable rather than temporary.

## 📋 Acceptance Criteria

- [x] The migration record schema gains `removes` / `supersededBy`.
- [x] `meridian upgrade` honors it: a retired marker block is deleted from every
      managed path.
- [~] Merging two overlapping capabilities into one canonical home with a
      cross-reference at the other sites is supported and documented —
      **scoped deviation, see below.**
- [x] `meridian audit` flags a rule appearing under more than one heading.
- [x] `migrations/CAPABILITY_MARKERS.md` documents the retirement lifecycle.
- [x] Tests cover: retire a block, retire an already-absent block (idempotent), and
      refuse to retire a block a project has locally modified.
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

### Scoped deviation on the "cross-reference" criterion

`supersededBy` is implemented as a report-only pointer: it names the
canonical capability in `meridian upgrade`'s plan detail and is available to
`meridian audit`, but nothing writes a cross-reference line into the managed
file the retired block is deleted from. Deliberate, not an oversight: a slot
left behind inside a block the three-way merge keeps reconciling is exactly
the protected-content-with-an-editable-hole tension task 014 recorded as
out of scope for `execution-assets` (see 014's "Related finding" section).
If a human wants a pointer left behind for readers, that is ordinary
unprotected prose added by the same migration, outside any marker — the
mechanism enforces nothing about it and writes nothing there itself. Task
008 (the first real retirement) is where this trade-off gets exercised for
real; if it turns out an in-file pointer is actually needed, that is 008's
finding to make, not a gap to silently work around here.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Upgrade path, audit check. |
| `migrations/CAPABILITY_MARKERS.md` | Lifecycle documentation. |
| `tests/test_meridian_cli.py` | Coverage. |

## 🧩 Technical Context

Verified (`docs/AUDIT_TOKEN_EFFICIENCY.md` F3): no removal, compaction, or
supersession path exists. `migrations/*.json` carries `capabilities`, `managedPaths`,
`verification` — all additive. `prune_stale_baselines` prunes baseline *snapshots*,
not marker blocks. Every upgrade appends to 2–4 documents and nothing ever merges or
retires one.

The duplication-detection half matters as much as the deletion half: the paraphrase
duplication between `CLAUDE.md` and `PROJECT_WORKFLOW.md` is invisible to any diff
tool, and is how the current triplication of the reviewer-integrator identity rule
happened.

## ⚠️ Constraints and Considerations

- Retiring a block a project has locally modified must **refuse and report**, not
  silently discard the operator's edit. Reuse the reconciliation shape
  `CAPABILITY_MARKERS.md` already defines for merge conflicts.
- Task 008 is the first real customer; treat it as the acceptance test for this one.
- **Extend task 014's baseline infrastructure; do not build a second one.**
  Commit `aaa1d57` added `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json`
  and `check_repository.py`'s `check_capability_marker_baselines` specifically
  to know what content a marker at a given version should have. Its final loop
  fails the moment a recorded capability disappears from the live templates —
  which a legitimate retirement does on purpose. Read that commit before
  designing this task's `removes` mechanics: the fix is to teach that
  existing check about migration-declared removal (`retired_capability_ids`),
  not to invent a parallel record of the same fact. The two *do* stay
  separate for a different reason: that JSON file is a snapshot of the
  framework's *current* template content (no version history), while
  "was this project's copy of a retired block locally modified" is answered
  by the project's own `.meridian/baselines/<version>/` snapshot — already
  the reference `plan_from_baseline`'s three-way merge and
  `append_only_new_markers` use for the identical question. Reuse that, too,
  rather than a third source of truth.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 008

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/007-capability-retirement-path.md)"$'\n\nExecute this task in the current project.'
```
