# Task 083 — Unify worktree-root resolution and add `meridian setup`

> **ID**: `083`
> **Category**: Host Integration / CLI
> **Priority**: 🟡 P2
> **Estimate**: ~5–8h
> **Assigned to**: Codex
> **Session**: 2026-10-01 worktree-root unification design

## 🎯 Objective

Make task-worktree location a machine-level setting that resolves identically
for Claude Code, Codex, and every project, instead of an argument each
coordinator must invent. Today `--worktree-root` is required by every
`meridian worktree` and `meridian codex` subcommand, `MERIDIAN_WORKTREE_ROOT`
only checks equality, and no user-level configuration exists. Consequently
different hosts and projects use different roots (a Codex profile root, a
project-nested `.claude/worktrees`, `/tmp`, and a sibling directory were all
observed), and the Codex permission profile can point at a root no other host
uses.

Deliver one root-resolution order, a project-location-independent default,
and one idempotent `meridian setup` command that configures the root and the
Codex profile together after explicit consent.

## 📋 Acceptance Criteria

- [ ] A single resolver returns the effective worktree root with this
      precedence: explicit `--worktree-root`, then `MERIDIAN_WORKTREE_ROOT`,
      then the user configuration file, then the built-in default. Every
      `meridian worktree` and `meridian codex` subcommand uses it, and
      `--worktree-root` becomes optional.
- [ ] The built-in default is `~/.meridian/worktrees` expanded against the
      current user's home. It is outside every repository, not under a
      temporary directory, and never the home directory itself or the
      filesystem root. The existing repository-qualified layout is unchanged.
- [ ] Conflicting sources are reported, not silently merged: an explicit value
      that differs from `MERIDIAN_WORKTREE_ROOT` keeps the existing blocked
      behavior, and the diagnostic names which source supplied each value.
- [ ] A user configuration file at `$XDG_CONFIG_HOME/meridian/config.json`
      (falling back to `~/.config/meridian/config.json`) may declare
      `worktreeRoot`. It is optional, versioned, validated, written only by
      `meridian setup --apply`, and absent when the default is used.
- [ ] `meridian setup --check` is read-only. It prints the resolved root and
      its source, whether the directory exists with owner-only permissions,
      and the Codex profile state (`unconfigured`, `ready`,
      `repair-required`, `different-root`, or `blocked`), plus the exact
      bounded changes `--apply` would make. It writes nothing.
- [ ] `meridian setup --apply` is idempotent and is the only write path. It
      creates the root with mode `0700`, writes the user configuration only
      when the root is not the default, and applies or repairs the Codex
      profile for exactly the resolved root by reusing the existing
      `meridian codex configure` logic and backup behavior. It never adopts a
      divergent or ambiguous profile and never touches unrelated Codex
      settings. Repeating it is a no-op.
- [ ] A Codex profile that points at a different root with damaged ownership
      markers is handled by an explicit, documented sequence (repair, then
      replace) or reported as `BLOCKED` with the exact diverging fields. It is
      never overwritten silently.
- [ ] `meridian doctor`-style diagnostics and the start-of-turn briefing report
      a single line when the Codex profile root differs from the resolved root.
      They do not modify anything.
- [ ] Existing worktrees outside the resolved root remain discoverable and are
      never moved or deleted automatically; the change documents how to finish
      and clean them up in the old root.
- [ ] The workflow texts that mention a selected or supplied worktree root in
      `PROJECT_WORKFLOW.md`, both workflow templates, and
      `docs/WORKTREE_LIFECYCLE.md` describe the resolved root. Each changed
      protected capability region has a version bump, marker baselines are
      rewritten deliberately, and a migration record delivers the change to
      existing adopters while preserving project-owned text.
- [ ] Documentation explains the typical flow for installation, a new project,
      and an existing project (see Technical Context), including the rule that
      Claude Code needs no host configuration and Codex needs one consented
      `meridian setup --apply`.
- [ ] Unit tests cover resolution precedence, source reporting, the default
      path on a fresh home, directory creation and permissions, `--check`
      writing nothing, `--apply` idempotence, each Codex profile state, and
      the refusal paths. No test writes to the real home directory or Codex
      configuration.
