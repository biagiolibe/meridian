# Task Execution Queue — Archive

Closed phases and sections moved out of `tasks/QUEUE.md` once every row in them is
`[x]`, to keep that file's reading cost low. Mirrors `QUEUE.md`'s own table
structure.

Authority for this queue: [docs/AUDIT_TOKEN_EFFICIENCY.md](../docs/AUDIT_TOKEN_EFFICIENCY.md)
(evidence) and [docs/PLAN_TOKEN_EFFICIENCY.md](../docs/PLAN_TOKEN_EFFICIENCY.md)
(rationale and sequencing).

## Priorities

| Code | Meaning |
|------|---------|
| 🔴 P1 | Blocking / Critical |
| 🟡 P2 | Important feature |
| 🟢 P3 | Optimization / Polish |

### Phase 43 — Agent-sandbox test reliability

Stops the full test suite from failing in the Codex sandbox because the macOS
AppleScript compiler cannot resolve the iTerm2 scripting dictionary there.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 099 | Skip the AppleScript compile test when `osacompile` cannot run | 🔴 P1 | 086 | [099](done/099-skip-applescript-compile-test-when-osacompile-unusable.md) |

### Phase 1 — Cost reduction (~2–3 days)

`001` and `002` are ~2h each and land the same day. `006` is the item that matters:
phases 1–2 of the plan reduce the *size* of each iteration, but only `006` reduces
their *number*, which is the quadratic term.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 001 | Output bounds belong in the command string | 🔴 P1 | — | [001](done/001-output-bounds-in-command.md) |
| `[x]` | 002 | Ship default numeric budgets, not empty brackets | 🔴 P1 | — | [002](done/002-default-numeric-budgets.md) |
| `[x]` | 006 | Budget state, CLI, and hook echo | 🔴 P1 | 002 | [006](done/006-budget-cli-and-hook.md) |

### Phase 2 — Correctness and drift (~1 day)

Little token value on their own; each fixes a rule that does not currently reach the
session meant to obey it. Zero risk, and nothing depends on them.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 003 | Close the probe / escape-hatch composition | 🔴 P1 | — | [003](done/003-probe-escape-hatch.md) |
| `[x]` | 004 | Generate `CLAUDE.md` from `AGENTS.md` | 🔴 P1 | — | [004](done/004-generate-claude-md.md) |
| `[x]` | 005 | Stop instructing sessions to read both files | 🟡 P2 | 004 | [005](done/005-prompts-read-one-file.md) |

### Phase 2b — Found in the field

Not planned from the audit: surfaced while reconciling Palimpsest onto 1.1.19.
Ahead of phase 3 because every adopted project that receives an inline
capability version bump silently accumulates a contradictory pair.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 012 | `append_only_new_markers` treats a version bump as a new capability | 🔴 P1 | — | [012](done/012-marker-supersession.md) |

### Phase 3 — The cause

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 010 | A `SPIKE` task class | 🟡 P2 | — | [010](done/010-spike-task-class.md) |

### Phase 3b — Route work away from manual evidence

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 014 | The `CLAUDE.md` generator altered protected marker content | 🔴 P1 | — | [014](done/014-generator-altered-protected-blocks.md) |
| `[x]` | 013 | Evidence tiers and a routing rule for `Manual verification` | 🔴 P1 | — | [013](done/013-evidence-tiers-and-routing.md) |

`013` shipped together with `011` (Phase 4), per `011`'s bundling constraint,
both in migration `024-evidence-tiers-and-routing` (VERSION `1.1.21`).

### Phase 4 — Stop the ratchet

Buys no tokens directly. It is what keeps phases 1–3 from being undone by the next
few upgrades.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 011 | Warn about the head/SIGPIPE/pipefail trap in the template | 🟡 P2 | — | [011](done/011-sigpipe-trap-in-template.md) |
| `[x]` | 007 | A retirement path for capabilities | 🟡 P2 | — | [007](done/007-capability-retirement-path.md) |
| `[x]` | 008 | Retire `role-scoped-agent-rules` | 🟢 P3 | 004, 007 | [008](done/008-retire-role-scoped-rules.md) |
| `[x]` | 009 | Bound the queue read | 🟡 P2 | — | [009](done/009-bound-the-queue-read.md) |

`011` shipped bundled with `013` (Phase 3b), per its own bundling constraint —
listed here too since it is formally a Phase 4 item.

### Phase 5 — SemVer version split

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|------------|-----------|
| `[x]` | 015 | Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner | 🔴 P1 | 054 | [015](done/015-split-workflow-baseline-version.md) |

Phase 5 remains active; its open tasks stay in `tasks/QUEUE.md`.

### Phase 6 — Agent instruction routing

The framework first made protected capability moves conflict-safe and compacted
its generic entry points. The phase closed only after Palimpsest applied the
release, preserved its customized rules, and supplied measured routed-session
evidence for status/design, implementation, and review.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 023 | Define capability-move and bootstrap-router contract | 🔴 P1 | — | [023](done/023-capability-move-router-contract.md) |
| `[x]` | 024 | Add managed role procedures and move-aware upgrade support | 🔴 P1 | 023 | [024](done/024-additive-role-procedures.md) |
| `[x]` | 025 | Compact entry points and retire duplicate role procedures | 🔴 P1 | 024 | [025](done/025-compact-entry-points.md) |
| `[x]` | 026 | Roll out routing to Palimpsest and measure initial context | 🟡 P2 | 025 | [026](done/026-palimpsest-routing-rollout.md) |

