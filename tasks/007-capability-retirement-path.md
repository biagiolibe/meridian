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

- [ ] The migration record schema gains `removes` / `supersededBy`.
- [ ] `meridian upgrade` honors it: a retired marker block is deleted from every
      managed path.
- [ ] Merging two overlapping capabilities into one canonical home with a
      cross-reference at the other sites is supported and documented.
- [ ] `meridian audit` flags a rule appearing under more than one heading.
- [ ] `migrations/CAPABILITY_MARKERS.md` documents the retirement lifecycle.
- [ ] Tests cover: retire a block, retire an already-absent block (idempotent), and
      refuse to retire a block a project has locally modified.
- [ ] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

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

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: 008

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/007-capability-retirement-path.md)"$'\n\nExecute this task in the current project.'
```
