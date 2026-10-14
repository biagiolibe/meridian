# Task 210 — Publish the public surface and enforce the release bump

> **ID**: `210`
> **Category**: Feature
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

Implement Decisions 1–5 of
[docs/ADR_PUBLIC_SURFACE_AND_STABILITY.md](../docs/ADR_PUBLIC_SURFACE_AND_STABILITY.md).
The ADR was accepted on 2026-10-14; the stable line starts at `1.3.0`.

## Acceptance Criteria

- [ ] `docs/PUBLIC_SURFACE.md` classifies every top-level CLI command and its
  subcommands as Stable, Host-facing, Experimental, or Internal by the
  Decision 1 rule. It also names the stable registries: stop codes, schemas,
  the manifest `protocolVersion`, capability markers, and plugin command and
  skill names.
- [ ] A test fails when a top-level command or subcommand from the CLI parser
  is missing from `docs/PUBLIC_SURFACE.md`, or when the document names one
  that does not exist.
- [ ] Every Experimental and Internal command says so in its `--help` text.
- [ ] `scripts/release.py prepare` refuses a `patch` bump when the release
  adds a migration or a fragment has an `Added`, `Deprecated`, or `Removed`
  subsection. It refuses a `minor` bump when a fragment has `Removed`. It
  checks `--version X.Y.Z` the same way. Each refusal names the rule and the
  offending fragment or migration. Tests cover each refusal and each allowed
  case.
- [ ] `CONTRIBUTING.md` states the versioning and deprecation rules of
  Decisions 2 and 3.
- [ ] The README status line is replaced as Decision 5 requires.
- [ ] One changelog fragment states the release check under `Changed` and the
  surface document under `Documentation`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `prepare` bump selection and fragment rendering. |
| `scripts/meridian.py` | CLI parser and `--help` text. |
| `docs/PUBLIC_SURFACE.md` | New classification. |
| `CONTRIBUTING.md` | Release procedure. |
| `README.md` | Status line. |
| `tests/` | Release and surface tests. |

## Technical Context

- `release.py` already reads the fragment subsections and computes the
  ledger's `migrations`. The check uses those facts, not a diff.
- No template or managed text changes, so the release stays CLI-only unless
  another task adds a migration.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Deprecating or removing any existing surface, cutting the release, and
adopter documentation beyond the status line (task 211).

## Dependencies

- **Depends on**: —
- **Blocks**: 211
