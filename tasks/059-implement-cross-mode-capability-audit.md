# Task 059 — Implement cross-mode capability audit semantics

> **ID**: `059`
> **Category**: Architecture / Validation
> **Priority**: 🔴 P1
> **Estimate**: ~4–6h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Make `meridian audit` declaration-driven and non-vacuous for every workflow
mode, using Task 058's catalog and manifest model while retaining protected
marker-integrity checks.

The audit must distinguish static installation, host activation, and effective
verification. It must never report success merely because no capability marker
or auditable surface was found.

## 📋 Acceptance Criteria

- [ ] `meridian audit` begins from the locked project's manifest declarations
      and capability catalog in both Lean Delivery and Governed SDD modes.
- [ ] Every declared capability and applicable host profile emits named results
      using `PASS`, `ADVISORY`, `UNVERIFIED`, `NOT_APPLICABLE`, or `FAIL` with
      evidence and rationale consistent with Task 057.
- [ ] Aggregate exit codes are `0` for complete passing evidence, `1` when at
      least one result is `ADVISORY` or `UNVERIFIED` and none is `FAIL`, and `2`
      for any failure or invalid/unauditable required declaration.
- [ ] A locked legacy project with no `capabilityProfiles` receives the defined
      compatibility result instead of `No capability markers found to audit.`
      The result becomes a failure when the active protocol requires explicit
      declarations.
- [ ] An applicable declaration with an empty, missing, drifted, contradictory,
      or unresolvable managed surface is `FAIL`; migration history cannot
      satisfy it.
- [ ] A `NOT_APPLICABLE` result is accepted only when the catalog excludes the
      workflow, selected profile, or named host and the report prints that
      exact rationale.
- [ ] Existing marker-integrity, duplicate-heading, capability-move, and entry-
      router checks remain distinct audit items and retain their protections.
- [ ] Output reports per-state counts, the worst aggregate result, and enough
      surface/evidence identity to diagnose a failure without dumping unrelated
      project context.
- [ ] Fixtures cover complete declarations, legacy Lean manifests, empty
      surfaces, missing policy files, missing hook configuration/shared sources,
      stale evidence, invalid positive claims, valid exclusions, and mixed
      aggregate results.
- [ ] No self-hosted profile or managed surface is installed by this task.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` | Authoritative audit states and exit codes. |
| `scripts/meridian.py` | Audit command, capability detection, and report aggregation. |
| `tests/test_meridian_cli.py` | Cross-mode audit and compatibility fixtures. |
| `tests/test_check_repository.py` | Repository invariant coverage. |
| `migrations/` | Capability and schema history used as provenance only. |
| `templates/workflows/lean-delivery/` | Lean fixtures without implicit Governed capability claims. |
| `templates/workflows/governed-sdd/` | Existing protected-marker audit surface. |

## 🧩 Technical Context

Current audit helpers return no capability results outside `governed-sdd`, and
`run_audit()` maps an empty result list to exit zero with `No capability markers
found to audit.` Task 057 makes this invalid for a locked project: audit must
evaluate declared requirements, not whatever markers happen to be discoverable.

## 🔨 Suggested Implementation

1. Separate installation, activation, verification, and legacy marker-integrity
   checks into typed audit items.
2. Drive applicability and expected surfaces from Task 058's catalog/profile
   model, then implement deterministic aggregation and compatibility behavior.
3. Add adversarial fixtures before changing the live Meridian declaration.

## ⚠️ Constraints and Considerations

- Do not collapse installation and activation into one result.
- Do not turn absent host evidence into `PASS` or `NOT_APPLICABLE`.
- Do not remove or weaken existing marker-integrity checks.
- Keep audit read-only; it must not repair manifests, files, or evidence.
- Do not enable Meridian's self-hosted profile in this task.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: audit reports host activation no stronger than the evidence
recorded for the exact named host profile.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Host-neutral CLI | governed-only marker audit | cross-mode declared-state audit | Valid Task 058 catalog and manifest declaration. | Exit 1 or 2 with the missing/invalid evidence named. |
| Codex project | empty Lean audit can pass | activation remains evidence-bounded | Installed adapter plus a matching host probe record. | `UNVERIFIED`; never infer enforcement from config presence. |
| Claude plugin | marker/config presence can be over-read | activation remains evidence-bounded | Installed adapter plus supported plugin probe evidence. | `ADVISORY`, `UNVERIFIED`, or `UNSUPPORTED` as catalogued. |

## 🔗 Dependencies

- **Depends on**: 058
- **Blocks**: 056, 060, 061

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/059-implement-cross-mode-capability-audit.md)"$'\n\nExecute this task in the current project.'
```
