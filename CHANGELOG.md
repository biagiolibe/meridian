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

- `meridian audit --project <path> [--mode ...]`
  ([commands/meridian-audit.md](commands/meridian-audit.md)): a new,
  read-only command. Phase 4 of
  [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md) —
  verifies every `MERIDIAN:BEGIN`/`END` protected region in a project's
  managed files still matches the framework's released text for that exact
  capability version, in that exact file (`PASS`/`FAIL`), and reports a
  project marker version the current template no longer carries as `SKIP`
  (a staleness question for `upgrade`, not a drift question for this
  command) rather than a false failure. Does not yet include the
  originally-proposed `ACCEPTED`-task/review-record consistency check from
  `QUALITY_COMPLIANCE_ROADMAP.md` Tier 2 — that remains a separate addition
  to this same command.
- Phase 3 of [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md):
  `meridian upgrade`/`adopt` now tell a cosmetic merge conflict from a real
  one. When a file's three-way merge conflicts, and that file's *own*
  content already carries a satisfied capability marker for every migration
  that manages it, the conflict downgrades to a new `VERIFIED` plan action
  (file left untouched, does not block the upgrade) instead of a blocking
  `CONFLICT`. The check is scoped to the conflicting file's own text, not
  the whole project — an earlier version of this checked project-wide
  presence and produced a false positive (a `PROJECT_WORKFLOW.md` conflict
  wrongly downgraded because an unrelated capability happened to be
  satisfied elsewhere in the project), caught by the existing conflict
  regression tests before it shipped.
- Phase 2 of [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md):
  `detect_capabilities()` is now version-aware — it reads each migration's
  `capability`/`capabilityVersion` fields and compares against the
  project's `MERIDIAN:BEGIN` marker version, so a future migration that
  *modifies* an existing capability (not just adds a new one) becomes
  detectable, with a distinct message for "no marker at all" versus "marker
  present but below the required version." A legacy fallback
  (`LEGACY_CAPABILITY_EVIDENCE`) keeps every project adopted before markers
  existed (migration 006) correctly detected at v1 via the old phrase
  check — caught by testing this against two real, already-adopted
  projects, which regressed to fully `MISSING` without it.
  `assisted_implementer_prompt` now surfaces a migration's `delta` field
  when present, so a capability version bump is scoped to the actual
  change instead of implying a from-scratch rewrite.
- `meridian upgrade --apply --owner-reconciled`: registers the target
  version and baseline snapshot without touching any managed file, for a
  project too customized for the automatic three-way merge to ever resolve
  cleanly (a permanently conflicting `AGENTS.md`/`CLAUDE.md`, not a one-off
  conflict) whose developer has already reconciled every managed file by
  hand. Mirrors `finalize-adoption --owner-accepted`'s escape-hatch shape.
  `adopt` already had a capability-aware path for a project with no manifest
  yet; `upgrade` had no equivalent for one that is already locked but too
  divergent for line-based merging.

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

## [1.1.7]

### Added

- Migration `010-project-workflow-baseline-capabilities`: backfills capability
  tracking for `PROJECT_WORKFLOW.md` — the single most important managed file,
  since it carries the `GOVERNED_SDD` mode lock itself — which had none until
  now. Wraps its eight independent rule sections
  (`workflow-mode-lock`, `document-precedence`, `task-lifecycle`,
  `execution-assets`, `roles`, `review-policy`, `git-workflow`,
  `execution-discipline`) each in its own `v1` marker, introducing the
  `capabilities` list field to the migration schema alongside the existing
  singular `capability`/`capabilityVersion` fields, so one migration record
  can declare several independent, pre-existing capabilities at once instead
  of needing eight near-duplicate records. Purely additive: no section's
  content changed. Verified live: a fresh vanilla project passes `meridian
  audit` on all 20 marker occurrences across the framework's four
  migrations-with-markers so far.

## [1.1.6]

### Changed

- Migrations `008-review-remediation-record-v2` and
  `009-lifecycle-orchestration-v2`: the canonical text for both capabilities
  stops hardcoding `tasks/reviews/<TASK-ID>.md` inline, referencing a new
  "Canonical locations" declaration in `PROJECT_WORKFLOW.md`'s Execution
  assets section instead (default unchanged). Motivated by Palimpsest: its
  own directory conventions (`docs/tasks/...`) were baked into the literal
  wording of the review-remediation-record and lifecycle-orchestration
  capabilities, so wrapping Palimpsest's actual text in a marker would have
  been a false claim of byte-identical canon. Parameterizing the reference
  lets any project's own declared locations sit outside the protected
  region without changing the canonical text at all.
