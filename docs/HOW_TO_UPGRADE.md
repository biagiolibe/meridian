# How to upgrade a project

This guide upgrades one Meridian-managed project to the release you have
installed, using `scripts/upgrade_project.sh`. The script wraps the manual
procedure in the README's [Updating Meridian](../README.md#updating-meridian)
and [Framework upgrades](../README.md#framework-upgrades) sections. It runs on
a dedicated branch and never merges, pushes, tags, or deletes anything.

## 1. Update the framework first

A project can only be upgraded to a release the framework already has.

- **Claude Code** (marketplace declared with `"ref": "stable"`):

  ```text
  /plugin marketplace update meridian
  ```

- **Codex** (tagged checkout):

  ```bash
  git -C "$MERIDIAN_ROOT" fetch --tags && git -C "$MERIDIAN_ROOT" checkout v<version>
  ```

Read the release section in `CHANGELOG.md` before upgrading projects. A
template-changing release lists the affected files and likely conflicts under
`Upgrade notes`.

## 2. Pick the framework root

Pass the framework with `--meridian-root`. It must be a released version:

- the installed Claude Code plugin, for example
  `~/.claude/plugins/cache/meridian/meridian/<version>`; or
- a Meridian checkout whose `HEAD` is exactly the tag `v<version>`.

The script refuses a checkout that is not at the release tag, because upgrading
from unreleased `main` is not supported. `--allow-untagged` overrides this for
framework development only.

The examples below use:

```bash
export FW=~/.claude/plugins/cache/meridian/meridian/<version>
```

## 3. Prepare the project

The script checks these itself and stops if one fails:

- the project has `.meridian/manifest.json`;
- it is the primary checkout, on `main`, with a clean working tree;
- `main` is not behind `origin/main`;
- the branch `meridian-upgrade-<version>` does not exist yet.

Prefer upgrading when no task worktree is open. An open worktree keeps the old
workflow text until its task is integrated; the script prints a note when it
finds one.

## 4. Preview

Without `--apply` nothing is changed:

```bash
scripts/upgrade_project.sh /path/to/project --meridian-root "$FW"
```

It prints the `meridian upgrade --check` plan, the `meridian setup --check`
plan, and the queue usage-text diff. A blocked upgrade plan stops here; resolve
the listed conflicts before continuing.

## 5. Apply

Add `--apply` and the project's own validation commands, one `--validate` per
command:

```bash
scripts/upgrade_project.sh /path/to/project --meridian-root "$FW" --apply \
  --validate "<format check>" --validate "<build>" --validate "<tests>"
```

The script then:

1. creates the branch `meridian-upgrade-<version>`;
2. runs `meridian upgrade --apply`;
3. runs `meridian setup --apply`;
4. aligns the queue usage text with `scripts/align_queue.py`;
5. runs `meridian audit` and stops on any `FAIL` row (`UNVERIFIED` and
   `ADVISORY` rows do not stop it);
6. checks that the manifest `frameworkVersion` is the new version;
7. runs each `--validate` command in the project;
8. commits on the branch, leaving `.claude/settings.local.json` uncommitted.

If a step fails after the branch exists, nothing is committed and the script
prints the commands that discard the attempt and return to `main`.

## 6. Review, integrate, and publish

The script ends by printing these steps; run them yourself:

```bash
git -C /path/to/project diff main..meridian-upgrade-<version>
git -C /path/to/project switch main
git -C /path/to/project merge --ff-only meridian-upgrade-<version>
git -C /path/to/project push origin main
git -C /path/to/project branch -d meridian-upgrade-<version>
```

Then restart open Claude Code or Codex sessions in the project so they reload
the updated workflow text and settings.

## Options

| Option | Effect |
|--------|--------|
| `--apply` | Perform the upgrade; without it the run is a preview. |
| `--validate "<cmd>"` | Run a project validation command before committing; repeatable. |
| `--meridian-root <path>` | Framework to upgrade from; defaults to the `meridian` on `PATH`. |
| `--branch <name>` | Branch name instead of `meridian-upgrade-<version>`. |
| `--skip-setup` | Do not run `meridian setup`; it may also change machine-level settings such as the Codex profile and skill links. |
| `--skip-queue` | Do not align the queue usage text. |
| `--allow-untagged` | Accept a framework checkout that is not at its release tag. |

## Aligning only the queue

The queue is not a managed file, so `meridian upgrade` never changes it. To
align its usage text without upgrading, run the aligner directly. It finds the
queue through `meridian locations`, so a queue outside `tasks/QUEUE.md` (for
example `docs/TASK_QUEUE.md`) is handled:

```bash
python3 scripts/align_queue.py /path/to/project --meridian "$FW/bin/meridian"
python3 scripts/align_queue.py /path/to/project --meridian "$FW/bin/meridian" --apply
```

It never stages or commits, and a second run reports `no change`.

## Recovering a manual upgrade

If `meridian upgrade --apply` was already run by hand on `main` and left
uncommitted changes, the script refuses the dirty tree. Finish by hand instead:

```bash
git -C /path/to/project switch -c meridian-upgrade-<version>
python3 scripts/align_queue.py /path/to/project --meridian "$FW/bin/meridian" --apply
"$FW/bin/meridian" audit --project /path/to/project
```

Run the project's validation, commit on the branch, and continue with step 6.
