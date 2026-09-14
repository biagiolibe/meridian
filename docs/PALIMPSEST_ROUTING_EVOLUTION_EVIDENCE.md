# Palimpsest Routing Evolution Evidence

Date: 2026-09-14

## Purpose

This report consolidates the durable evidence for Meridian tasks 026, 029,
and 030. It records how Palimpsest moved from a customized universal agent
entry point, through a conflict-safe compatibility upgrade and additive rule
extraction, to byte-identical generated entry routers with role-specific
loading.

This report closes the evidence gap for task 026. It also demonstrates that
the consumer-side outcomes requested by tasks 029 and 030 exist in
Palimpsest. Their Meridian queue states remain unchanged until those tasks
are explicitly assigned for closure.

## Evolution summary

### Compatibility rollout — Meridian task 026

The first Palimpsest upgrade check detected that its customized `AGENTS.md`
did not match the installed baseline for capability retirement. Meridian
stopped without applying a partial upgrade. The framework was then corrected
so retirement removes only exact protected source markers, preserves
unrelated project-owned text, combines marker update and retirement safely,
and upgrades the legacy Claude pointer only after the AGENTS route is proven.

Palimpsest commit `a76b200` (`meridian upgrade 1.1.35`) applied the corrected
upgrade. The commit installed the four role procedures, recorded migrations
`037-additive-role-procedures` and `038-compact-entry-point-routers`, and
retained all project-owned rules. At that compatibility checkpoint:

| Entry point | Before upgrade | After upgrade |
|---|---:|---:|
| `AGENTS.md` | 31,619 bytes | 21,777 bytes |
| `CLAUDE.md` | 1,665 bytes | 1,709 bytes |

The post-upgrade `CLAUDE.md` contained the explicit
`MERIDIAN:CLAUDE-AGENTS-POINTER v1` marker. This was the required compatibility
state, not the final consumer-router architecture.

### Consumer mapping and additive extraction — Meridian task 029

Palimpsest decomposed this work into two governed tasks:

- `WFLOW-004` created accepted ADR-0054 and mapped every existing entry-point
  section to the router, status/design, implementation, review, remediation,
  lifecycle, or historical architecture evidence. Its second review attempt
  was approved after the compatibility-baseline section was added to the map.
- `WFLOW-005` performed Release A. It copied the mapped rules into
  `docs/workflows/STATUS_DESIGN.md`, `IMPLEMENTATION.md`, `REVIEW.md`,
  `REMEDIATION.md`, and `LIFECYCLE.md`, while retaining the entry-point
  copies. Its review was approved and the governed audit passed.

Both tasks are `ACCEPTED`, and their acceptance commits are ancestors of the
current Palimpsest checkout.

### Generated router and retirement — Meridian task 030

Palimpsest task `WFLOW-006` performed Release R. It created
`docs/workflows/ENTRY_ROUTER.md` and `ENTRY_ROUTER_MAP.json`, generated both
host entry points, and retired only copies proven by the accepted additive
release. The task and its independent review are `ACCEPTED`.

The final measurements are:

| Artifact | Final size | SHA-256 relationship |
|---|---:|---|
| `docs/workflows/ENTRY_ROUTER.md` | 1,448 bytes | canonical source |
| `AGENTS.md` | 1,448 bytes | byte-identical to source |
| `CLAUDE.md` | 1,448 bytes | byte-identical to source |

All three files have SHA-256
`a86a876e09e2f49dcc3ac127a0e7b8c1797d10de71a3c86f0a155f30908b2221`.
The route map declares exactly the six required routes: status/design,
implementation, review, remediation, lifecycle/acceptance, and audit. The
final configuration contains no Claude-to-AGENTS pointer because ADR-0054
defines that pointer as a migration input rather than the target architecture.

## Task 026 routed-session evidence

The following evidence was extracted from fresh Palimpsest session
transcripts. A procedure name listed by a directory command without reading
its content was not treated as preloaded context.

### Status/design route — PASS

- Initial request: a read-only project status and tech-design alignment.
- Auto-loaded project entry point: `CLAUDE.md`.
- Mandatory bootstrap reads: `PROJECT_WORKFLOW.md` and `LANGUAGE_POLICY.md`.
- Sole initial role procedure: `docs/workflows/STATUS_DESIGN.md`.
- Other role procedures preloaded: none.
- Later reads were limited to `docs/TASK_QUEUE.md` and read-only Git state
  needed for the requested status report.

### Proceed route — PASS

- Trigger: `proceed with M23-CMD-001`.
- Starting state: clean `main` at `db2bf01`.
- Auto-loaded project entry point: `CLAUDE.md`, confirmed by the session's
  initial system-reminder content.
- Mandatory bootstrap reads: `PROJECT_WORKFLOW.md` and `LANGUAGE_POLICY.md`.
- Sole initial role procedure: `docs/workflows/IMPLEMENTATION.md`.
- Other role procedures preloaded or read during the task: none.
- Later reads were the assigned task, its cited specification and code-
  organization authority, its direct dependency row, relevant source, and
  the completion-report template.

### Review route — PASS

- Trigger: `Review M23-CMD-001`.
- Starting state: clean `m23-cmd-001` at implementation commit `509995f`.
- Auto-loaded project entry point: project `CLAUDE.md`; the host also supplied
  its global user instructions, which did not replace local authority.
- Mandatory bootstrap reads: `PROJECT_WORKFLOW.md` and `LANGUAGE_POLICY.md`.
- Sole initial role procedure: `docs/workflows/REVIEW.md`.
- Other role procedures preloaded or read during review: none. A directory
  listing exposed filenames only and did not load their contents.
- Later reads were the assigned task, its queue state, cited specification,
  handoff, execution evidence, review-record template, relevant source diff,
  and Git ancestry evidence.

An earlier review-session candidate correctly selected `REVIEW.md` but did
not read the mandatory local workflow and language policies first. It was
classified as insufficient and was not used as task 026 evidence.

## Current verification

The task 026 validation was repeated against the current Palimpsest checkout
after the routed-session evidence was collected:

- `meridian upgrade --project /Users/biagioliberto/dev/src/palimpsest --check`
  — exit 0; `1.1.35 -> 1.1.35`, all managed files `KEEP`.
- `meridian audit --project /Users/biagioliberto/dev/src/palimpsest --mode governed-sdd`
  — exit 0; all reported capability checks pass.
- `meridian generate-entry-routers --project /Users/biagioliberto/dev/src/palimpsest --check`
  — exit 0; generated entry routers match their canonical source.
- `git -C /Users/biagioliberto/dev/src/palimpsest diff --check` — exit 0.

The current Palimpsest checkout is clean on `main`. The accepted WFLOW-004,
WFLOW-005, and WFLOW-006 commits are all ancestors of the current checkout.

## Result

Task 026's compatibility upgrade, pointer state, measurements, routed-session
proof, and safety checks now have explicit evidence. Tasks 029 and 030 have
also been realized in Palimpsest through accepted governed tasks, culminating
in a smaller and symmetric initial context for Claude Code and Codex without
loss of project-owned workflow or domain safeguards.
