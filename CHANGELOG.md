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

## [1.1.17]

### Added

- Migration `020-reasoning-budget-contract`: makes a task's `Reasoning`
  declaration an exact permitted worker-runtime cap rather than a minimum or
  a suggestion. It adds `low` for focused mechanical work, requires a written
  rationale for `high`, and requires explicit developer authorization for
  `xhigh`. Implementers and reviewers must use a fresh session configured at
  the declared value; a mismatch or an unconfirmable setting blocks before
  substantive work, and agents may never escalate effort automatically.
  Lifecycle coordinators retain the lowest available effort because they only
  inspect durable state and delegate substantive work.

## [1.1.16]

### Fixed

- Migration `019-marker-aware-capability-insertion`: framework upgrade now
  handles the safe case where a project moved intact protected marker blocks
  and a newer template adds a new protected capability. Rather than reporting
  a line-based merge conflict, it appends the new byte-identical block without
  changing project text. Altered or missing inherited protected blocks remain
  blocking conflicts.

## [1.1.15]

### Added

- Migration `018-execution-evidence-profile`: adds the
  `execution-evidence-profile` capability to Governed SDD. It separates
  stack-agnostic evidence discipline from project-specific commands: the
  protected context policy requires concise successful output, progressive
  diagnostics, complete per-hunk diff review, planned manual evidence, and no
  duplicate session context, while the new project-owned
  `docs/EXECUTION_EVIDENCE_PROFILE.md` records the actual commands, logs,
  capture channels, and runtime settings. Required validation, independent
  review, and manual acceptance evidence are unchanged.

## [1.1.14]

### Added

- Migration `017-manual-verification-precondition-and-record`: adds
  `manual-verification-precondition` and `manual-verification-record` to
  Governed SDD. Caught in real use: a task requiring manual/visual proof
  passed every automated check and only then discovered, mid-implementation,
  that the evidence itself was unavailable — forcing a wasted resumption
  session to finish what a precondition check would have caught for free.
  `manual-verification-precondition` (step 1 of `AGENTS.md`/`CLAUDE.md`'s
  Implementation workflow) makes the implementer confirm evidence
  availability *before* writing any code when the task declares `Manual
  verification: required`, returning `BLOCKED` immediately instead of
  discovering the gap later, and prefers a deterministic test as primary
  acceptance evidence over a GUI check when one exists (e.g. a geometry or
  layout assertion). `manual-verification-record` gives
  `docs/COMPLETION_REPORT_TEMPLATE.md` and `docs/REVIEW_RECORD_TEMPLATE.md` a
  dedicated field — a named screenshot, the view checked, and the result —
  so a reviewer can use it without reconstructing the session; the review
  record's own marker sits outside `review-remediation-record`'s existing
  marker to avoid the documented nesting limitation.

## [1.1.13]

### Added

- Migration `016-task-blueprint-manual-verification-v2`: bumps
  `task-blueprint` to `capabilityVersion: 2`, adding a `Manual verification:
  [none / required]` field immediately after `Review` — the declaration
  migration 017's precondition and record capabilities key off.

## [1.1.12]

### Added

- Migration `015-role-scoped-agent-rules`: adds the `role-scoped-agent-rules`
  capability to Governed SDD. `AGENTS.md`/`CLAUDE.md` states rules for every
  role in one file; this scopes how much of it a session actually needs to
  read. Every role reads a shared core (introductory rules through "Command
  triggers", plus "Owner-acceptance workflow"); an implementer additionally
  reads the implementation-side sections, a reviewer-integrator the
  review-side sections, and the orchestrator does not read the file at all
  beyond confirming its own trigger phrases (already true per this policy's
  existing "Lifecycle orchestration" section). Sections are matched by
  heading text with an explicit fallback to reading the whole file when a
  heading is missing or the mapping is unclear — this narrows a known-safe
  read, it does not license skipping unfamiliar content.

  This is the cheaper alternative to physically splitting `AGENTS.md`/
  `CLAUDE.md` by role, which was evaluated and set aside: relocating an
  existing capability marker to a new file would require a migration
  category the framework doesn't have yet (previous migrations only ever
  add or version a capability, never move it between files) and would orphan
  the operative prose a customized project has already written next to that
  marker in its current location (Palimpsest and fusa both did this in
  their retrofit onto capability markers). A prompt-level reading rule gets
  most of the same benefit — implementer and reviewer sessions each skip
  roughly a quarter to a third of the file — with no migration risk and no
  retrofit cost on already-adopted projects. Physical splitting stays a
  future option once enough adopting projects exist to justify a one-time
  relocation migration.

