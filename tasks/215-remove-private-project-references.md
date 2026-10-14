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
identity. Prevent the names from returning. Task records under `tasks/` are
handled by task 216.

## Acceptance Criteria

- [ ] Every document under `docs/` that mentions either project is classified
  in the handoff as `delete` or `anonymize`:
  - `delete`: the document's subject is the other project, for example
    `docs/PALIMPSEST_ROUTING_EVOLUTION_EVIDENCE.md`;
  - `anonymize`: the document is about Meridian and only cites the project as
    evidence.
  Every tracked link to a deleted document is removed or redirected.
- [ ] Anonymized text names neither project, nor its domain terms or crate
  names. Each mention becomes a neutral description such as "a Governed SDD
  consumer project". Each measured fact, such as a count, size, or date, is
  kept.
- [ ] The same applies to `hooks/`, `migrations/` (descriptions and
  `CAPABILITY_MARKERS.md`), `tests/` (names, docstrings, and fixtures),
  `CHANGELOG.md`, and `.meridian/`. Before editing a published migration
  description, the handoff records whether any digest, baseline, or check
  covers it. A covered field is left unchanged and listed instead.
- [ ] `scripts/check_repository.py` fails when a tracked file outside
  `tasks/` contains a denied name, matched as a whole word and
  case-insensitively. The denied names are stored only as SHA-256 hashes of
  their lowercase form. A test covers a match, a non-match on a substring such
  as `refusal`, and the exclusion of `tasks/`.
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

Task records under `tasks/` (task 216), Git history, and GitHub Release
bodies.

## Dependencies

- **Depends on**: —
- **Blocks**: 216
