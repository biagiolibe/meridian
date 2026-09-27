# Task 058 — Add self-hosting manifest and capability-catalog support

> **ID**: `058`
> **Category**: Architecture / Manifest
> **Priority**: 🔴 P1
> **Estimate**: ~5–7h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Implement the protocol and schema foundation defined by Task 057 so Meridian
can represent workflow mode, selected capability profiles, catalog metadata,
managed surfaces, and evidence states independently from migration history.

This task adds no self-hosted capability declaration to the Meridian manifest
and makes no host-activation claim. It establishes the validated data model
that later audit and installation tasks consume.

## 📋 Acceptance Criteria

- [x] The manifest model has a protocol-versioned canonical `workflowMode`
      field and rejects conflicting simultaneous `mode` and `workflowMode`
      values. Compatibility readers accept legacy `mode`; writers follow the
      protocol transition defined by Task 048.
- [x] A versioned capability catalog represents capability ID and version,
      applicable workflow modes, self-hosting eligibility, supported host
      profiles, installation forms, managed surfaces, evidence requirements,
      and capability dependencies.
- [x] Manifest validation supports `capabilityProfiles` with profile version,
      required capability versions, complete managed surfaces, installation
      state, per-host activation state, verification state, and evidence
      references.
- [x] State validation implements the Task 057 vocabularies and rejects an
      unsupported state, an empty applicable managed surface, missing evidence
      required by a positive claim, or `NOT_APPLICABLE` without a catalog-backed
      rationale.
- [x] `appliedMigrations` remains historical provenance and is never projected
      into effective capability installation, activation, or verification.
- [x] A legacy Lean manifest whose migration history names Governed
      capabilities loads without fabricating capability declarations. Its
      compatibility projection is deterministic and covered by tests.
- [x] Bootstrap and upgrade planning can inspect catalog/profile declarations
      without changing project files or silently promoting observed state.
- [x] Schema, catalog, parser, writer, invalid-state, compatibility, and
      round-trip tests cover both Lean and Governed manifests.
- [x] No hook, policy document, self-hosting surface, capability marker, or host
      probe is installed by this task.
- [x] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` | Authoritative design and state model. |
| `.meridian/manifest.json` | Legacy Lean manifest fixture; do not enable the profile here yet. |
| `scripts/meridian.py` | Manifest parsing, validation, bootstrap, upgrade, and persistence. |
| `migrations/` | Protocol/schema transition metadata. |
| `release-baselines/` | Backwards-compatible manifest and workflow fixtures. |
| `tests/test_meridian_cli.py` | Parser, migration, compatibility, and round-trip tests. |
| `tests/test_check_repository.py` | Repository-level schema and baseline validation. |

## 🧩 Technical Context

The current manifest uses `mode`, records only managed-file hashes, and carries
an `appliedMigrations` list that can mention capabilities never installed under
Lean Delivery. Task 057 requires those concerns to become independent:
migration history records traversal, while effective state records declared
capabilities and evidence snapshots.

Task 048 is a prerequisite because adding the protocol-versioned schema before
the CLI enforces `protocolVersion` would let incompatible readers accept or
rewrite state they do not understand.

## 🔨 Suggested Implementation

1. Define typed catalog, profile, surface, state, and evidence structures plus
   strict validation independent of audit output.
2. Add the backwards-compatible manifest reader and protocol-aware writer,
   preserving historical fields without inferring effective capability state.
3. Add migration/baseline fixtures and exhaustive invalid-state tests, leaving
   the Meridian repository profile disabled until Task 060.

## ⚠️ Constraints and Considerations

- Do not enable `meridian-self-hosting` in the live manifest.
- Do not infer a capability from a migration ID, marker, file, or rule.
- Do not treat a catalog entry as installation or activation evidence.
- Do not install hooks or policy documents and do not change audit exit codes.
- Preserve existing Lean and Governed consumers through the declared protocol
  compatibility boundary.
- Repository artifacts are English-only.

## Host impact

Classification: NOT_APPLICABLE

Rationale: this task adds a host-neutral schema and catalog model only. It does
not install adapters, activate hooks, change host policy, or claim enforcement.

## 🔗 Dependencies

- **Depends on**: 057, 048
- **Blocks**: 059, 060, 061

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/058-add-self-hosting-manifest-and-capability-catalog.md)"$'\n\nExecute this task in the current project.'
```
