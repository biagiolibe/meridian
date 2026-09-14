# Task 026 — Roll out routing to Palimpsest and measure initial context

> **ID**: `026`
> **Category**: Integration
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned

## Objective

Upgrade Palimpsest to the compact-routing release and verify that Claude Code
and Codex begin status, tech-design, implementation, and review work without
loading a universal monolith.

## Acceptance Criteria

- [x] Palimpsest upgrades from a clean checkout with no lost customized rule
      and a passing `meridian audit`.
- [x] Its `CLAUDE.md` uses the explicit pointer marker and routes silently,
      mentioning precedence only for a real conflict or blocker.
- [x] Before/after byte measurements for both entry points are recorded.
- [x] One status/question, `Proceed`, and `Review` session demonstrate the
      expected routed reads and preserve all required safeguards.

## Constraints

- Do not overwrite consumer-project changes or use `adopt`.
- Stop on an upgrade conflict and record it for an explicit resolution.

## Validation

- `meridian upgrade --project <palimpsest> --check`
- `meridian audit --project <palimpsest> --mode governed-sdd`
- `git diff --check`

## Dependencies

- **Depends on**: 025
- **Blocks**: none

## Execution record

2026-09-13 — `meridian upgrade --project /Users/biagioliberto/dev/src/palimpsest --check`
reported `CONFLICT AGENTS.md — capability move
038-compact-entry-point-routers source file differs from the installed
baseline`. The plan also identified a safe `APPEND-MARKERS` action for the
explicit-pointer `CLAUDE.md`, but no changes were applied because the
retirement conflict blocks the whole upgrade. Per the task constraint, the
Palimpsest checkout was left unchanged pending an explicit resolution of its
customized `AGENTS.md`.

2026-09-13 — Meridian was corrected before retrying the consumer plan. A
retirement now proves and removes only exact protected source markers, while
preserving unrelated project-owned text; a combined marker-update/retirement
action prevents a router version bump from retaining duplicate procedures;
and legacy Claude pointers receive the explicit pointer marker once AGENTS is
verified or safely planned current. The read-only retry is conflict-free and
plans `APPEND-RETIRE-MARKERS AGENTS.md`, `POINTER-UPGRADE CLAUDE.md`, and the
four new role procedures. It was deliberately not applied to Palimpsest per
developer instruction. Remaining work: explicitly authorize `upgrade --apply`
in the Palimpsest checkout, then collect the required audit and measurements.

2026-09-14 — Palimpsest commit `a76b200` applied the corrected Meridian
1.1.35 upgrade from a clean checkout. The compatibility checkpoint preserved
all customized rules, installed the four role procedures, retained the
explicit `MERIDIAN:CLAUDE-AGENTS-POINTER v1` marker, and changed entry-point
sizes from 31,619 to 21,777 bytes for `AGENTS.md` and from 1,665 to 1,709
bytes for `CLAUDE.md`.

Palimpsest then completed the consumer-specific evolution through accepted
tasks WFLOW-004 (ADR-0054 route map), WFLOW-005 (additive extraction), and
WFLOW-006 (generated-router retirement). The final `AGENTS.md`, `CLAUDE.md`,
and `docs/workflows/ENTRY_ROUTER.md` are byte-identical at 1,448 bytes and
declare the six required routes. Fresh status/design, Proceed, and Review
sessions each loaded the mandatory bootstrap files and exactly one matching
role procedure without preloading the other role procedures. An earlier
review candidate that omitted the bootstrap reads was rejected and replaced.

The consolidated evidence, session details, measurements, and evolution
mapping are recorded in
[`docs/PALIMPSEST_ROUTING_EVOLUTION_EVIDENCE.md`](../../docs/PALIMPSEST_ROUTING_EVOLUTION_EVIDENCE.md).

Final validation on 2026-09-14:

- `bin/meridian upgrade --project /Users/biagioliberto/dev/src/palimpsest --check`
  — exit 0; version 1.1.35 to 1.1.35, all managed files `KEEP`.
- `bin/meridian audit --project /Users/biagioliberto/dev/src/palimpsest --mode governed-sdd`
  — exit 0; all reported checks pass.
- `bin/meridian generate-entry-routers --project /Users/biagioliberto/dev/src/palimpsest --check`
  — exit 0; generated routers match the canonical source.
- `git -C /Users/biagioliberto/dev/src/palimpsest diff --check` — exit 0.
- `python3 scripts/check_repository.py` — exit 0.
- `git diff --check` — exit 0.
