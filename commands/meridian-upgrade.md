---
description: "Check or apply a deterministic Meridian framework upgrade"
---

Upgrade a project initialized by Meridian without overwriting local workflow
customizations.

Run the CLI from this plugin source. First inspect the plan:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/meridian upgrade --project . --check
```

If this is a project created before framework locking, use a packaged baseline
to preview adoption first (`--mode` and `--from` are detected automatically
when unambiguous):

```bash
${CLAUDE_PLUGIN_ROOT}/bin/meridian adopt --project . --check
```

Run the same command with `--apply` only after a conflict-free plan and explicit
developer authorization. The CLI refuses to infer an unrecorded baseline.

When the generic plan conflicts because the project has an intentional local
workflow adaptation, use `/meridian-adopt` instead. It detects which framework
capabilities are already present, scopes an agent migration to only the missing
ones, and finalizes the lockfile after an independent review.

If the plan has no `CONFLICT` entries and the developer authorizes the update,
apply it:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/meridian upgrade --project . --apply
```

The CLI uses `.meridian/manifest.json` and installed baseline snapshots for a
three-way merge. It applies no files when any managed-file conflict exists.
After a successful apply, inspect the diff, run the project's baseline checks,
and create a dedicated framework-upgrade commit. Never resolve conflict markers
or edit `.meridian/` baselines automatically; report `BLOCKED` with the exact
paths instead.
