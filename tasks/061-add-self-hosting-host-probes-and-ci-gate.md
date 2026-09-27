# Task 061 — Add self-hosting host probes and CI dogfooding gate

> **ID**: `061`
> **Category**: Host Integration / CI
> **Priority**: 🔴 P1
> **Estimate**: ~4–6h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Complete Meridian's self-hosting profile with evidence-bound host probes and a
CI gate that rejects missing, drifted, or unverified required capability state.

Static installation, host activation, and behavior evidence must remain
separate. A supported host is `ENFORCED` only after a versioned real-host probe
satisfies `docs/HOST_CAPABILITY_CONTRACT.md` for that exact profile.

## 📋 Acceptance Criteria

- [ ] A read-only profile doctor resolves every declared capability, managed
      copy, shared source, adapter, host profile, evidence record, and required
      probe from the repository root.
- [ ] Versioned probes exist for each host/profile combination that the catalog
      claims can reach `ENFORCED`; each records host/version, invocation mode,
      trust/configuration layer, evidence artifact, observation time, and exact
      behavior tested.
- [ ] Codex probes distinguish hook configuration, project trust, filesystem
      access, execpolicy decision, command result, and read-guard behavior.
- [ ] Claude probes distinguish shared-source integrity, plugin activation,
      permission behavior, queue briefing, and read-guard behavior.
- [ ] Unsupported or unavailable host behavior remains `UNSUPPORTED`,
      `ADVISORY`, or `UNVERIFIED` with a usable fallback. No static fixture or
      CI-only test promotes host activation to `ENFORCED`.
- [ ] CI runs the profile doctor and profile-aware audit in a clean checkout and
      rejects aggregate exit 1 or 2 for every capability whose profile contract
      requires CI-verifiable `PASS`.
- [ ] Host-dependent evidence that cannot exist in generic CI is evaluated
      against its declared support/fallback contract rather than fabricated or
      silently omitted.
- [ ] Negative tests remove a managed policy file, Codex hook declaration, and
      shared hook source independently and prove each produces `FAIL` rather
      than an empty successful audit.
- [ ] Tests prove that installed adapters without matching probe evidence remain
      `UNVERIFIED` and that catalog-backed exclusions produce visible
      `NOT_APPLICABLE` results.
- [ ] The live Meridian manifest records only evidence actually produced by
      completed probes and contains no machine-specific absolute path.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` | Dogfooding verification contract. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Host evidence and enforcement boundary. |
| `.meridian/manifest.json` | Profile declarations and evidence snapshots. |
| `scripts/meridian.py` | Profile doctor, audit integration, and evidence validation. |
| `.github/workflows/` | Clean-checkout dogfooding gate. |
| `.codex/hooks.json`, `.codex/rules/meridian.rules` | Codex activation surfaces. |
| `hooks/queue-briefing.sh`, `hooks/read-guard.sh`, `hooks/hooks.json` | Shared host adapters. |
| `tests/` | Deterministic audit, doctor, negative, and host-contract coverage. |

## 🧩 Technical Context

Task 060 installs and declares the profile but deliberately retains conservative
host states. This task supplies the final evidence layer. Generic CI can prove
schema, integrity, resolution, and deterministic behavior, but it cannot claim
that an interactive Codex or Claude host loaded project configuration unless a
real matching probe ran and its evidence is recorded.

## 🔨 Suggested Implementation

1. Implement the read-only profile doctor and versioned evidence-record format.
2. Add deterministic negative fixtures and the clean-checkout CI gate.
3. Run only the supported real-host probes, record exact evidence, and retain
   conservative fallbacks for every unavailable profile.

## ⚠️ Constraints and Considerations

- Do not make CI invent interactive host evidence.
- Do not store machine-specific absolute paths or unbounded raw logs.
- Do not weaken the gate to accept aggregate exit 1 for required deterministic
  capabilities.
- Do not mark a profile `ENFORCED` from configuration presence alone.
- Keep all probes read-only except for isolated temporary fixtures explicitly
  created by the probe contract.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: every positive host-enforcement claim is tied to a repeatable,
versioned probe for the exact supported profile; unavailable evidence produces
a conservative state and explicit fallback.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Codex trusted project | adapters installed, activation unverified | evidence-bound result | Supported version, trust/config activation, and successful real-host probes. | `UNVERIFIED` plus documented manual approval/policy fallback. |
| Claude plugin | shared adapters declared | evidence-bound result | Supported plugin version and successful briefing/read-guard probes. | `ADVISORY`, `UNVERIFIED`, or `UNSUPPORTED` with fallback. |
| Host-neutral CI | installation audit available | enforced dogfooding gate | Clean-checkout doctor/audit and deterministic fixtures pass. | CI failure with named capability and surface. |

## 🔗 Dependencies

- **Depends on**: 060, 047
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/061-add-self-hosting-host-probes-and-ci-gate.md)"$'\n\nExecute this task in the current project.'
```