- **Real consequence, not a bug**: because this changes what "the current
  version" of these two capabilities' canonical text actually is, both
  capabilities require v2 now. The `LEGACY_CAPABILITY_EVIDENCE` fallback
  (added in migration 006/phase 2) only ever proves v1, by design — so a
  project relying on it, including the two real projects adopted so far
  (`fusa`, `palimpsest`), now correctly reports both capabilities `MISSING`
  (stale) rather than falsely `PRESENT`, and needs another assisted-adoption
  pass to reach `1.1.6`. Verified live, read-only, against both.

## [1.1.4]

### Added

- Migration `007-validation-capability-markers`: wraps `validation-scoping`
  (004) and `ci-verified-validation` (005) in the same
  `<!-- MERIDIAN:BEGIN capability=<id> v1 --> / <!-- MERIDIAN:END -->`
  markers migration 006 gave to 001/002 — bringing all four framework
  capabilities shipped so far under version-aware detection, cosmetic-vs-real
  conflict resolution, and `meridian audit` integrity checking. Purely
  additive: detection and verification code are unchanged, only the marker
  text and the `capability`/`capabilityVersion` fields backfilled onto 004
  and 005's own records. Also genericized a Rust-specific example
  (`cargo test/build/clippy`) in the validation-scope rule to a stack-agnostic
  one, and required `extract_marker_block`'s parser to accept a marker sitting
  inline mid-sentence (not just on its own line), since `validation-scoping`'s
  text in `AGENTS.md`/`CLAUDE.md` is one clause inside a larger numbered step,
  not a standalone section like 001/002's.

## [1.1.3]

### Added

- Versioned capability markers (Phase 1 of
  [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md)):
  the review-remediation-record (001) and lifecycle-orchestration (002)
  capability text in `AGENTS.md`, `CLAUDE.md`,
  `docs/REVIEW_RECORD_TEMPLATE.md`, and `docs/LIFECYCLE_ORCHESTRATION.md` is
  now wrapped in `<!-- MERIDIAN:BEGIN capability=<id> v1 -->` /
  `<!-- MERIDIAN:END -->` markers. Purely additive in this migration —
  detection (`detect_capabilities()`) and verification are unchanged; the
  markers exist so later phases can compare a required capability version
  against what a project actually has, and tell a cosmetic merge conflict
  (the project already has the rule, worded its own way) from a real gap,
  instead of the phrase-only detection that failed to recognize a real,
  pre-token governed-SDD project twice this session.
- Migration `006-capability-markers`.

## [1.1.2]

### Added

- CI-first validation-evidence rule
  ([docs/PULL_REQUEST_POLICY.md](templates/workflows/governed-sdd/docs/PULL_REQUEST_POLICY.md)):
  a reviewer with a completed CI run for the exact task-branch commit that
  covers the task's validation surface uses that run as evidence instead of
  re-running the same checks locally — a real independent, tamper-evident
  source, unlike the implementer's own self-report. Without such a run, the
  reviewer performs its own validation scoped to the diff per
  `docs/CONTEXT_BUDGET_POLICY.md`, rather than trusting a bare "tests
  passed" claim or duplicating the implementer's full run wholesale.
- `docs/COMPLETION_REPORT_TEMPLATE.md`'s `Validation` field now requires the
  exact commands and exit status, or the CI check run, instead of a bare
  pass/fail assertion — evidence has to be falsifiable to be evidence.
- Migration `005-ci-verified-validation`.

## [1.1.1]

### Added

- Validation-scope rule
  ([docs/CONTEXT_BUDGET_POLICY.md](templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md)):
  before running validation, classify the diff by surface
  (documentation/policy text vs. source/build) and run only the commands
  whose surface the diff actually touches. A documentation/policy-only change
  now explicitly skips the project's full build/test/lint suite and states so
  in the report, instead of running it defensively. A reviewer verifies the
  same scoping and flags disproportionate or missing validation as a finding.
  This closes a real, measured gap: a 7-file documentation-only migration to
  another project burned roughly 200K tokens across two review sessions,
  almost entirely from a full `cargo build`/`test`/`clippy` run that had
  nothing to validate.
- `meridian adopt --assisted`'s implementer and reviewer prompts now state the
  same scoping explicitly, since every framework-managed file is
  documentation/policy text by construction.
- Migration `004-validation-scoping`.

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
