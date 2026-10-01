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
- `[ ]` 088 — Define how a completion handoff names commits that cannot contain their own SHA.
- `[x]` 089 — Prepare release 1.2.0.
- `[ ]` 090 — Make a 1.0.0 project reach the current release in one step.
- `[x]` 091 — Record the 1.2.0 marketplace install evidence.
- `[x]` 092 — Link the Codex skills in `meridian setup` and check them in `codex doctor`.
- `[x]` 093 — Add `scripts/release.py prepare`.
- `[x]` 094 — Add `scripts/release.py publish`.
- `[x]` 095 — Fix the release command's usage and dry run, and update the README.
- `[ ]` 096 — Retry the workflow lookup in `release.py publish` and add `verify`.
- `[x]` 097 — Let a manually typed `Proceed with` prepare its own worktree in Governed SDD.
- `[ ]` 098 — Let `release.py publish` release an already-prepared template-changing release.
- `[x]` 069 — Document Codex install from a tagged checkout.
- `[x]` 052 — Make the upgrade planner aware of generated entry routers.
- `[x]` 053 — Remove machine-specific absolute paths from tracked records.

`tasks/QUEUE.md` is the operational source for ordering, dependencies, and
phase status. Completed delivery records are archived in
`tasks/QUEUE_ARCHIVE.md`.