## [1.1.11]

### Added

- Migration `014-minimal-read-only-status`: adds the
  `minimal-read-only-status` capability to Governed SDD. It distinguishes a
  lightweight read-only project-status report from a conformance audit,
  constraining the default reads to workflow mode, non-terminal queue state,
  direct dependency readiness, and Git state. Expanded reads require a stated
  evidence gap. The governed-SDD operator prompt and Codex/Claude Code skills
  now route explicit status requests through this profile.

- Fixed a bug in the Phase 3 cosmetic-vs-real conflict check (`upgrade`/
  `adopt`): the set of capabilities a conflicting file had to satisfy to be
  downgraded to `VERIFIED` was derived from each migration's `managedPaths`
  — every file that migration's diff *touches* — rather than from which
  capability markers the file's own template actually *carries*. A
  migration can mention a capability in several files' prose while marking
  it in only one (`migrations/011-whole-file-baseline-capabilities.json`
  pairs four capabilities with four different single-purpose files via
  parallel arrays); the old code required all four in every one of the
  four files, so none of them could ever verify. `capability_ids_for_file`
  is replaced by `capability_ids_in_template`, which reads the marker ids
  directly out of the framework's own template for that file — the same
  ground truth `audit` already uses. The satisfied-check itself is also
  tightened from "marker version present" to a byte-exact comparison of
  the local marker's content against the template's, closing a gap where a
  version-tagged marker with corrupted inner text was wrongly accepted.
  Caught while retrofitting a real, heavily customized project (Palimpsest)
  onto capability markers: `meridian audit` passed all 31 markers while
  `meridian upgrade --check` still reported 5 files as blocking `CONFLICT`s
  — a contradiction between the two commands that shouldn't be possible
  since they check the same protected regions.
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

## [1.1.10]

### Fixed

- Migration `013-language-policy-v2`: the `language-policy` marker (migration
  011) wrongly included the per-project `**Conversation language:**
  `[Conversation language]`` declaration inside its protected region.
  `commands/meridian-init.md` step 9 replaces that placeholder with the
  project's actual chosen language during initialization — so every real,
  correctly initialized project would have diverged from canon on that exact
  line and failed `meridian audit` on day one, not just Palimpsest. Caught
  before shipping anywhere, while working out the Palimpsest retrofit.
  Verified live: a project with the placeholder replaced (exactly what
  `/meridian-init` produces) now passes.

## [1.1.9]

### Added

- Migration `012-agents-claude-residual-capabilities`: backfills capability
  tracking for `AGENTS.md`/`CLAUDE.md`'s remaining independently-changeable
  sections — `command-triggers`, `review-mode-boundary`,
  `owner-acceptance-workflow`, `implementer-reviewer-handoff`,
  `reviewer-integrator-identity` — each at `v1`. `review-mode-boundary` is
  introduced already path-parameterized (referencing `PROJECT_WORKFLOW.md`'s
  canonical locations instead of a hardcoded `tasks/reviews/<TASK-ID>.md`),
  since a brand-new capability has no reason to ship with a defect a later
  migration would just have to fix again. `### Implementation workflow`'s
  steps 1-4 and 6-8 remain untracked: the marker grammar has no nesting, and
  step 5 already carries `validation-scoping`'s marker inside that same
  numbered section. This closes out the marker-retrofit sweep of every
  managed governed-SDD file except the two intentionally excluded ones
  (`docs/ARCHITECTURE_DECISIONS.md`, a project-owned scaffold, and
  `docs/OPERATOR_PROMPTS.md`, an explicitly non-normative cookbook).
  Verified live: a fresh vanilla project passes `meridian audit` on all 34
  marker occurrences.

## [1.1.8]

### Added

- Migration `011-whole-file-baseline-capabilities`: backfills capability
  tracking for the four remaining single-purpose managed files that had
  none — `LANGUAGE_POLICY.md`, `tasks/TASK_BLUEPRINT.md`,
  `docs/CODE_ORGANIZATION.md`, `docs/AUDIT_PROMPT_READ_ONLY.md` — each
  wrapped whole in one `v1` marker. Purely additive. Verified live: a fresh
  vanilla project passes `meridian audit` on all 24 marker occurrences
  across every migration with markers so far.

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
