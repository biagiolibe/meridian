# Task 092 — Link the Codex skills in `meridian setup` and check them in `codex doctor`

> **ID**: `092`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Developer question on which Codex install steps `meridian setup` performs

## Objective

Today `meridian setup` creates the worktree root and writes the Codex permission
profile, and nothing else. The README's Codex quick start still asks the
developer to link the two skills into `~/.agents/skills` and to set
`MERIDIAN_ROOT` and `PATH` by hand. Make `meridian setup` plan and, only with
`--apply`, create the skill links, report the shell-profile lines without
editing the profile, and make `meridian codex doctor` report the same facts
read-only.

## Acceptance Criteria

- [ ] `meridian setup --check` lists, in addition to its current output, the
  state of the two user-skill links `~/.agents/skills/meridian-lean-delivery`
  and `~/.agents/skills/meridian-governed-sdd`. Each link is in exactly one of
  these states, with the planned change stated:
  - `ready`: a symlink already points to `<framework root>/skills/<name>`;
  - `missing`: nothing exists there; `--apply` creates the symlink;
  - `conflict`: a symlink points elsewhere;
  - `blocked`: a regular file or directory exists there.
- [ ] `conflict` and `blocked` are never overwritten, replaced, or removed by
  any mode. They make the overall setup result `blocked` and name the path and
  the observed target, and nothing is written for that run.
- [ ] `--check` writes nothing. `--apply` creates only the missing links (and
  `~/.agents/skills` with owner-only mode if absent), is idempotent, and a
  second `--apply` reports no changes.
- [ ] Links are planned only when the framework root of the running CLI is a Git
  checkout containing `skills/<name>/SKILL.md` for both names. Otherwise the
  link step reports `skipped` with the reason (for example a versioned plugin
  cache path, which changes on every update) and the rest of setup is
  unaffected.
- [ ] `meridian setup --check` prints the exact `MERIDIAN_ROOT` and `PATH` lines
  to add to the developer's shell profile and states whether `MERIDIAN_ROOT` in
  the current environment is unset, equal to the framework root, or different.
  Setup never edits a shell profile and never exports anything itself.
- [ ] A stale `~/.codex/skills/meridian-*` copy is reported as a warning naming
  the path; setup does not touch it (the README already says to remove it by
  hand).
- [ ] `meridian codex doctor` adds two read-only checks using its existing
  `name: state` output shape: the skill links (`ready`, `missing`, `conflict`,
  `blocked`, or `skipped`) and `MERIDIAN_ROOT` (`ready`, `unset`, or
  `mismatch`). It writes nothing and does not change the existing seven checks.
- [ ] Existing `setup` exit codes and the output of the current worktree-root and
  Codex-profile sections are unchanged.
- [ ] The README Codex quick start replaces the manual `mkdir` and `ln -s` lines
  with `meridian setup --check` / `--apply`, keeps the clone and the shell-profile
  lines as the developer's steps, and `CHANGELOG.md` records the change under
  `[Unreleased]`.
- [ ] If implementing this requires a new top-level command, a new flag, or a
  write outside `~/.agents/skills`, the task stops and reports instead of
  deciding, because Governed SDD would then apply.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `plan_setup`, `apply_setup`, `_setup_codex_state`, `codex_doctor`, and their output printing. |
| `tests/test_meridian_cli.py` | Existing setup and doctor tests to extend. |
| `README.md` | "Quick start with Codex" install lines. |
| `CHANGELOG.md` | `[Unreleased]` entry. |

## Technical Context

- `plan_setup` already takes `home` and `environment` parameters, so the links
  can be planned against a temporary home in tests and never against the real
  one.
- **Current behavior**: `setup` covers the worktree root and the Codex permission
  profile. `codex doctor` reports `permission-model`, `profile-ownership`,
  `project-trust`, `command-policy`, `lifecycle-command-policy`,
  `worktree-root-write`, and `git-metadata`. Neither mentions skills or
  `MERIDIAN_ROOT`.
- **Desired behavior**: setup owns the machine-level filesystem facts that the
  README currently leaves to manual steps, while the clone (which chooses the
  version) and the shell profile (a file Meridian does not own) stay with the
  developer.
- The two linked skills are exactly the names in the README. The `-claude-code`
  skills are not Codex skills and are not linked.
- Codex discovery of `$HOME/.agents/skills` symlinks is recorded as verified in
  the README for Codex CLI 0.159.2; this task does not re-verify it.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Unit tests, using a temporary home and no real `~/.agents`, cover: each link
  state, `--check` writing nothing, idempotent `--apply`, refusal to overwrite
  `conflict` and `blocked`, `skipped` for a non-checkout framework root, the
  `MERIDIAN_ROOT` states, the stale `~/.codex/skills` warning, the two new
  doctor checks being read-only, and unchanged existing output.
- Evidence tier: filesystem state and printed text are program-computed and
  asserted; no manual evidence is required.

## Out of scope

Cloning Meridian, choosing or moving a version, editing shell profiles, Claude
Code plugin installation, a Codex plugin package, and any change to the
permission profile.

## Dependencies

- **Depends on**: 083, 085
- **Blocks**: none