### Phase 7 — Shared consumer entry routers

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 027 | Add generated shared entry-router support | 🔴 P1 | 025 | [027](done/027-generated-entry-router-support.md) |
| `[x]` | 028 | Add routed-read fixtures and adoption audit | 🟡 P2 | 027 | [028](done/028-router-route-fixtures-and-audit.md) |
| `[x]` | 029 | Map and additively extract Palimpsest router procedures | 🟡 P2 | 026, 028 | [029](done/029-palimpsest-router-additive-extraction.md) |
| `[x]` | 030 | Generate compact Palimpsest entry routers and retire copies | 🟡 P2 | 029 | [030](done/030-palimpsest-generated-router-retirement.md) |
| `[x]` | 031 | Publish the consumer router-adoption playbook | 🟢 P3 | 030 | [031](done/031-consumer-router-adoption-playbook.md) |

### Phase 8 — Language-policy salience

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 032 | Add Claude language-policy briefing adapter | 🟡 P2 | — | [032](done/032-language-policy-briefing-adapter.md) |

### Phase 9 — Budget-state integrity

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 033 | `budget_spend()` durably consumes budget before the cap check can reject it | 🔴 P1 | — | [033](done/033-budget-spend-write-before-check.md) |

### Phase 10 — Context-enforcement second pass

Authority: [docs/PROPOSAL_CONTEXT_ENFORCEMENT.md](../docs/PROPOSAL_CONTEXT_ENFORCEMENT.md)
(§3, M1/M2 — highest-yield items of the proposal; independent of each other).

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 034 | Add `meridian adr show` and `meridian context authority` | 🟡 P2 | — | [034](done/034-authority-excerpt-command.md) |
| `[x]` | 035 | `PreToolUse` guard against unranged large-file reads | 🟡 P2 | — | [035](done/035-pretooluse-read-guard.md) |

### Phase 11 — Long-lag consumer upgrade safety

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 036 | Plan capability moves correctly across long-lag consumer upgrades | 🔴 P1 | — | [036](done/036-long-lag-capability-move-upgrades.md) |
| `[x]` | 037 | Let a long-lag consumer stop an upgrade before retirement | 🔴 P1 | 036 | [037](done/037-stop-before-retirement-upgrade.md) |

### Phase 12 — Budget cap semantics

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 038 | Make a budget cap admit exactly `cap` uses | 🟡 P2 | — | [038](done/038-budget-cap-boundary-allows-cap-uses.md) |

### Phase 13 — Optional structured task identity

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|------------|-----------|
| `[x]` | 039 | Design an opt-in structured task-identity policy | 🔴 P1 | 054 | [039](done/039-design-opt-in-task-identity-policy.md) |

### Phase 14 — Codex execution-policy support

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 040 | Ship Codex command-approval rules as a managed governed-SDD template file | 🟡 P2 | — | [040](done/040-codex-command-approval-rules-template.md) |
| `[x]` | 041 | Codex `PreToolUse` read guard, gated by an empirical probe | 🟡 P2 | 040 | [041](done/041-codex-read-guard-hook.md) |
| `[x]` | 042 | Deny over-budget absolute reads outside the project root | 🟡 P2 | 041 | [042](done/042-codex-external-read-guard-paths.md) |

### Phase 15 — Host-impact governance

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 043 | Design the host-impact task contract and completion gate | 🔴 P1 | — | [043](done/043-design-host-impact-gate.md) |
| `[x]` | 044 | Distribute the governed-SDD host-impact task declaration | 🔴 P1 | 043 | [044](done/044-distribute-host-impact-declaration.md) |
| `[x]` | 045 | Enforce host-impact declarations at lifecycle gates | 🔴 P1 | 044 | [045](done/045-enforce-host-impact-lifecycle-gates.md) |

### Phase 17 — Per-task worktree isolation

This phase establishes a dedicated linked worktree as the mandatory execution
boundary for every Lean Delivery and Governed SDD task, with serialized,
non-rewriting final integration.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|-----------|-----------|
| `[x]` | 051 | Enforce isolated worktrees for every task | 🔴 P1 | — | [051](done/051-enforce-isolated-task-worktrees.md) |

### Phase 20 — Host-neutral bounded worktree lifecycle commands

Replaces approval-prone raw Git worktree and integration mutations with
validated, agent-agnostic Meridian state transitions. Codex may grant exact
allow rules for those commands, while Claude and direct terminal users invoke
the same lifecycle surface through their own host permission mechanisms.

| Status | ID | Title | Priority | Depends on | Task File |
|--------|----|-------|----------|------------|-----------|
| `[x]` | 056 | Add bounded worktree lifecycle commands | 🔴 P1 | 054, 055, 059, 063 | [056](done/056-add-bounded-worktree-lifecycle-commands.md) |

### Phase 21 — Meridian self-hosting profile

Separates workflow lifecycle from workflow-neutral operational capabilities so
Meridian can retain Lean Delivery while consuming and verifying the safeguards
it distributes to consumer projects.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 057 | Design the Meridian self-hosting capability profile | 🔴 P1 | 054 | [057](done/057-design-meridian-self-hosting-profile.md) |
| `[x]` | 058 | Add self-hosting manifest and capability-catalog support | 🔴 P1 | 057, 048 | [058](done/058-add-self-hosting-manifest-and-capability-catalog.md) |
| `[x]` | 059 | Implement cross-mode capability audit semantics | 🔴 P1 | 058 | [059](done/059-implement-cross-mode-capability-audit.md) |
| `[x]` | 060 | Install Meridian self-hosting capability surfaces | 🔴 P1 | 059, 056, 052 | [060](done/060-install-meridian-self-hosting-surfaces.md) |
| `[x]` | 061 | Add self-hosting host probes and CI dogfooding gate | 🔴 P1 | 060, 047 | [061](done/061-add-self-hosting-host-probes-and-ci-gate.md) |

