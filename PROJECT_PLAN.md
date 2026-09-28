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
- `[/]` 060 — Install Meridian self-hosting capability surfaces.
- `[ ]` 061 — Add self-hosting host probes and CI dogfooding gate.
- `[ ]` 062 — Make Codex permission-profile repair resilient.
- `[x]` 015 — Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner.
- `[ ]` 016 — Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption`.
- `[ ]` 017 — Relax `check_migrations()`'s VERSION equality to `<=`.
- `[ ]` 018 — Persist-time SemVer guard for prerelease `frameworkVersion`.
- `[ ]` 019 — `releases/<version>.json` immutable release ledger + `check_releases()`.
- `[ ]` 020 — Update docs for the version split.
- `[ ]` 021 — Ship the first CLI-only release as end-to-end proof.
- `[x]` 039 — Design an opt-in structured task-identity policy.
- `[x]` 063 — Implement the task-identity declaration and resolver.
- `[x]` 064 — Remove the primary-checkout review conflict.
- `[x]` 046 — Keep `.claude-plugin/plugin.json` version in sync with `VERSION`.
- `[x]` 047 — Run the unit test suite in CI.
- `[x]` 048 — Enforce `protocolVersion` compatibility in the CLI.
- `[ ]` 049 — Design the distribution and update channel for adopters.
- `[ ]` 050 — Automate the GitHub Release from a version tag.
- `[x]` 052 — Make the upgrade planner aware of generated entry routers.
- `[ ]` 053 — Remove machine-specific absolute paths from tracked records.

`tasks/QUEUE.md` is the operational source for ordering, dependencies, and
phase status. Completed delivery records are archived in
`tasks/QUEUE_ARCHIVE.md`.
