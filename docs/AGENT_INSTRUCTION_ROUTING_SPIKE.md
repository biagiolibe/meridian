# Agent Instruction Routing Spike

## Question

Can Meridian avoid loading a large, universal `AGENTS.md` before a session
knows whether it will implement, review, report status, or answer a project
question, without weakening workflow safety or breaking managed upgrades?

## Measurements

| Entry point | Bytes |
|---|---:|
| Governed-SDD template `AGENTS.md` | 15,223 |
| Governed-SDD template `CLAUDE.md` | 14,872 |
| Governed-SDD template `PROJECT_WORKFLOW.md` | 11,209 |
| Palimpsest `AGENTS.md` | 31,619 |
| Palimpsest `CLAUDE.md` | 1,665 |
| Palimpsest `PROJECT_WORKFLOW.md` | 18,292 |

The template `AGENTS.md` carries eleven capability-marker blocks. Its role
procedures, not merely project invariants, are therefore paid before the
request type is known. Palimpsest's thin Claude pointer then instructs Claude
Code to read its 31.6 KB `AGENTS.md`, recreating the same unconditional cost.

## Recommended architecture

Keep a compact, always-loaded bootstrap contract in each host entry point.
Its only responsibilities are language, mode lock, explicit-task requirement,
Git safety floor, and routing. It must fit within a fixed byte budget and must
not reproduce a role procedure.

Move operational procedures to managed, on-demand documents:

| Request | On-demand source |
|---|---|
| `Proceed with <TASK-ID>` | `docs/workflows/IMPLEMENTATION.md` |
| `Review <TASK-ID>` | `docs/workflows/REVIEW.md` |
| `Address review <TASK-ID>` | `docs/workflows/REMEDIATION.md` |
| `Run lifecycle <TASK-ID>` | `docs/workflows/LIFECYCLE.md` |
| Status or project question | `docs/CONTEXT_BUDGET_POLICY.md`'s minimal profile |

`CLAUDE.md` should use the explicit
`MERIDIAN:CLAUDE-AGENTS-POINTER v1` marker only when it delegates to the same
compact bootstrap contract. It must not require a full `AGENTS.md` read for a
status or question. A host that auto-loads `AGENTS.md` receives the compact
router; a host that auto-loads `CLAUDE.md` receives an equivalent compact
router.

## Migration constraints

The router cannot simply paraphrase existing rules. The current audit records
capability-marker content per managed file, and upgrades must reject locally
modified protected text rather than discarding it. The migration therefore
needs an additive-then-retiring sequence:

1. Add the four managed role documents and copy each exact marker block to its
   new canonical role home. Add routing links to the entry points, but retain
   the old blocks for one compatibility release.
2. Extend upgrade planning and audit to recognize a declared capability move:
   a move succeeds only when the old and new protected blocks are byte-identical
   to their respective released baselines. A locally edited old block must
   produce a conflict and preserve the project text for a deliberate migration.
3. In a later migration, retire the old entry-point copies with declared
   `removes`/`supersededBy` metadata, leaving the compact bootstrap contract.
   Do not delete a block in the same release that first introduces its new
   home.

This keeps one release in which every old project can be upgraded safely, then
removes the duplicate only once the migration engine can prove where the rule
went.

## Proposed implementation tasks

1. Define the bootstrap byte budget, exact invariant set, role-document map,
   and capability-location migration schema.
2. Implement additive role documents and upgrade/audit support for declared
   moves; test vanilla, locally customized, and explicit Claude-pointer
   projects.
3. Convert `AGENTS.md` and `CLAUDE.md` to compact routers and retire duplicate
   blocks in a separate migration.
4. Upgrade Palimpsest in a clean checkout; measure entry-point bytes and run a
   real `Proceed`, `Review`, status, and tech-design-alignment session.

## Success and rollback

Success requires a compact bootstrap entry point, no weakened capability audit,
conflict-safe preservation of locally changed rules, and measured reduction in
initial instruction bytes for both Codex and Claude Code.

If a project cannot upgrade without losing a customized rule, stop at the
additive release. The new documents remain available, and the legacy copies
remain authoritative until the conflict is resolved; no destructive rollback is
needed.
