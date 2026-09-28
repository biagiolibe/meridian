# Task 060 — Install Meridian self-hosting capability surfaces

> **ID**: `060`
> **Category**: Architecture / Workflow Distribution
> **Priority**: 🔴 P1
> **Estimate**: ~5–7h
> **Assigned to**: Codex
> **Session**: 2026-09-28 implementation

## 🎯 Objective

Install the first `meridian-self-hosting` profile defined by Task 057 after the
manifest/catalog, cross-mode audit, generated-router, and bounded-worktree
foundations are stable.

Factor and deliver only the workflow-neutral canonical policy blocks selected
by the design, declare every managed copy and shared source, and bootstrap the
live Meridian manifest without claiming host activation that has not been
probed.

## 📋 Acceptance Criteria

- [x] The live Meridian manifest retains `workflowMode: lean-delivery`, enables
      the versioned `meridian-self-hosting` profile, and declares the exact
      required versions and surfaces of every included capability.
- [x] `LANGUAGE_POLICY.md` is a managed local copy whose project-owned language
      value remains upgrade-safe and whose protected canonical policy is
      integrity-checked.
- [x] A local `docs/CONTEXT_BUDGET_POLICY.md` contains only the selected neutral
      minimal-status, task-first context, bounded-exploration, evidence-tier,
      validation-scoping, and communication rules; it contains no Governed-only
      lifecycle or role requirements.
- [x] A configured local `docs/EXECUTION_EVIDENCE_PROFILE.md` contains no
      unresolved placeholder that could receive `PASS`.
- [x] Queue briefing and read guard use the declared repository-owned shared
      sources. `.codex/hooks.json` installs only the supported Codex adapter;
      Claude hook configuration remains represented separately.
- [x] Worktree-safety policy and command rules reflect Task 056's final bounded
      lifecycle surface and remain distinct from proof of sandbox access,
      project trust, or command success.
- [x] Canonical shared policy text has one authoritative source. Generated or
      managed copies use capability markers and migrations without duplicating
      competing policy ownership.
- [x] Migrations name the exact managed paths they add, move, update, or retire;
      shared sources receive integrity records without duplicate marker blocks.
- [x] Bootstrap records observed installation state and leaves every unprobed
      host-dependent capability `UNVERIFIED`, `ADVISORY`, or `UNSUPPORTED` as
      required by the catalog.
- [x] Lean and Governed initialization, adoption, and upgrade fixtures preserve
      existing consumers while delivering only their applicable capability
      surfaces.
- [x] Profile-aware audit reports no missing, empty, drifted, or contradictory
      installation surface for Meridian. It does not need to return aggregate
      `PASS` until Task 061 supplies host evidence.
- [x] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` | Authoritative selected profile and managed surface. |
| `.meridian/manifest.json` | Live self-hosting declaration and evidence snapshot. |
| `LANGUAGE_POLICY.md` | Managed language-policy surface. |
| `docs/CONTEXT_BUDGET_POLICY.md` | New neutral context and validation policy. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | New configured evidence profile. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | Lean routing and selected marked policy references. |
| `.codex/hooks.json` | Codex read-guard adapter configuration. |
| `.codex/rules/meridian.rules` | Bounded worktree command policy. |
| `hooks/queue-briefing.sh`, `hooks/read-guard.sh`, `hooks/hooks.json` | Shared-source hook surfaces. |
| `templates/workflows/lean-delivery/` | Lean delivery of applicable neutral capabilities. |
| `templates/workflows/governed-sdd/` | Governed canonical blocks and compatibility. |
| `migrations/`, `release-baselines/` | Managed delivery and historical compatibility. |
| `scripts/meridian.py` | Bootstrap, upgrade, generation, and integrity handling. |
| `tests/` | Initialization, upgrade, marker, hook, and profile audit coverage. |

## 🧩 Technical Context

Task 057 selected the initial profile but deliberately changed no runtime
surface. Tasks 058 and 059 make declarations and audits meaningful. Task 052
must make generated router upgrades safe before new managed policy routes are
introduced. Task 056 must stabilize the worktree-safety commands and rules
before this task declares their final self-hosted surface.

## 🔨 Suggested Implementation

1. Factor the selected neutral canonical blocks and add their catalog/profile
   records without copying Governed-only procedures.
2. Install local managed copies, shared-source declarations, hook adapters, and
   exact migrations through the established router-aware upgrade path.
3. Bootstrap the live manifest from observed state and verify installation with
   the cross-mode audit while retaining conservative host states.

## ⚠️ Constraints and Considerations

- Do not change Meridian's workflow mode or import Governed task states/roles.
- Do not claim hook or execpolicy enforcement from file presence.
- Do not duplicate repository-owned hook scripts as managed local copies.
- Do not weaken project-owned language values or overwrite consumer custom text.
- Do not bypass migrations or capability-marker baselines for managed changes.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: Meridian installs the declared host adapters and policy surfaces
but records conservative activation states until Task 061 performs real probes.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Codex trusted project | no local hook declaration | adapter installed, activation unverified | Project trust, supported Codex hook loading, and Task 061 probe. | Keep `UNVERIFIED`; use policy guidance without enforcement claim. |
| Claude plugin | repository hooks exist | shared sources declared and integrity-checked | Supported plugin activation and Task 061 probe. | Retain `ADVISORY` or `UNVERIFIED`. |
| Host-neutral CLI | no effective self-hosting declaration | installed profile is auditable | Tasks 058 and 059 plus complete managed surfaces. | Audit exits 1 or 2 and names retained state. |

## 🔗 Dependencies

- **Depends on**: 059, 056, 052
- **Blocks**: 061

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/060-install-meridian-self-hosting-surfaces.md)"$'\n\nExecute this task in the current project.'
```