### Phase 5 — SemVer version split

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 016 | Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption` | 🔴 P1 | 015 | [016](done/016-adopt-workflow-baseline-version.md) |
| `[x]` | 017 | Relax `check_migrations()`'s VERSION equality to `<=` | 🔴 P1 | 015 | [017](done/017-relax-check-migrations-version-gate.md) |
| `[x]` | 018 | Persist-time SemVer guard for prerelease `frameworkVersion` | 🟡 P2 | 015 | [018](done/018-prerelease-version-guard.md) |
| `[x]` | 019 | `releases/<version>.json` immutable release ledger + `check_releases()` | 🟡 P2 | 017 | [019](done/019-releases-ledger.md) |
| `[x]` | 020 | Update docs for the version split | 🟢 P3 | 015, 017, 019 | [020](done/020-docs-version-split.md) |
| `[x]` | 021 | Ship the first CLI-only release as end-to-end proof | 🟢 P3 | 016, 018, 019, 020, 046 | [021](done/021-first-cli-only-release.md) |

### Phase 22 — Codex configuration resilience

Keeps Meridian's least-privilege task-worktree permission profile recoverable
when Codex app updates or settings rewrites preserve effective TOML semantics
but normalize or remove Meridian's ownership comments.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 062 | Make Codex permission-profile repair resilient | 🟡 P2 | 054 | [062](done/062-make-codex-profile-repair-resilient.md) |

### Phase 17 — Consumer workflow integrity

Fixes found while repairing a consumer's generated entry routers: the upgrade
planner merges templates into generated `AGENTS.md`/`CLAUDE.md`, and tracked
records carry machine-specific absolute paths.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 052 | Make the upgrade planner aware of generated entry routers | 🔴 P1 | 015 | [052](done/052-router-aware-upgrade-planner.md) |
| `[x]` | 053 | Remove machine-specific absolute paths from tracked records | 🟡 P2 | 054 | [053](done/053-remove-machine-specific-absolute-paths.md) |

### Phase 25 — Local project console

Provides an interactive, read-only terminal view of the current project's
queue, task descriptions, dependencies, and local Git state.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 070 | Build a read-only project console with automatic local refresh | 🟡 P2 | 063 | [070](done/070-build-project-console.md) |

### Phase 26 — Project console presentation

Align the local console with the approved compact shell design while keeping
its project-state sources local.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 071 | Apply the compact dark shell design to the project console | 🟡 P2 | 070 | [071](done/071-apply-compact-console-design.md) |
| `[x]` | 072 | Match the approved console mockup in the terminal renderer | 🟡 P2 | 071 | [072](done/072-match-console-mockup.md) |
| `[x]` | 073 | Make directives copyable and restore All filter navigation | 🟡 P2 | 072 | [073](done/073-copy-directive-and-filter-navigation.md) |

### Phase 27 — Project console background refinement

Let the interactive console use the terminal's own background.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 074 | Use the terminal background in the project console | 🟢 P3 | 073 | [074](done/074-match-console-background-color.md) |

### Phase 28 — Project console distribution

Expose the read-only project console through the distributed Meridian CLI and
document how adopters use it from any Meridian project.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 075 | Distribute the project console through the Meridian CLI | 🟡 P2 | 074, 065 | [075](done/075-distribute-project-console-cli.md) |

### Phase 31 — Console agent launch in a split pane

Replaces the iTerm2 tab launched by the console with a horizontal split pane of
the console's own session, so the console stays visible beside the agent.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 086 | Launch console agents in a horizontal iTerm2 split pane | 🟡 P2 | 077 | [086](done/086-console-launch-agent-in-iterm2-split-pane.md) |

### Phase 32 — Console review launch for task-record review policy

Makes the console offer the permitted `Review` directive when a Governed SDD
project declares the review policy in the task record instead of a queue
column, and explains why a directive is withheld.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 087 | Read the review policy from the task record in the console | 🟡 P2 | 077 | [087](done/087-console-read-review-policy-from-task-record.md) |

### Phase 33 — Handoff commits that cannot name themselves

Makes the Governed SDD completion handoff and reviewer preflight state how a
handoff names a commit that cannot contain its own SHA, and how a wrong commit
field is corrected without amend or force-push.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 088 | Define how a completion handoff names commits that cannot contain their own SHA | 🟡 P2 | — | [088](done/088-handoff-commits-that-cannot-name-themselves.md) |

### Phase 34 — Release 1.2.0 preparation

Closes the changelog, bumps the version, and records the ledger entry for the
first adopter-installable release since `v1.1.50`.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 089 | Prepare release 1.2.0 | 🟡 P2 | 067, 068, 069 | [089](done/089-prepare-release-1-2-0.md) |

### Phase 36 — Post-release install evidence

Records what the migration to the published `v1.2.0` tag proved about the
`meridian@meridian` marketplace install, and keeps the unproven claims
labelled.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 091 | Record the 1.2.0 marketplace install evidence | 🟡 P2 | 065, 089 | [091](done/091-record-1-2-0-marketplace-install-evidence.md) |

### Phase 39 — Release command follow-up and README

Fixes the usage mismatch and the unbounded dry-run output found in the first
run of `scripts/release.py`, and brings the README in line with what ships.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 095 | Fix the release command's usage and dry run, and update the README | 🟡 P2 | 093, 094 | [095](done/095-release-command-fixes-and-readme.md) |

### Phase 42 — Release command for template-changing releases

Lets `release.py publish` release a template-changing release whose version,
ledger, and changelog were bumped by the task that added its migration, and makes
`prepare` explain that state.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 098 | Let `release.py publish` release an already-prepared template-changing release | 🟡 P2 | 094, 095 | [098](done/098-release-publish-prepared-template-changing.md) |

*Last updated: 2026-10-01*

### Phase 45 — Closure blockers found at Task 101

Fixes the two causes found while closing Task 101: `integrate stage` blocking
the archive rename, and a required validation that exceeds the agent host's
command limit, and adds changelog fragments so parallel tasks stop sharing
`[Unreleased]`. Execution order: 111, 101, 102, 116, 112, 113, 114, 115, then the
remaining Phase 44 tasks (see `docs/TASK_CLOSURE_DESIGN.md` once Task 115
records it).

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 111 | Let `integrate stage` accept the exact archive rename of the task record | 🔴 P1 | 055, 063 | [111](done/111-stage-accepts-exact-task-archive-rename.md) |
| `[x]` | 112 | Add a sharded test runner with a coverage proof | 🟡 P2 | 100 | [112](done/112-sharded-test-runner.md) |
| `[x]` | 113 | Add the validation evidence record and a read-only verifier | 🟡 P2 | 112 | [113](done/113-validation-evidence-record-and-verifier.md) |
| `[x]` | 114 | Validate task branches in CI and capture the result as evidence | 🟡 P2 | 113 | [114](done/114-ci-on-task-branches-and-evidence-lookup.md) |
| `[x]` | 115 | Record the validation-timeout and stage-whitelist decisions in the closure design | 🟡 P2 | 100, 101 | [115](done/115-closure-design-addendum-validation-and-stage.md) |
| `[x]` | 116 | Replace edits to `[Unreleased]` with per-task changelog fragments | 🟡 P2 | 093, 095, 098 | [116](done/116-changelog-fragments.md) |
### Phase 41 — Governed Proceed prepares its worktree

Makes a manually typed `Proceed with` in Governed SDD prepare the task's
worktree for exactly that task when no coordinator did, and ships the rule to
adopters as a migration.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 097 | Let a manually typed `Proceed with` prepare its own worktree in Governed SDD | 🟡 P2 | 051, 055 | [097](done/097-governed-proceed-prepares-worktree.md) |
### Phase 38 — Release command

Replaces the manual release steps with a maintainer script: a local `prepare`
that derives the release kind and writes and validates the release commit, and
a `publish` that pushes `main` and the tag only after a typed confirmation.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 093 | Add `scripts/release.py prepare` | 🟡 P2 | 067, 089 | [093](done/093-release-script-prepare.md) |
| `[x]` | 094 | Add `scripts/release.py publish` | 🟡 P2 | 093 | [094](done/094-release-script-publish.md) |
### Phase 37 — Codex machine setup completeness

Moves the Codex skill links and the `MERIDIAN_ROOT` check from manual README
steps into the consented `meridian setup` and the read-only `codex doctor`.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 092 | Link the Codex skills in `meridian setup` and check them in `codex doctor` | 🟡 P2 | 083, 085 | [092](done/092-setup-codex-skill-links-and-doctor-checks.md) |
### Phase 29 — Workflow-aware console state and agent launch

Makes the project console show each task's real state in both Lean Delivery and
Governed SDD projects, then lets the developer start Claude Code or Codex from
it in an iTerm2 tab with the permitted task directive already supplied.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 076 | Show effective task state across workflow modes in the console | 🟡 P2 | 075 | [076](done/076-console-effective-state-and-workflow-profiles.md) |
| `[x]` | 078 | Remove the console refresh latency introduced by effective-state reads | 🔴 P1 | 076 | [078](done/078-fix-console-refresh-latency.md) |
| `[x]` | 079 | Resolve task records in the console when the queue has no file link | 🔴 P1 | 076, 078 | [079](done/079-console-resolve-task-records-without-queue-links.md) |
| `[x]` | 080 | Fit the task ID column to the IDs in the console list | 🟡 P2 | 076 | [080](done/080-console-fit-task-id-column.md) |
| `[x]` | 081 | Group console tasks by their queue headings in Governed SDD projects | 🟡 P2 | 076 | [081](done/081-console-group-tasks-by-queue-heading.md) |
| `[x]` | 082 | Fix detail pane scrolling, Governed objective, and dependency order | 🔴 P1 | 076, 079 | [082](done/082-console-detail-pane-scroll-and-content.md) |
| `[x]` | 084 | Show uncommitted in-progress task state in the console | 🟡 P2 | 076, 078, 079, 082 | [084](done/084-console-show-uncommitted-in-progress-state.md) |
| `[x]` | 077 | Launch Claude Code or Codex from the console in an iTerm2 tab | 🟡 P2 | 076, 078, 079, 080, 081, 082 | [077](done/077-console-launch-agent-in-iterm2.md) |
### Phase 30 — Unified worktree root and host setup

Makes the task-worktree root a machine-level setting that resolves the same way
for Claude Code, Codex, and every project, and adds one consented setup command
that configures the root and the Codex permission profile together.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 083 | Unify worktree-root resolution and add `meridian setup` | 🟡 P2 | 054, 056, 062 | [083](done/083-unified-worktree-root-and-setup.md) |
| `[x]` | 085 | Repair and replace the Codex profile root in one setup step | 🟡 P2 | 062, 083 | [085](done/085-setup-repair-and-replace-codex-profile-root.md) |
### Phase 24 — Review worktree routing correction

Removes contradictory Governed SDD instructions that can send a fresh
reviewer to the primary checkout instead of the task's registered linked
worktree, and migrates the correction to existing adopters.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 064 | Remove the primary-checkout review conflict | 🔴 P1 | 051, 063 | [064](done/064-remove-primary-checkout-review-conflict.md) |
### Phase 23 — Shared task identity resolver

Implements the opt-in identity policy designed by Task 039 as one
host-neutral resolver. Projects remain opaque by default, while structured
milestone adopters gain deterministic task, path, branch, handoff, review, and
budget identities for the worktree lifecycle to consume.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 063 | Implement the task-identity declaration and resolver | 🔴 P1 | 039 | [063](done/063-implement-task-identity-resolver.md) |
### Phase 19 — Proportional integration validation

Removes the unconditional duplicate full-baseline run from task integration.
Validated task evidence is reused when safe; integration defaults to a bounded
gate and escalates to full validation only for explicit or material risk.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 055 | Avoid duplicate full validation during worktree integration | 🔴 P1 | 051 | [055](done/055-avoid-duplicate-full-integration-validation.md) |
### Phase 18 — Codex worktree access

Completes the host-integration side of the isolated-worktree contract: task
worktrees use a shared repository-qualified root, Codex can configure that root
with explicit user consent, and filesystem access remains separate from
protected Git metadata and command policy.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 054 | Configure Codex access for isolated task worktrees | 🔴 P1 | 055 | [054](done/054-configure-codex-worktree-access.md) |
### Phase 16 — Release distribution and adopter updates

Closes the gaps left by Phase 5: plugin version drift, behavior tests missing
from CI, unenforced `protocolVersion`, no defined distribution/update channel
for adopters, and a manual-only release procedure.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 046 | Keep `.claude-plugin/plugin.json` version in sync with `VERSION` | 🔴 P1 | 054 | [046](done/046-sync-plugin-manifest-version.md) |
| `[x]` | 047 | Run the unit test suite in CI | 🔴 P1 | 054 | [047](done/047-run-unit-tests-in-ci.md) |
| `[x]` | 048 | Enforce `protocolVersion` compatibility in the CLI | 🟡 P2 | 015 | [048](done/048-enforce-protocol-version-compatibility.md) |
| `[x]` | 049 | Design the distribution and update channel for adopters | 🟡 P2 | 019 | [049](done/049-design-distribution-and-update-channel.md) |
| `[x]` | 050 | Automate the GitHub Release from a version tag | 🟢 P3 | 021, 046, 047 | [050](done/050-automate-github-release-from-tag.md) |
| `[x]` | 065 | Rename the marketplace and document the pinned install | 🟡 P2 | 049 | [065](done/065-rename-marketplace-and-document-pinned-install.md) |
| `[x]` | 066 | Add `meridian self-check --check-latest` | 🟢 P3 | 049, 050, 065 | [066](done/066-add-self-check-latest-command.md) |
| `[x]` | 067 | Enforce the adopter-facing release-notes contract | 🟢 P3 | 049, 050 | [067](done/067-enforce-release-notes-contract.md) |
| `[x]` | 068 | Document and test the upgrade support policy | 🟢 P3 | 049 | [068](done/068-document-and-test-support-policy.md) |
| `[x]` | 069 | Document Codex install from a tagged checkout | 🟢 P3 | 049 | [069](done/069-document-codex-install-from-tagged-checkout.md) |

## 🧪 Quick Tasks (No File)

None currently. The three pre-queue uncommitted working-tree edits flagged at
project start are all resolved: task 001 shipped the output-bound rewrite,
task 002 filled the `[policy]` placeholder with a default number, and task 004
committed the `AGENTS.md` change-summary line as its own drift proof case,
then folded it into the regenerated `CLAUDE.md`.

### Phase 35 — Single-step upgrade from the 1.0.0 baseline

Found by task 068: a pristine `1.0.0` project does not reach the current
release without conflicts, contradicting Decision 6.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 090 | Make a 1.0.0 project reach the current release in one step (cancelled) | 🟡 P2 | 068 | [090](done/090-make-1-0-0-projects-upgradable-in-one-step.md) |

Cancelled on 2026-10-03: the narrower upgrade window from `v1.1.49` stays.

All completed task and phase records are in `tasks/QUEUE_ARCHIVE.md`; this
operational queue contains only non-terminal work.

*Last updated: 2026-10-01*

### Phase 40 — Release publish wait

Makes `release.py publish` wait for the workflow run to appear, identifies it by
commit, and adds a read-only `verify` to resume verification after the tag is
pushed.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 096 | Retry the workflow lookup in `release.py publish` and add `verify` | 🟡 P2 | 094, 095 | [096](done/096-release-publish-wait-retry.md) |

### Phase 44 — Hands-off task closure design

Designs how an assigned task runs through implementation, validation,
integration, the required `main` push, and cleanup without stopping for avoidable
reasons, and creates the implementation follow-ups.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 100 | Design hands-off task closure | 🔴 P1 | 088, 097, 099 | [100](done/100-design-hands-off-task-closure.md) |
| `[x]` | 101 | Add `meridian worktree closure-status` | 🟡 P2 | 100 | [101](done/101-closure-status-command.md) |
| `[x]` | 102 | Add the evidence command and recompute main-advance facts in `integrate stage` | 🟡 P2 | 100, 111 | [102](done/102-evidence-command-and-main-advance-facts.md) |
| `[x]` | 103 | Apply queue and plan row status during `integrate stage` | 🟡 P2 | 100, 102 | [103](done/103-apply-queue-and-plan-rows-at-integration.md) |
| `[x]` | 104 | Apply phase archival during `integrate stage` | 🟡 P2 | 100, 103 | [104](done/104-apply-phase-archival-at-integration.md) |
| `[x]` | 105 | Derive `[/]` and show closure stop reasons in the console | 🟡 P2 | 101, 103 | [105](done/105-console-derive-in-progress-and-closure-stops.md) |
| `[x]` | 106 | Narrow the Codex push rule and offer a Claude Code allowlist | 🟡 P2 | 100 | [106](done/106-narrow-push-rule-and-claude-allowlist.md) |
| `[x]` | 107 | Block `integrate stage` when `main` is behind `origin` and report a pending push | 🟡 P2 | 100, 101 | [107](done/107-block-stage-when-main-behind-origin.md) |
| `[x]` | 108 | Add the `Validation skips` handoff field and its check | 🟡 P2 | 099, 100, 113 | [108](done/108-validation-skips-handoff-field.md) |
| `[x]` | 109 | Ship the Lean Delivery closure rules and migration | 🟡 P2 | 100, 101, 102, 103, 104, 106, 107, 108, 113 | [109](done/109-ship-lean-closure-rules-and-migration.md) |
| `[x]` | 110 | Ship the Governed SDD closure rules and migration | 🟡 P2 | 109, 113, 117 | [110](done/110-ship-governed-closure-rules-and-migration.md) |
| `[x]` | 117 | Make `integrate stage` completion mode-aware for Governed SDD | 🟡 P2 | 103, 104 | [117](done/117-make-stage-completion-governed-aware.md) |
| `[x]` | 118 | Show the running framework version and root in the project console | 🟢 P3 | 105 | [118](done/118-console-show-framework-version.md) |
| `[x]` | 119 | Show task elapsed time and lifecycle progress in the project console | 🟢 P3 | 118 | [119](done/119-console-show-task-elapsed-time-and-progress.md) |
| `[x]` | 120 | Quiet validation command and foreground rule for long checks | 🟡 P2 | — | [120](done/120-quiet-validation-command-and-foreground-rule.md) |
| `[x]` | 121 | Verify mandatory commands in candidate validation evidence | 🟡 P2 | 120 | [121](done/121-finalize-checks-candidate-validation-commands.md) |
| `[x]` | 122 | Define the bounded gate per integration outcome | 🟡 P2 | 121 | [122](done/122-define-bounded-gate-per-integration-outcome.md) |
| `[x]` | 123 | Complete the unattended-closure command policy for Codex and Claude Code | 🟡 P2 | — | [123](done/123-allow-archive-rename-in-agent-command-policies.md) |
| `[x]` | 124 | Keep a closing task visible in the console until cleanup, in both workflows | 🟡 P2 | 119 | [124](done/124-console-keep-closing-tasks-visible.md) |
| `[x]` | 125 | Make candidate validation commands project-declared and align the gate docs for both workflows | 🔴 P1 | 121, 122 | [125](done/125-project-declared-candidate-validation-commands.md) |

### Phase 45 — Console polish

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 126 | Let the console resume an interrupted task | 🟡 P2 | 124 | [126](done/126-console-resume-interrupted-task.md) |

### Phase 46 — Release 1.2.6 readiness

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 127 | Distribute `docs/WORKTREE_LIFECYCLE.md` to Lean Delivery projects | 🔴 P1 | 125 | [127](done/127-ship-lean-worktree-lifecycle-doc.md) |

### Phase 47 — Release 1.2.6 upgrade blocker

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 128 | Upgrade a newly managed file that the project already has | 🔴 P1 | 127 | [128](done/128-adopt-existing-copy-of-newly-managed-file.md) |

### Phase 48 — Opt-in milestone task identity

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 129 | Choose the task-identity mode at project setup | 🟡 P2 | — | [129](done/129-choose-task-identity-at-project-setup.md) |
| `[x]` | 130 | Make task creation follow the project's task-identity mode | 🟡 P2 | 129 | [130](done/130-identity-aware-task-creation.md) |

### Phase 49 — Release tooling

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 131 | Verify the latest release without the removed `isLatest` field | 🟡 P2 | — | [131](done/131-release-verify-latest-without-islatest.md) |
| `[x]` | 132 | Document the settings-pinned marketplace refusal and how to check the installed version | 🟢 P3 | — | [132](done/132-readme-marketplace-pin-in-settings-note.md) |

### Phase 52 — Governed queue shapes

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 140 | Let `integrate stage` complete rows of project-shaped Governed queues | 🔴 P1 | — | [140](done/140-governed-project-queue-shapes.md) |

### Phase 52 — Consumer conformance (Palimpsest report)

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 142 | Recognize spike rows at stage and require `git diff --check` at finalize | 🔴 P1 | — | [142](done/142-stage-spike-rows-and-diff-check.md) |
| `[x]` | 143 | Make the read-guard and queue-briefing hooks independent of queue status | 🔴 P1 | — | [143](done/143-hooks-derive-task-state-from-worktree.md) |
| `[x]` | 144 | Add `.meridian/project.json` as the project declaration surface | 🟡 P2 | — | [144](done/144-project-declaration-file.md) |
| `[x]` | 145 | Align Governed lifecycle capability text with the closure design and the CLI | 🔴 P1 | 142, 143, 144 | [145](done/145-governed-lifecycle-text-alignment.md) |
| `[x]` | 146 | Restructure inline markers, audit managed copies, and add consumer profiles | 🟡 P2 | 145 | [146](done/146-marker-structure-audit-and-consumer-profiles.md) |
| `[x]` | 147 | Isolate setup CLI tests from the developer's real home directory | 🔴 P1 | — | [147](done/147-isolate-setup-tests-from-real-home.md) |

### Phase 50 — Interrupted task recovery

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 133 | Let a confirmed Resume reach a dirty task worktree | 🟡 P2 | — | [133](done/133-resume-dirty-task-worktree.md) |

### Phase 51 — Context cost

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 134 | Add `meridian context size` to measure the startup read set | 🟡 P2 | — | [134](done/134-context-size-command.md) |
| `[x]` | 135 | Report measured token usage of agent sessions | 🟡 P2 | — | [135](done/135-session-usage-report.md) |
| `[x]` | 136 | Load workflow context by phase and point agents to bounded readers | 🟡 P2 | 134, 135 | [136](done/136-per-phase-context-loading.md) |
| `[x]` | 137 | Tell Codex agents to wait once for long commands | 🟡 P2 | — | [137](done/137-codex-wait-guidance-for-long-commands.md) |
| `[x]` | 138 | Run the unit suite in parallel without changing what it covers | 🟡 P2 | — | [138](done/138-parallel-test-runner.md) |
| `[x]` | 139 | Make `check_repository.py` catch managed-copy digest drift | 🟡 P2 | — | [139](done/139-check-managed-copy-digest-drift.md) |
| `[x]` | 141 | Count cached input in the Claude Code usage report | 🟡 P2 | — | [141](done/141-usage-report-claude-input-total.md) |

### Phase 53 — Upgrade follow-ups

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 148 | Drop retired markers from project sections carried by a restructure | 🔴 P1 | — | [148](done/148-restructure-drops-retired-markers-from-carried-sections.md) |
| `[x]` | 149 | Warn at upgrade when a markerless managed copy keeps local edits | 🟡 P2 | — | [149](done/149-upgrade-warns-on-edited-markerless-copies.md) |
| `[x]` | 150 | Publish a `stable` branch so the Claude Code plugin follows releases | 🟡 P2 | — | [150](done/150-stable-release-branch-for-plugin-updates.md) |
| `[x]` | 151 | Make hook task-state lookups linear and keep the briefing within its timeout | 🔴 P1 | — | [151](done/151-linear-task-state-lookups-for-hooks.md) |
| `[x]` | 152 | Read project declarations from the primary checkout, keep budget state out of it, and state Review's closure authority | 🔴 P1 | — | [152](done/152-project-declaration-review-authority-and-budget-state.md) |
| `[x]` | 153 | Install the completion template here and keep validation commands unchained | 🟡 P2 | — | [153](done/153-completion-template-and-unchained-validation.md) |
| `[x]` | 154 | Retarget migration 062 to 1.2.8 and reject same-version migrations | 🔴 P1 | — | [154](done/154-retarget-migration-062-to-1-2-8.md) |
| `[x]` | 155 | Align capability-profile surfaces at upgrade and keep `upgrade --check` from blocking on them | 🔴 P1 | 154 | [155](done/155-align-profile-surfaces-at-upgrade.md) |
| `[x]` | 156 | Stop `release.py` passing `--repo` to `gh api` | 🟡 P2 | — | [156](done/156-release-verify-gh-api-repo-flag.md) |
| `[x]` | 157 | Stop `handoff-check` requiring one hard-coded Meridian test as the only valid skip | 🟡 P2 | — | [157](done/157-handoff-check-validation-skips-not-project-specific.md) |
| `[x]` | 158 | Migrate legacy budget state only at upgrade, never from a read | 🔴 P1 | — | [158](done/158-budget-state-migration-only-at-upgrade.md) |
| `[x]` | 159 | Retire the reasoning budget contract | 🔴 P1 | — | [159](done/159-retire-reasoning-budget-contract.md) |
| `[x]` | 160 | Give the Claude Code allowlist parity with the Codex execution-command rules | 🟡 P2 | — | [160](done/160-claude-allowlist-execution-commands.md) |
| `[x]` | 161 | State that a local `main` ahead of `origin/main` does not block integration | 🟡 P2 | — | [161](done/161-state-main-ahead-of-origin-is-allowed.md) |
| `[x]` | 170 | Require a declared validation ID for every command that proves a criterion | 🟡 P2 | — | [170](done/170-declare-validation-id-for-every-proving-command.md) |
| `[x]` | 179 | Stabilize the parallel runner output comparison test | 🔴 P1 | — | [179](done/179-stabilize-parallel-runner-output-test.md) |

### Phase 54 — Stops and denials

Authority: [docs/ADR_STOPS_AND_DENIALS.md](../docs/ADR_STOPS_AND_DENIALS.md). 162–167 shipped in 1.2.9 with 161. The ADR's second release is split by release kind: 168 changes only the CLI and ships in Release A with 171–175; 169 changes managed text and ships in Release B, before 176, so both share one migration and one `git-workflow` marker bump.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 162 | Add the stop-code registry and emit closure stops through it | 🟡 P2 | — | [162](done/162-stop-code-registry-and-closure-codes.md) |
| `[x]` | 163 | Check that managed text and tests agree with the stop-code registry | 🟡 P2 | 162 | [163](done/163-check-stop-codes-against-registry.md) |
| `[x]` | 164 | State the stop and denial rules in the managed workflow text | 🟡 P2 | 161, 163 | [164](done/164-state-stop-and-denial-rules-in-managed-text.md) |
| `[x]` | 165 | Install the deny list as host permission rules | 🟡 P2 | — | [165](done/165-host-deny-rules-for-denied-actions.md) |
| `[x]` | 166 | Give codes and actionable messages to the execution and handoff gates | 🟡 P2 | 162 | [166](done/166-coded-actionable-execution-and-handoff-gates.md) |
| `[x]` | 167 | Make the execution preflight satisfiable during remediation | 🔴 P1 | 166 | [167](done/167-satisfiable-execution-preflight-during-remediation.md) |
| `[x]` | 168 | Report queue sections that archival cannot read | 🟡 P2 | 162 | [168](done/168-report-unarchivable-queue-sections.md) |
| `[x]` | 169 | Code the remaining gates and require every stop to carry a code | 🟡 P2 | 163, 166 | [169](done/169-code-remaining-gates-and-require-coded-stops.md) |

### Phase 55 — Closure flow and measurement

Authority: follow-up designs in [docs/ADR_STOPS_AND_DENIALS.md](../docs/ADR_STOPS_AND_DENIALS.md) and Decision 5 of [docs/TASK_CLOSURE_DESIGN.md](../docs/TASK_CLOSURE_DESIGN.md).

Release plan:

- **Release A (CLI-only, no migration)**: 168, 171, 172, 173, 174, 175. These change only the CLI and plugin hooks. Shipping 171–173 first lets the journal record a baseline before 176 changes managed text, so 172's targets can compare before and after.
- **Release B (template-changing)**: 169, then 176, in one migration, plus 180, which changes only seed templates and needs no migration of its own. 181 adds a managed `.codex/hooks.json` entry and shares that migration. 177 and 178 are integrated first, and the 178 evaluation run on Claude Code gates the release, because 176 shortens the text agents follow. 177 may start once 171 is integrated.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 171 | Record lifecycle command results in a local journal | 🟡 P2 | — | [171](done/171-lifecycle-journal.md) |
| `[x]` | 172 | Add `meridian report flow` over the lifecycle journal | 🟡 P2 | 171 | [172](done/172-report-flow-command.md) |
| `[x]` | 173 | Detect `BLOCKED` reports that no command emitted | 🟡 P2 | 171 | [173](done/173-detect-unbacked-blocked-reports.md) |
| `[x]` | 174 | Add `meridian worktree advance` to drive closure through its mechanical steps | 🟡 P2 | 171 | [174](done/174-worktree-advance-driver.md) |
| `[x]` | 175 | Let `advance` finalize from supplied candidate validation results | 🟡 P2 | 174 | [175](done/175-advance-through-candidate-validation.md) |
| `[x]` | 176 | Replace the closure procedure in managed text with `advance` | 🟡 P2 | 164, 175 | [176](done/176-closure-text-uses-advance.md) |
| `[x]` | 177 | Add an agent evaluation harness graded on the journal and Git state | 🟡 P2 | 171 | [177](done/177-agent-eval-harness.md) |
| `[x]` | 178 | Add the safety and remediation scenarios and run them before template-changing releases | 🟡 P2 | 177, 167 | [178](done/178-agent-eval-scenarios-and-release-gate.md) |
| `[x]` | 180 | Align the queue seed templates with closure ownership | 🟢 P3 | — | [180](done/180-align-queue-seed-templates-with-closure-ownership.md) |
| `[x]` | 181 | Run the stop audit on Codex and record the host on audit lines | 🟡 P2 | 173 | [181](done/181-codex-stop-audit-and-journal-host.md) |

### Phase 57 — Self-hosting installation

Authority: the task 181 unblock of 2026-10-06; `upgrade --check` on this repository stops on a 1.1.49 baseline.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 184 | Bring this repository's Meridian installation to the current release and keep it upgradable | 🟡 P2 | 181 | [184](done/184-bring-self-hosting-installation-current.md) |

### Phase 57 — Python runtime baseline

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 188 | Raise Meridian's minimum supported Python version to 3.12 | 🟡 P2 | — | [188](done/188-python-312-minimum.md) |

### Phase 56 — Test suite cost

Authority: the test suite cost review of 2026-10-06 (848 tests, 343 s sequential, 61 s parallel).

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 182 | Make the parallel test runner this repository's standard validation | 🟡 P2 | — | [182](done/182-parallel-suite-as-standard-validation.md) |
| `[x]` | 183 | Build lifecycle test repositories once per class and copy them per test | 🟡 P2 | — | [183](done/183-shared-test-fixtures-for-lifecycle-tests.md) |
| `[x]` | 185 | Report failing tests by name in the parallel runner and make timing tests tolerate a loaded runner | 🟡 P2 | — | [185](done/185-diagnosable-parallel-failures-and-load-tolerant-timing-tests.md) |
| `[x]` | 186 | Keep `closure-status` read-only when reporting lifecycle state | 🔴 P1 | — | [186](done/186-keep-closure-status-read-only.md) |
| `[x]` | 187 | Stabilize the `closure-status` non-mutation test against Git maintenance | 🔴 P1 | 186 | [187](done/187-stabilize-closure-status-nonmutation-test.md) |

### Phase 58 — Worktree resume access

Authority: Task 183 resume access failure of 2026-10-08.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 189 | Keep worktree resume independent of Git metadata writes | 🔴 P1 | — | [189](done/189-keep-worktree-resume-read-only.md) |

### Phase 59 — Release process

Authority: developer decision of 2026-10-08 during the 1.2.11 release preparation.

| Status | ID | Title | Priority | Depends on | File |
|--------|----|-------|----------|------------|------|
| `[x]` | 190 | Make agent evaluations an optional tool, not a release gate | 🔴 P1 | — | [190](done/190-make-agent-evaluations-optional.md) |
