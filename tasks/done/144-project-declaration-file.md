# Task 144 — Add `.meridian/project.json` as the project declaration surface

> **ID**: `144`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Palimpsest defect report D6/D7, design approved 2026-10-04
> **Review**: independent review required before integration (new public schema and CLI surface)

## Objective

Managed capability blocks need project values they cannot contain: canonical
locations (`execution-assets` v2 says a project redeclares them "in this section",
which is a managed block), the reviewer-integrator name and slug
(`<PROJECT_NAME>`/`<project-slug>` placeholders), the mapping from changed surfaces
to validation commands, and CI facts. Today `resolve_project_locations` parses
backticked paths from the prose right after the `execution-assets` END marker,
which is fragile, and projects restate rules around the values. Provide one
machine-readable declaration and a read command, so projects hold values, not
prose.

## Design (approved)

`.meridian/project.json`, consumer-owned, never written by `upgrade --apply`:

```json
{
  "version": 1,
  "project": { "name": "Palimpsest", "slug": "palimpsest" },
  "locations": {
    "queue": "docs/TASK_QUEUE.md",
    "taskRoots": ["tasks"],
    "reviewRoot": "tasks/reviews",
    "handoffRoot": "tasks/handoffs",
    "adrLog": "docs/ARCHITECTURE_DECISIONS.md",
    "plan": "PROJECT_PLAN.md"
  },
  "validationScoping": [
    { "paths": ["crates/domain/**"], "commands": ["cargo test -p domain"] }
  ],
  "ci": { "provider": "github-actions", "requiredChecks": ["test"] }
}
```

- Every key except `version` is optional; an absent key keeps today's default.
  `ci` may also be the string `"none"`. The queue archive is always the queue's
  sibling `QUEUE_ARCHIVE.md` and is not declarable.
- `task-identity.json` and `candidate-validation.json` stay separate files.
- Resolution order for locations: `project.json`, then the legacy prose after the
  `execution-assets` block (with a deprecation warning on stderr), then defaults.
- Paths are project-relative, without `..`; unknown keys and invalid values fail
  with a message naming the key.

## Acceptance Criteria

- [x] The schema above is documented (reference doc plus a JSON schema under
  `schemas/`) and validated on every read.
- [x] `meridian locations` reads `project.json` first and accepts
  `--field queue|queue-archive|task-roots|review-root|handoff-root|adr-log|plan`.
  Existing `queue` and `task-roots` output is unchanged for projects without the
  file. The legacy prose path still resolves and warns once per invocation.
- [x] `meridian project show [--field <name>] [--format json|text]` prints the
  resolved declaration; `--field reviewer-author` prints
  `<name> Reviewer-Integrator <reviewer-integrator@<slug>.local>` and fails with a
  clear message when `project` is undeclared.
- [x] Every internal consumer of locations (`resolve_project_locations`, stage,
  task identity, context authority, hooks via `meridian locations`) uses the same
  resolver; no second default list is introduced.
- [x] `meridian setup --check` reports a missing `project.json` as advisory and
  can propose one from the current resolved values; `--apply` writes it only after
  the existing consent flow. `upgrade --apply` never writes it.
- [x] Tests cover: no file (defaults); full file; partial file; invalid version,
  key, absolute or traversing path; legacy prose with warning; `project.json`
  overriding prose; every `--field`; `reviewer-author` with and without `project`.
- [x] An independent review approves the schema and CLI before integration; the
  handoff records the reviewer verdict.
- [x] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `resolve_project_locations`, `ProjectLocations`, `locations` parser, new `project` subcommand, `setup`. |
| `schemas/` | New `project-v1.schema.json`. |
| `docs/` | Reference description of the declaration. |
| `tests/` | Resolver and CLI tests. |

## Technical Context

- `validationScoping` and `ci` are declared and printed only in this task; using
  them in workflow text is task 145.
- Keep the resolver free of Git calls so hooks stay fast.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Capability text changes (task 145), merging `task-identity.json` or
`candidate-validation.json` into the new file, and removing the legacy prose
fallback (a later release).

## Dependencies

- **Depends on**: —
- **Blocks**: 145
