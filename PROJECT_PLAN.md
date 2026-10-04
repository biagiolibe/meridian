# Project Plan — Meridian

## Task Lifecycle

```text
[ ] TODO -> [/] IN_PROGRESS -> [x] DONE
```

## Active Delivery

- `[x]` 051 — Enforce isolated worktrees for every task.
- `[x]` 055 — Avoid duplicate full validation during worktree integration.
- `[x]` 054 — Configure Codex access for isolated task worktrees.
- `[x]` 056 — Add bounded worktree lifecycle commands.
- `[x]` 057 — Design the Meridian self-hosting capability profile.
- `[x]` 058 — Add self-hosting manifest and capability-catalog support.
- `[x]` 059 — Implement cross-mode capability audit semantics.
- `[x]` 060 — Install Meridian self-hosting capability surfaces.
- `[x]` 061 — Add self-hosting host probes and CI dogfooding gate.
- `[x]` 062 — Make Codex permission-profile repair resilient.
- `[x]` 015 — Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner.
- `[x]` 016 — Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption`.
- `[x]` 017 — Relax `check_migrations()`'s VERSION equality to `<=`.
- `[x]` 018 — Persist-time SemVer guard for prerelease `frameworkVersion`.
- `[x]` 019 — `releases/<version>.json` immutable release ledger + `check_releases()`.
- `[x]` 020 — Update docs for the version split.
- `[x]` 021 — Ship the first CLI-only release as end-to-end proof.
- `[x]` 039 — Design an opt-in structured task-identity policy.
- `[x]` 063 — Implement the task-identity declaration and resolver.
- `[x]` 064 — Remove the primary-checkout review conflict.
- `[x]` 046 — Keep `.claude-plugin/plugin.json` version in sync with `VERSION`.
- `[x]` 047 — Run the unit test suite in CI.
- `[x]` 048 — Enforce `protocolVersion` compatibility in the CLI.
- `[x]` 049 — Design the distribution and update channel for adopters.
- `[x]` 050 — Automate the GitHub Release from a version tag.
- `[x]` 065 — Rename the marketplace and document the pinned install.
- `[x]` 066 — Add `meridian self-check --check-latest`.
- `[x]` 070 — Build a read-only project console with automatic local refresh.
- `[x]` 071 — Apply the compact dark shell design to the project console.
- `[x]` 072 — Match the approved console mockup in the terminal renderer.
- `[x]` 073 — Make directives copyable and restore All filter navigation.
- `[x]` 074 — Use the terminal background in the project console.
- `[x]` 075 — Distribute the project console through the Meridian CLI.
- `[x]` 076 — Show effective task state across workflow modes in the console.
- `[x]` 078 — Remove the console refresh latency introduced by effective-state reads.
- `[x]` 079 — Resolve task records in the console when the queue has no file link.
- `[x]` 080 — Fit the task ID column to the IDs in the console list.
- `[x]` 081 — Group console tasks by their queue headings in Governed SDD projects.
- `[x]` 082 — Fix detail pane scrolling, Governed objective, and dependency order.
- `[x]` 084 — Show uncommitted in-progress task state in the console.
- `[x]` 077 — Launch Claude Code or Codex from the console in an iTerm2 tab.
- `[x]` 067 — Enforce the adopter-facing release-notes contract.
- `[x]` 068 — Document and test the upgrade support policy.
- `[x]` 083 — Unify worktree-root resolution and add `meridian setup`.
- `[x]` 085 — Repair and replace the Codex profile root in one setup step.
- `[x]` 086 — Launch console agents in a horizontal iTerm2 split pane.
- `[x]` 087 — Read the review policy from the task record in the console.
- `[x]` 088 — Define how a completion handoff names commits that cannot contain their own SHA.
- `[x]` 089 — Prepare release 1.2.0.
- `[x]` 090 — Make a 1.0.0 project reach the current release in one step (cancelled, see `tasks/done/090-make-1-0-0-projects-upgradable-in-one-step.md`).
- `[x]` 091 — Record the 1.2.0 marketplace install evidence.
- `[x]` 092 — Link the Codex skills in `meridian setup` and check them in `codex doctor`.
- `[x]` 093 — Add `scripts/release.py prepare`.
- `[x]` 094 — Add `scripts/release.py publish`.
- `[x]` 095 — Fix the release command's usage and dry run, and update the README.
- `[x]` 096 — Retry the workflow lookup in `release.py publish` and add `verify`.
- `[x]` 097 — Let a manually typed `Proceed with` prepare its own worktree in Governed SDD.
- `[x]` 098 — Let `release.py publish` release an already-prepared template-changing release.
- `[x]` 099 — Skip the AppleScript compile test when `osacompile` cannot run.
- `[x]` 100 — Design hands-off task closure.
- `[x]` 101 — Add `meridian worktree closure-status`.
- `[x]` 102 — Add the evidence command and recompute main-advance facts in `integrate stage`.
- `[x]` 103 — Apply queue and plan row status during `integrate stage`.
- `[x]` 104 — Apply phase archival during `integrate stage`.
- `[x]` 105 — Derive `[/]` and show closure stop reasons in the console.
- `[x]` 106 — Narrow the Codex push rule and offer a Claude Code allowlist.
- `[x]` 107 — Block `integrate stage` when `main` is behind `origin` and report a pending push.
- `[x]` 108 — Add the `Validation skips` handoff field and its check.
- `[x]` 109 — Ship the Lean Delivery closure rules and migration.
- `[x]` 110 — Ship the Governed SDD closure rules and migration.
- `[x]` 111 — Let `integrate stage` accept the exact archive rename of the task record.
- `[x]` 112 — Add a sharded test runner with a coverage proof.
- `[x]` 113 — Add the validation evidence record and a read-only verifier.
- `[x]` 114 — Validate task branches in CI and capture the result as evidence.
- `[x]` 115 — Record the validation-timeout and stage-whitelist decisions in the closure design.
- `[x]` 116 — Replace edits to `[Unreleased]` with per-task changelog fragments.
- `[x]` 117 — Make `integrate stage` completion mode-aware for Governed SDD.
- `[x]` 118 — Show the running framework version and root in the project console.
- `[x]` 119 — Show task elapsed time and lifecycle progress in the project console.
- `[x]` 120 — Quiet validation command and foreground rule for long checks.
- `[x]` 121 — Verify mandatory commands in candidate validation evidence.
- `[x]` 122 — Define the bounded gate per integration outcome.
- `[x]` 123 — Complete the unattended-closure command policy for Codex and Claude Code.
- `[x]` 124 — Keep a closing task visible in the console until cleanup, in both workflows.
- `[x]` 125 — Make candidate validation commands project-declared and align the gate docs for both workflows.
- `[x]` 126 — Let the console resume an interrupted task.
- `[x]` 127 — Distribute `docs/WORKTREE_LIFECYCLE.md` to Lean Delivery projects.
- `[x]` 128 — Upgrade a newly managed file that the project already has.
- `[x]` 129 — Choose the task-identity mode at project setup.
- `[x]` 130 — Make task creation follow the project's task-identity mode.
- `[x]` 131 — Verify the latest release without the removed `isLatest` field.
- `[x]` 132 — Document the settings-pinned marketplace refusal and how to check the installed version.
- `[x]` 133 — Let a confirmed Resume reach a dirty task worktree.
- `[x]` 134 — Add `meridian context size` to measure the startup read set.
- `[x]` 135 — Report measured token usage of agent sessions.
- `[x]` 136 — Load workflow context by phase and point agents to bounded readers.
- `[x]` 137 — Tell Codex agents to wait once for long commands.
- `[ ]` 138 — Run the unit suite in parallel without changing what it covers.
- `[x]` 139 — Make `check_repository.py` catch managed-copy digest drift.
- `[x]` 141 — Count cached input in the Claude Code usage report.
- `[x]` 142 — Recognize spike rows at stage and require `git diff --check` at finalize.
- `[x]` 143 — Make the read-guard and queue-briefing hooks independent of queue status.
- `[x]` 144 — Add `.meridian/project.json` as the project declaration surface.
- `[x]` 145 — Align Governed lifecycle capability text with the closure design and the CLI.
- `[x]` 146 — Restructure inline markers, audit managed copies, and add consumer profiles.
- `[x]` 147 — Isolate setup CLI tests from the developer's real home directory.
- `[x]` 148 — Drop retired markers from project sections carried by a restructure.
- `[ ]` 149 — Warn at upgrade when a markerless managed copy keeps local edits.
- `[ ]` 150 — Publish a `stable` branch so the Claude Code plugin follows releases.
- `[x]` 140 — Let `integrate stage` complete rows of project-shaped Governed queues.
- `[x]` 069 — Document Codex install from a tagged checkout.
- `[x]` 052 — Make the upgrade planner aware of generated entry routers.
- `[x]` 053 — Remove machine-specific absolute paths from tracked records.

`tasks/QUEUE.md` is the operational source for ordering, dependencies, and
phase status. Completed delivery records are archived in
`tasks/QUEUE_ARCHIVE.md`.
