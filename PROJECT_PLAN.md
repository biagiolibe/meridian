# Project Plan — Meridian

## Task Lifecycle

```text
[ ] TODO -> [/] IN_PROGRESS -> [x] DONE
```

## Active Delivery

- `[ ]` 051 — Enforce isolated worktrees for every task.
- `[ ]` 015 — Split `workflowBaselineVersion` from `frameworkVersion` in manifest and upgrade planner.
- `[ ]` 016 — Propagate `workflowBaselineVersion` to `adopt`/`finalize-adoption`.
- `[ ]` 017 — Relax `check_migrations()`'s VERSION equality to `<=`.
- `[ ]` 018 — Persist-time SemVer guard for prerelease `frameworkVersion`.
- `[ ]` 019 — `releases/<version>.json` immutable release ledger + `check_releases()`.
- `[ ]` 020 — Update docs for the version split.
- `[ ]` 021 — Ship the first CLI-only release as end-to-end proof.
- `[ ]` 039 — Design an opt-in structured task-identity policy.
- `[ ]` 046 — Keep `.claude-plugin/plugin.json` version in sync with `VERSION`.
- `[ ]` 047 — Run the unit test suite in CI.
- `[ ]` 048 — Enforce `protocolVersion` compatibility in the CLI.
- `[ ]` 049 — Design the distribution and update channel for adopters.
- `[ ]` 050 — Automate the GitHub Release from a version tag.

`tasks/QUEUE.md` is the operational source for ordering, dependencies, and
phase status. Completed delivery records are archived in
`tasks/QUEUE_ARCHIVE.md`.
