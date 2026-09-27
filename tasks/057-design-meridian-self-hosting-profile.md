# Task 057 — Design the Meridian self-hosting capability profile

> **ID**: `057`
> **Category**: Architecture / Governance
> **Priority**: 🔴 P1
> **Estimate**: ~3–4h
> **Assigned to**: unassigned
> **Session**: 2026-09-27 self-hosting profile design

## 🎯 Objective

Design an explicit self-hosting profile that lets the Meridian repository keep
the `LEAN_DELIVERY` lifecycle while consuming and verifying workflow-neutral
capabilities that Meridian already distributes to consumer projects.

The design must separate lifecycle semantics from operational capabilities so
that context discipline, validation scoping, host safeguards, and auditability
do not become available only by selecting the full Governed SDD lifecycle.
This task is design-only: it defines the model, compatibility boundary,
evidence states, migration strategy, and bounded implementation follow-ups
without changing runtime behavior or enabling hooks.

## 📋 Acceptance Criteria

- [ ] A design note at `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` defines the
      distinction between `workflowMode` and an independently declared set of
      capabilities. It preserves `lean-delivery` as Meridian's lifecycle and
      does not import Governed SDD task states, roles, or acceptance ceremony.
- [ ] The note defines the first self-hosted capability set and gives an
      inclusion or exclusion rationale for at least language policy, minimal
      read-only status, context budgeting, queue briefing, read guard,
      validation scoping, execution-evidence discipline, and worktree safety.
- [ ] The design distinguishes migration history from effective capability
      state. It specifies how the manifest records required capability version,
      managed surface, installation state, host activation state, verification
      state, and an explicit `NOT_APPLICABLE` rationale where appropriate.
- [ ] The design defines non-vacuous audit behavior for every workflow mode.
      A project that declares capabilities but exposes no auditable surface
      cannot receive an implicit successful result such as `No capability
      markers found to audit.` The result vocabulary and exit-code behavior for
      `PASS`, `ADVISORY` or `UNVERIFIED`, `NOT_APPLICABLE`, and `FAIL` are
      specified.
- [ ] The note defines how a capability declares its applicability to Lean
      Delivery, Governed SDD, Meridian self-hosting, and supported hosts without
      duplicating canonical policy text or treating template presence as host
      enforcement.
- [ ] The design identifies the minimum repository surfaces that would become
      managed by the self-hosting profile, including whether
      `docs/CONTEXT_BUDGET_POLICY.md`, `.codex/hooks.json`, and supporting hook
      files are installed locally, referenced from a shared source, or excluded
      with rationale.
- [ ] The design specifies bootstrap and upgrade compatibility for existing
      manifests whose `appliedMigrations` include capability migrations that
      were not installed under `lean-delivery`. It does not reinterpret those
      historical entries as proof of current activation.
- [ ] The design defines CI and local verification that prove Meridian is
      dogfooding the declared profile, including at least one negative fixture
      where a declared capability or activation surface is absent and the
      check fails or reports the specified non-success state.
- [ ] The note names bounded implementation follow-up tasks for manifest/schema
      support, audit semantics, managed self-hosting surfaces, and host probes.
      It states their ordering and migration/capability-marker implications but
      does not create or implement them in this task.
- [ ] `git diff --check` passes.

## 📁 Relevant Files

| File | Role |
|------|------|
| `PROJECT_WORKFLOW.md` | Locks Meridian to Lean Delivery and defines its risk boundary. |
| `.meridian/manifest.json` | Currently records migration history and only three managed workflow documents. |
| `scripts/meridian.py` | Defines managed files, capability detection, mode gating, and audit results. |
| `templates/workflows/lean-delivery/` | Current Lean managed surface and candidate shared-capability consumer. |
| `templates/workflows/governed-sdd/` | Current source of capability-marked operational policies. |
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | Existing workflow-neutral and Governed-specific policy clauses to classify. |
| `hooks/queue-briefing.sh` | Existing context-saving capability and candidate self-hosted hook. |
| `hooks/read-guard.sh` | Existing read-boundary capability and candidate self-hosted hook. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Separates template declaration, host activation, and verified enforcement. |
| `migrations/` | Existing capability history and future compatibility mechanism. |
| `tests/test_meridian_cli.py` | Existing audit, migration, capability, and manifest coverage. |
| `docs/MERIDIAN_SELF_HOSTING_PROFILE.md` | New design-note deliverable. |

## 🧩 Technical Context

Meridian currently runs in `lean-delivery` mode. Its manifest records many
capability migrations as applied, including minimal status, bounded queue
reads, execution evidence, and reasoning budgets, while the Lean managed-file
set contains only `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md`, and available
Codex policy files. The repository has no `.codex/hooks.json`, and
`meridian audit --project .` returns success with `No capability markers found
to audit.` because capability detection and protected-region audit are gated to
`governed-sdd`.

The design must make those facts representable without assuming that every
Governed SDD capability belongs in Lean Delivery. A capability can be
workflow-neutral yet host-dependent: for example, queue briefing may be valid
for both lifecycles, while its actual enforcement still depends on hook
installation and host activation. The profile therefore needs separate
declaration, installation, activation, and verification states.

## 🔨 Suggested Approach

1. Classify the existing Governed capability markers into lifecycle-specific,
   workflow-neutral, and host-dependent groups, using only their canonical
   template blocks and host contract.
2. Design the manifest/profile schema and audit state machine, including
   backwards compatibility for historical Lean manifests.
3. Define the smallest self-hosted surface and split its delivery into bounded
   schema, audit, managed-file, and host-evidence follow-ups.

## ⚠️ Constraints and Considerations

- Do not switch Meridian to Governed SDD or introduce Governed-only lifecycle
  states, reviewer roles, owner acceptance, or status-only commits.
- Do not copy every Governed document into the Lean template. Include only
  capabilities with an explicit lifecycle-independent rationale.
- Do not modify the manifest schema, templates, migrations, CLI, hooks, tests,
  or host configuration in this design task.
- Do not claim that a file, marker, migration entry, or execpolicy rule proves
  host activation or enforcement.
- Keep risk-based workflow escalation separate. This task may identify it as a
  follow-up boundary but must not design or implement an automatic mode switch.
- Preserve compatibility for existing Lean and Governed consumers.
- Repository artifacts are English-only.

## Host impact

Classification: NOT_APPLICABLE

Rationale: this task produces a design note only and does not install hooks,
change host policy, alter managed files, or claim new enforcement. The design
must specify the host evidence required by later implementation tasks.

## 🔗 Dependencies

- **Depends on**: 054
- **Blocks**: implementation of the Meridian self-hosting profile and
  non-vacuous cross-mode capability auditing.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/057-design-meridian-self-hosting-profile.md)"$'\n\nExecute this task in the current project.'
```