- [ ] `python3 -m unittest discover -s tests`,
      `python3 scripts/check_repository.py`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_effective_worktree_root`, argument parsers, `codex configure`, worktree commands. |
| `docs/WORKTREE_LIFECYCLE.md` | Command and evidence contract; resolved-root wording. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Codex permission-profile contract and recovery rules. |
| `PROJECT_WORKFLOW.md` | Local Lean Delivery worktree section. |
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md`, `templates/workflows/lean-delivery/docs/WORKTREE_LIFECYCLE.md` | Lean adopter text. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`, `templates/workflows/governed-sdd/docs/WORKTREE_LIFECYCLE.md`, `templates/workflows/governed-sdd/docs/workflows/*.md` | Governed adopter text that repeats the root argument. |
| `hooks/queue-briefing.sh` | One-line root-mismatch notice, read-only. |
| `migrations/`, `migrations/marker-baselines/` | Adopter delivery. |
| `tests/` | Resolver, setup, and migration coverage. |

## 🧩 Technical Context

- **Current behavior**: `_effective_worktree_root` accepts a required path and
  only rejects it when `MERIDIAN_WORKTREE_ROOT` differs or the path is the home
  or filesystem root. The Codex profile root is written only by
  `meridian codex configure --apply --worktree-root`. No default exists, so
  each coordinator selects a root.
- **Desired behavior**: the root resolves in one place, the same on every host
  and project, and Codex's filesystem grant is set from that same value by one
  consented command.
- **Host boundary**: Claude Code and Codex do not read
  `MERIDIAN_WORKTREE_ROOT`; only the Meridian CLI does. Claude therefore needs
  no configuration once the CLI has a default. Codex needs its permission
  profile because its sandbox is host-level; Meridian must not write
  `~/.codex/config.toml` without explicit `--apply`.
- **Host environment inheritance** (whether the desktop app inherits shell
  exports) is not required by this design and is deliberately not relied on.
- **Typical flow to document**:
  1. Install Meridian (plugin or checkout, per the distribution design) and put
     `meridian` on `PATH`.
  2. Once per machine, run `meridian setup --check`, review the output, then
     `meridian setup --apply`, and restart Codex. Claude Code needs nothing.
  3. New project: `meridian init` (or the init skill); worktree lifecycle
     commands then resolve the root with no argument.
  4. Existing project: `meridian upgrade --check` / `--apply` delivers the
     migrated workflow text; no per-project root configuration exists.
  5. Existing worktrees in older roots are finished and cleaned up there with
     `meridian worktree cleanup --worktree-root <old-root>`.
- **Open decisions to settle in the implementation and record in the
  handoff**: whether `meridian setup` also becomes a step of `init`/`adopt`
  output as a printed instruction (it must not run automatically); whether this
  change needs Governed SDD escalation because it changes the public CLI
  contract (the default expectation is Lean Delivery with a migration).

## 🔨 Suggested Implementation

1. Extract the resolver and its source reporting from `_effective_worktree_root`
   and make `--worktree-root` optional on every subcommand that has it.
2. Add the user configuration reader/writer with schema validation.
3. Implement `meridian setup --check` and `--apply` on top of the existing
   `codex configure` planning, backup, and repair code from Task 062.
4. Add the read-only root-mismatch notice to the briefing and diagnostics.
5. Update the workflow texts, bump capability versions, regenerate marker
   baselines, add the migration, and add the documentation flow.
6. Write the tests listed above using temporary home and config directories.

## ⚠️ Constraints and Considerations

- Never write the user's real home, `~/.codex`, or Claude settings from tests.
- Never write Codex or user configuration except through `--apply`.
- Do not move, delete, or recreate existing worktrees automatically; cleanup
  stays the existing non-force command.
- Preserve every existing lifecycle check, lease, and evidence rule; this task
  changes only where the root comes from.
- Preserve project-owned text outside managed capability markers.
- Repository artifacts are English-only.
- A root under a temporary directory or inside a repository must be rejected
  or clearly warned about, because both are volatile or collide with host-native
  isolation directories.

## 🔗 Dependencies

- **Depends on**: 054, 056, 062.
- **Blocks**: none.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/083-unified-worktree-root-and-setup.md)"$'\n\nExecute this task in the current project.'
```
