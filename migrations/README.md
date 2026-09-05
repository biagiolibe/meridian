# Meridian Framework Migrations

Each JSON record describes one released workflow transition. The framework
upgrade CLI uses the records to determine which migrations a project has
received and uses the installed baseline plus the target templates to perform
their managed-file transformation deterministically.

A migration record must declare a stable `id`, contiguous `from` and `to`
versions, a concise description, its managed paths, and post-upgrade
verification. It must be append-only after release. Do not replace a migration
to rewrite historical behavior; add a corrective migration instead.

The records do not authorize an overwrite. `meridian upgrade --apply` first
plans a three-way merge for every managed file and applies nothing if any file
conflicts. Projects created before `.meridian/manifest.json` existed must use
`meridian lock` to start tracking future migrations; absent historical
baselines cannot be inferred safely.

`.meridian/baselines/<version>/` in a generated project is a snapshot of the
templates installed at that version — the merge base for the next upgrade's
three-way merge. Only the snapshot matching the manifest's current
`frameworkVersion` is ever read again, so a completed `upgrade --apply` or
generic `adopt --apply` prunes every other baseline snapshot automatically.
Do not rely on an old snapshot surviving past its upgrade; keep a Git tag or
branch instead if a project needs to inspect a historical baseline.

## Packaged legacy baselines

`release-baselines/1.0.0/` is the immutable Governed SDD template snapshot for
Meridian `1.0.0`. Use it only through:

```bash
meridian adopt --mode governed-sdd --from 1.0.0 --check
```

An adoption plan is safe to apply only when it reports no conflicts. New legacy
baselines must be copied from an immutable released revision and covered by an
adoption test before being distributed.
