# History Rewrite of 2026-10-14

On 2026-10-14 the repository history was rewritten to replace personal email
addresses in commit metadata with the maintainer's GitHub `noreply` address.
Only author, committer, and tagger emails changed. Every file in every commit,
branch, and tag is unchanged; the rewrite was verified by comparing the trees
of `main`, `stable`, and all 14 release tags before and after.

Because the metadata is part of each commit's identity, every commit received
a new SHA. Release tags `v1.1.49` through `v1.2.15` were moved to the
rewritten commits, and their GitHub Releases are unchanged.

## Resolving an old commit SHA

Commit messages were translated to the new SHAs during the rewrite. File
contents were not: task handoffs, `.meridian/tasks/*.json` transitions, and
other records may still cite pre-rewrite SHAs.
[commit-map-2026-10-14.txt](commit-map-2026-10-14.txt) maps each old SHA to
its new SHA, one pair per line after the `old new` header:

```bash
grep '^<old-sha-prefix>' docs/history/commit-map-2026-10-14.txt
```

No gate reads the commit SHAs of terminal tasks, so the old references affect
no lifecycle decision.

## Consequences for existing clones

A clone made before the rewrite holds the old history. Do not pull into it:
clone the repository again. A Claude Code marketplace added before the rewrite
is refreshed by removing it and adding `biagiolibe/meridian#v<version>` again.
A Codex checkout is refreshed with a new clone or `git fetch --tags --force`.
