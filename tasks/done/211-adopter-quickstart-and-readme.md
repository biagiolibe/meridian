# Task 211 — Publish an adopter quick start and separate maintainer content

> **ID**: `211`
> **Category**: Documentation
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

The README has 721 lines and mixes adopter instructions with maintainer
material: Codex approvals, the read guard, token usage, and the release
procedure. Its Roadmap section names work that is already closed. Give a
newcomer a short path from install to a first closed task, using the
findings of task 209 and the status established by task 210.

## Acceptance Criteria

- [x] `docs/QUICKSTART.md` takes a newcomer, in order, through:
  prerequisites; a pinned install for Claude Code and for Codex;
  `/meridian-init`; choosing a workflow mode; one Lean Delivery task from
  creation to cleanup; and where to go next.
- [x] Every friction recorded in `docs/CLEAN_INSTALL_VERIFICATION.md` is
  either corrected in the README or the quick start, or listed in the handoff
  with the reason it was left.
- [x] The README's opening, before the first `##` section after the
  introduction, links the quick start. Maintainer-only sections move to
  `CONTRIBUTING.md` or an existing `docs/` page, and every moved anchor that
  another tracked file links to is updated.
- [x] The Roadmap section either links the open queue and plan or is removed.
  It names no closed work as upcoming.
- [x] No managed text or template changes. If a correction needs one, it is
  listed in the handoff as a follow-up instead.
- [x] `python3 scripts/check_repository.py` and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `README.md` | Adopter entry point. |
| `docs/QUICKSTART.md` | New quick start. |
| `CONTRIBUTING.md` | Destination of maintainer sections. |
| `docs/CLEAN_INSTALL_VERIFICATION.md` | Findings to address (task 209). |

## Technical Context

- `check_repository.py` validates local Markdown links, so moved sections
  surface as broken links.
- Documentation-only change: the test suite may be skipped, recorded per
  `docs/CONTEXT_BUDGET_POLICY.md`.

## Validation

- `python3 scripts/check_repository.py`
- `git diff --check`

## Out of scope

The worked example (task 212), the platform matrix (task 213), and template
changes.

## Dependencies

- **Depends on**: 209, 210
- **Blocks**: 212
