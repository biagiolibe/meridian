# Task 225 — Update the framework checkout with `meridian self-update`

> **ID**: `225`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h (split if the plan and apply paths do not fit)
> **Assigned to**: unassigned
> **Session**: Release checkout review, 2026-10-15
> **Origin**: friction

## Objective

The `meridian` CLI, the Codex skills, and `scripts/upgrade_project.sh` run
from a local framework checkout (`MERIDIAN_ROOT`). Moving that checkout to a
new release is a manual Git step that is easy to get wrong:

- an unset variable in `git -C "$VAR" pull` silently runs in the current
  directory;
- a checkout moved past a tag makes `upgrade_project.sh` stop with
  `framework HEAD is not tag v<version>`;
- running agent sessions keep using the old CLI until restarted.

Add a controlled `meridian self-update` command that plans and applies the
move of the checkout the CLI runs from, and verifies the result. It never
updates in the background and never touches projects.

## Acceptance Criteria

- [ ] `meridian self-update --check` identifies the framework checkout that the
  running CLI belongs to and prints a plan without changing anything:
  - the current version and the target version;
  - the release kind, patch or minor, and whether it changes templates, from
    the release notes;
  - the link to the release notes;
  - the Git operation it would run.
  The target is the latest release by default; `--to v<version>` selects
  another release tag, including an older one for rollback. Without
  network access, `--check` reports the latest release as unknown and exits
  with a distinct code, as `self-check --check-latest` does.
- [ ] `meridian self-update --apply` performs the plan:
  - on a checkout that follows `stable`, a fast-forward of `stable` to
    `origin/stable`;
  - on a detached checkout at a release tag, a checkout of the target tag
    after `git fetch --tags`;
  - with `--to v<version>` on a `stable` checkout, it stops and explains how
    to switch to a tag checkout; it does not reset `stable`.
- [ ] Each refusal stops with a registered `BLOCKED <CODE>` before any Git
  change:
  - uncommitted or untracked changes in the checkout;
  - a checkout on `main` or any branch other than `stable`, which covers a
    development clone;
  - a `stable` that cannot fast-forward;
  - a target that is not a release tag;
  - a CLI that runs from the Claude Code plugin cache, which the plugin
    manager owns; the message names `/plugin marketplace update meridian`.
- [ ] After `--apply`, the command verifies that `HEAD` is exactly the target
  tag and that `VERSION` matches it, the same conditions that
  `upgrade_project.sh` requires. A failed verification stops with a
  registered code and prints the recovery command.
- [ ] On success it prints the next steps: restart running Codex and Claude
  Code sessions, and run `meridian upgrade --check` in each project when the
  release changes templates.
- [ ] The command never edits shell profiles, Codex or Claude configuration,
  skill links, or any project. It runs no update without `--apply`.
- [ ] Tests use local Git fixtures, with no network access, and cover:
  - the plan on a `stable` checkout and on a tag checkout;
  - apply on both;
  - `--to` rollback on a tag checkout;
  - every refusal above;
  - the post-apply verification failure;
  - offline `--check`.
- [ ] `docs/PUBLIC_SURFACE.md` lists `meridian self-update` as Experimental.
  The README update procedure, or the document it links for updates, names
  the command. One changelog fragment records it under `Added`, which makes
  the next release a minor release.
- [ ] The managed Codex user rules block from task 221 does not allow
  `self-update --apply`; `self-update --check` may be allowed.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Argument parser, `run_self_check`, `fetch_latest_release`, `plugin_ref_report`, Codex user rules block. |
| `scripts/upgrade_project.sh` | The tag check the result must satisfy. |
| `docs/PUBLIC_SURFACE.md` | Surface classification. |
| `docs/HOW_TO_UPGRADE.md`, `README.md` | Update documentation. |
| `tests/` | Self-check and CLI tests. |

## Technical Context

- `meridian self-check --check-latest` already reads the latest public GitHub
  Release with no credentials, and uses exit codes `0` (`UP_TO_DATE`), `10`
  (`UPDATE_AVAILABLE`), and `11` (`UNKNOWN`). Reuse its release lookup.
- Each release's `publish` fast-forwards `stable` to the commit of its
  `v<version>` tag, so a `stable` checkout reaches the latest release by a
  fast-forward.
- The maintainer guide on the `maintainer-docs` branch documents the manual
  procedure (`git -C "$MERIDIAN_ROOT" pull --ff-only origin stable` plus the
  tag check); task 224 documents both checkout variants in
  `docs/HOW_TO_UPGRADE.md`.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## Out of scope

Background or scheduled updates. Updating the Claude Code plugin. Upgrading
projects. Changing `MERIDIAN_ROOT` or shell profiles. Release signature
verification.

## Dependencies

- **Depends on**: none. Schedule after 224 if both edit
  `docs/HOW_TO_UPGRADE.md` at the same time.
- **Blocks**: none

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/225-self-update-command.md)"$'\n\nExecute this task in the current project.'
```
