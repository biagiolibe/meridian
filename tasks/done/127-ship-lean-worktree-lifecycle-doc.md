# Task 127 — Distribute `docs/WORKTREE_LIFECYCLE.md` to Lean Delivery projects

> **ID**: `127`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Upgrade rehearsal for release 1.2.6, 2026-10-03

## Objective

The shipped Lean Delivery `PROJECT_WORKFLOW.md` tells agents to run the candidate
validation "defined in `docs/WORKTREE_LIFECYCLE.md`" (tasks 122 and 125), but that
document is not in the Lean managed-file set, so `meridian upgrade` never
installs or refreshes it. In an upgrade rehearsal from the 1.2.5 baseline, the
Lean project kept an outdated copy while Governed SDD received the current
document. Make the Lean document a managed file so Lean adopters receive it, and
fix the unreleased 1.2.6 migration and changelog that currently over-claim.

## Acceptance Criteria

- [x] `docs/WORKTREE_LIFECYCLE.md` is part of the Lean Delivery managed-file set
  in `managed_files_for_workflow`, and `meridian upgrade --apply` installs or
  refreshes it from `templates/workflows/lean-delivery/docs/WORKTREE_LIFECYCLE.md`.
- [x] Packaged legacy baselines that never shipped the file do not break
  adoption or upgrade: inclusion follows the existing rule used for Codex files
  (include it only when the workflow snapshot supplies it), and a test proves
  an adoption from such a baseline still works.
- [x] A Lean project that never had the file receives it; a project whose copy
  matches the installed baseline is replaced; a locally edited copy produces a
  normal three-way merge or conflict result, never a silent overwrite.
- [x] The decision about `templates/workflows/lean-delivery/docs/COMPLETION_REPORT_TEMPLATE.md`
  (shipped in the template tree but not managed) is recorded in the handoff: add
  it with this change if the Lean workflow references it, otherwise state why it
  stays unmanaged.
- [x] Migration `060-unattended-closure-command-policy` is extended, not
  replaced, because 1.2.6 is unpublished (confirm no tag at or after `v1.2.6`
  exists on `origin` before editing it). Its `managedPaths` and `delta` list every
  managed file changed since migration 059: both Codex rules files, both
  `docs/WORKTREE_LIFECYCLE.md` files, both `docs/EXECUTION_EVIDENCE_PROFILE.md`
  files, the Lean `PROJECT_WORKFLOW.md`, and the Governed `COMPLETION_REPORT_TEMPLATE.md`,
  `LIFECYCLE_ORCHESTRATION.md`, and `workflows/REVIEW.md`. Verify the list
  against `git diff` of the template tree rather than from memory.
- [x] The Lean `PROJECT_WORKFLOW.md` reference to the document is accurate for a
  freshly initialized project and for an upgraded one.
- [x] A changelog fragment `changelog.d/127.md` states that Lean projects now
  receive the lifecycle document through `upgrade --apply`, with an Upgrade
  note about a locally edited copy. The 1.2.6 changelog section, already
  assembled from earlier fragments, is updated to match this change and to stop
  claiming that the document was updated for Lean before this task.
- [x] A test upgrades a Lean project from the 1.2.5 baseline and asserts the
  document equals the current template afterwards; the same test covers a
  project that lacks the file and one with a local edit.
- [x] `python3 scripts/check_repository.py` and the unit tests pass, including
  `test_oldest_published_release_upgrades_to_current_in_one_apply`.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `managed_files_for_workflow` managed-file set for `lean-delivery`. |
| `templates/workflows/lean-delivery/docs/WORKTREE_LIFECYCLE.md` | Document to distribute. |
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md` | Contains the reference to the document. |
| `migrations/060-unattended-closure-command-policy.json` | Unreleased migration to extend. |
| `CHANGELOG.md`, `changelog.d/` | 1.2.6 section and new fragment. |
| `tests/test_meridian_cli.py` | Upgrade and adoption tests. |
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | Upgrade path and release-note contract. |

## Technical Context

- Managed set for Lean today: `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md`,
  `LANGUAGE_POLICY.md`, `docs/CONTEXT_BUDGET_POLICY.md`,
  `docs/EXECUTION_EVIDENCE_PROFILE.md`, plus the Codex files when the snapshot
  supplies them (`scripts/meridian.py`, `managed_files_for_workflow`).
- Governed SDD already manages every `docs/**/*.md`, which is why the rehearsal
  showed it fully updated.
- Task 125 made the gate wording project-declared; the Lean workflow now depends
  on this document for the per-outcome definition, so a stale or missing copy
  leaves Lean agents without it.
- Do not hand-edit the template copy for this task; it already carries the
  current text. This task changes distribution only.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`
- Rehearsal: lock a Lean project at the 1.2.5 baseline, run `meridian upgrade
  --apply` from the current tree, and confirm the document matches the template.

## Out of scope

Changing the document's content, redefining the gate, publishing the release,
and adding any other Lean file to the managed set beyond the decision recorded
for `COMPLETION_REPORT_TEMPLATE.md`.

## Dependencies

- **Depends on**: 125
- **Blocks**: none
