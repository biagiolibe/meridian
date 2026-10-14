# Task 215 — Remove private-project references from the distributed tree

> **ID**: `215`
> **Category**: Documentation
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

The developer's two private projects that adopted Meridian are named in
documentation, hook comments, migration descriptions, tests, and the
changelog. Remove documents that are about those projects rather than about
Meridian. Anonymize every other mention, keeping the evidence and dropping the
identity. Prevent the names from returning anywhere in the tree.

Task records under `tasks/` (archived records, handoffs, and
`tasks/QUEUE_ARCHIVE.md`) were already anonymized by a coordination commit on
`main` on 2026-10-15, because a task branch may not edit other tasks' records.
That commit also turned the last record link to the routing evidence document
into plain text. Task 216 was cancelled, and its name-guard scope moved here.

## Acceptance Criteria

- [ ] Every document under `docs/` that mentions either project is classified
  in the handoff as `delete` or `anonymize`:
  - `delete`: the document's subject is the other project, for example the
    routing evidence report of consumer project A;
  - `anonymize`: the document is about Meridian and only cites the project as
    evidence.
  Every tracked link to a deleted document is removed or redirected.
- [ ] Anonymized text names neither project, nor its domain terms or crate
  names. Each mention becomes a neutral description, using the labels the
  coordination commit used in `tasks/`: "consumer project A" and "consumer
  project B". Each measured fact, such as a count, size, or date, is
  kept.
- [ ] The same applies to `hooks/`, `migrations/` (descriptions and
  `CAPABILITY_MARKERS.md`), `tests/` (names, docstrings, and fixtures),
  `CHANGELOG.md`, and `.meridian/`. Before editing a published migration
  description, the handoff records whether any digest, baseline, or check
  covers it. A covered field is left unchanged and listed instead.
- [ ] `scripts/check_repository.py` fails when any tracked file, including
  everything under `tasks/`, contains a denied name. The check matches
  case-insensitively at word boundaries, where `_`, `-`, `.`, and `/` also
  count as boundaries, so identifiers such as `NAME_ROUTING` and `../name` are
  caught. The denied names are stored only as SHA-256 hashes of their
  lowercase form. A test covers a plain match, an identifier match, and a
  non-match on a substring such as `refusal`.
- [ ] The handoff lists the GitHub Release bodies that still contain either
  name, with each release tag. Editing them is a developer action.
- [ ] No behavior changes. Test renames keep every assertion.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/` | Documents to delete or anonymize. |
| `hooks/`, `migrations/`, `tests/`, `CHANGELOG.md`, `.meridian/` | Mentions to anonymize. |
| `scripts/check_repository.py` | New name guard. |

## Technical Context

- Find mentions with `git grep -inwE` on both names. A plain substring search
  also matches `refusal`.
- Do not write either name into a new tracked file, a commit message, or the
  handoff. Refer to them as "consumer project A" and "consumer project B".

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Other tasks' records under `tasks/`, which a task branch may not edit; Git
history; and GitHub Release bodies.

## Dependencies

- **Depends on**: —
- **Blocks**: none
