# Changelog

All notable changes to Meridian are documented here. Versions before this file
existed are reconstructed from `migrations/*.json` and `VERSION`, which remain
the authoritative, machine-checked source of truth (`scripts/check_repository.py`
verifies the migration sequence is contiguous and ends at `VERSION`). This file
adds human-readable context on top of that record; it does not replace it.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/); version
numbers follow the `frameworkVersion` tracked in generated projects'
`.meridian/manifest.json`, not a separate release cadence.

## [Unreleased]

Framework-CLI improvements to `bin/meridian` for capability-aware adoption.
These change tooling and documentation only — no generated-project managed
file changed, so no migration record or `VERSION` bump applies.

### Added

- `meridian adopt --assisted --check` now computes a single, durable
  `NEXT_ACTION` (`IMPLEMENT_MIGRATION` → `REVIEW_MIGRATION`/`ADDRESS_REVIEW`
  → `FINALIZE`, or `BLOCKED`) from detected capabilities and a
  machine-readable `.meridian/adoption-review.md` header
  (`Verdict:`/`Attempt:`), mapped onto the CLI's existing exit codes so a
  coordinator can drive the whole migration with no memory of its own — see
  [migrations/ASSISTED_ADOPTION.md](migrations/ASSISTED_ADOPTION.md).
- `--mode` and `--from` are auto-detected on `adopt` and `finalize-adoption`
  when unambiguous (mode from the project's `PROJECT_WORKFLOW.md` lock,
  version from the sole packaged baseline), falling back to an explicit
  error naming the flags needed.
- `--emit implementer|reviewer|orchestrator` extracts a single prompt block
  from `adopt --assisted --check`, without parsing the `_BEGIN`/`_END`
  markers, for a host or human that only needs one block.
- `finalize-adoption` now refuses to run unless `.meridian/adoption-review.md`
  records an unconditional `APPROVE` (no unchecked findings) for the current
  attempt, or an explicit `--owner-accepted` override is passed — mirroring
  the existing `Accept <TASK-ID>` owner-acceptance path.
- The two-consecutive-`CHANGES_REQUESTED` retry limit is now enforced by the
  CLI itself (`BLOCKED`), not left to a coordinator's memory of prior turns.
- `.meridian/baselines/<version>/` snapshots older than the manifest's
  current `frameworkVersion` are pruned automatically once `upgrade --apply`
  or `adopt --apply` completes, since only the current version's snapshot is
  ever read again.
- `skills/meridian-governed-sdd-claude-code/SKILL.md` and
  `skills/meridian-governed-sdd/SKILL.md` document how a coordinator dispatches
  the implementer and reviewer roles as genuinely independent sessions (Claude
  Code Task-tool subagents, or separate fresh chats where no subagent tool is
  available) driven by that loop.

## [1.1.0]

### Added

- `bin/meridian` / `scripts/meridian.py`: a portable CLI that locks a
  generated project to its installed Meridian version
  (`.meridian/manifest.json` plus baseline snapshots) and performs a
  three-way merge for framework upgrades (`meridian upgrade --check/--apply`),
  applying nothing when any managed file conflicts.
- `meridian adopt --from <version> [--assisted]` for projects that predate the
  lockfile: a generic three-way merge against a packaged legacy baseline, or
  capability-aware detection of missing framework behavior for a project that
  has intentionally customized its workflow documents.
- `release-baselines/1.0.0/`: the immutable packaged Governed SDD template
  snapshot for Meridian 1.0.0, the merge base for adopting a pre-lockfile
  project.
- Migration `003-framework-updater` (this release).

## [1.0.2]

### Added

- `Run lifecycle <TASK-ID>` autonomous orchestration
  ([docs/LIFECYCLE_ORCHESTRATION.md](templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md)):
  a coordination-only role that starts distinct implementer and
  reviewer-integrator sessions, loops through requested-change remediation via
  the durable review record, and integrates only after approval and all
  repository/forge gates.
- Migration `002-lifecycle-orchestration`.

## [1.0.1]

### Added

- Durable review-remediation record
  (`docs/REVIEW_RECORD_TEMPLATE.md`, `tasks/reviews/<TASK-ID>.md`): on
  `CHANGES_REQUESTED`, the reviewer records prioritized, evidence-backed
  findings and returns the task to `IN_PROGRESS` instead of relying on chat
  output as the handoff. `Address review <TASK-ID>` resolves exactly the
  unchecked findings.
- Migration `001-review-remediation-record`.

## [1.0.0]

Initial packaged Governed SDD workflow: ADRs, dependency-gated atomic tasks,
`REQUIRED`/`NOT_REQUIRED` review policy, reviewer-integrator-led `main`
integration, and the Lean Delivery mode for low-risk work. Snapshotted verbatim
at [release-baselines/1.0.0/](release-baselines/1.0.0/) as the reference point
for adopting projects that predate `.meridian/manifest.json`.
