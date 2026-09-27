# Task 062 — Make Codex permission-profile repair resilient

> **ID**: `062`
> **Category**: Host Integration / Reliability
> **Priority**: 🟡 P2
> **Estimate**: ~3–5h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Make Meridian's Codex permission-profile configurator resilient when a Codex
app update or settings rewrite preserves the effective TOML profile but drops,
moves, or normalizes Meridian's comment delimiters.

The configurator must recognize an exactly equivalent managed profile and offer
a safe, explicit repair path without weakening its fail-closed behavior for
foreign, divergent, ambiguous, or partially overlapping configuration.

## 📋 Acceptance Criteria

- [ ] `meridian codex configure --check` distinguishes a semantically identical
      profile with damaged or missing Meridian ownership comments from a
      genuinely incomplete or conflicting profile.
- [ ] The diagnostic reports a named repairable state and prints the exact
      bounded change. It does not report the permission model as generically
      blocked when the expected profile name, inheritance, workspace root, and
      selected default are all semantically identical.
- [ ] `--apply` can repair ownership metadata only after explicit invocation,
      while preserving unrelated keys, comments, tables, ordering where
      practical, and application-managed settings.
- [ ] Repair creates a restrictive backup and uses the existing atomic write
      path. Repeating the repair is idempotent.
- [ ] A profile with a different root, parent, description, default selection,
      extra permission grants, ambiguous duplicate tables, legacy sandbox
      settings, or only a partial semantic match remains `BLOCKED` and is never
      adopted or overwritten automatically.
- [ ] The ownership strategy does not rely exclusively on a paired trailing
      comment that a conforming TOML reserializer may discard. If comments
      remain part of the strategy, exact semantic recovery and future rewrite
      behavior are documented and tested.
- [ ] A regression fixture reproduces the observed Codex app rewrite: top-level
      keys move, unrelated app/plugin settings change, the managed profile stays
      equivalent, and the trailing Meridian marker disappears.
- [ ] `meridian codex doctor` reports the repairable condition separately from
      effective worktree-root access and Git-metadata approval behavior.
- [ ] `docs/HOST_CAPABILITY_CONTRACT.md` documents the recovery boundary and
      makes clear that config repair does not prove session reload or host
      enforcement.
- [ ] Lean and Governed generated instructions expose the same bounded recovery
      procedure where they reference Codex worktree configuration.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Permission-profile parsing, planning, repair, backup, and doctor diagnostics. |
| `tests/test_meridian_cli.py` | Semantic-equivalence, conflicting-profile, rewrite, and idempotence fixtures. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Host activation and safe recovery contract. |
| `templates/workflows/lean-delivery/` | Lean recovery instructions and managed delivery. |
| `templates/workflows/governed-sdd/` | Governed recovery instructions and managed delivery. |
| `migrations/`, `release-baselines/` | Delivery to existing consumers when managed policy changes. |

## 🧩 Technical Context

Task 054 introduced a managed comment block around the user-level Codex
permission profile. A later Codex app update rewrote `~/.codex/config.toml`,
preserved the effective `default_permissions`, profile inheritance, and shared
worktree root, but removed the trailing `# MERIDIAN:END worktree-permissions`
comment while also updating unrelated application settings. Meridian correctly
refused to overwrite an apparently incomplete block, but the task lifecycle was
blocked until the missing comment was restored manually.

The permanent solution must treat semantic equivalence as evidence for a
bounded repair, not as permission to claim host activation. Codex permission
profiles and their configuration serialization are host-owned surfaces;
Meridian owns only its declared profile shape and repair operation.

## 🔨 Suggested Implementation

1. Parse the effective TOML profile independently from comment ownership and
   compare it against one exact normalized expected profile.
2. Add a repair plan/state for exact semantic matches with damaged metadata,
   retaining fail-closed diagnostics for every divergent shape.
3. Cover observed and adversarial rewrites, then update the host contract and
   managed instructions through the normal migration path.

## ⚠️ Constraints and Considerations

- Do not auto-repair during project open, initialization, upgrade, doctor, or
  `--check`; only explicit `--apply` may write user configuration.
- Do not adopt a foreign profile merely because it uses the expected name.
- Do not broaden filesystem or network access and do not select full access.
- Do not interpret successful repair as proof that the current session loaded
  the profile; a fresh-session probe remains required.
- Do not persist machine-specific absolute paths in repository artifacts or
  fixtures; use temporary or symbolic example roots.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: a Codex-managed TOML rewrite cannot permanently strand an
otherwise identical Meridian permission profile, while divergent profiles
remain protected from automatic adoption or overwrite.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Codex desktop / trusted project | equivalent profile can become blocked after app rewrite | explicit bounded repair available | Exact semantic match, explicit `--apply`, successful atomic write, and fresh session. | Print the conflicting fields and require manual reconciliation. |
| Codex CLI / trusted project | same user config may be blocked by damaged comments | explicit bounded repair available | Supported permission-profile version and exact semantic match. | Retain ordinary approval prompts without widening access. |
| Host-neutral CLI | comment pairing is treated as sole ownership evidence | semantic repair is deterministic and tested | Parser and adversarial fixtures pass. | Fail closed on ambiguity or divergence. |

## 🔗 Dependencies

- **Depends on**: 054
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/062-make-codex-profile-repair-resilient.md)"$'\n\nExecute this task in the current project.'
```
