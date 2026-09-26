# Task 054 — Configure Codex access for isolated task worktrees

> **ID**: `054`
> **Category**: Architecture / Host Integration
> **Priority**: 🔴 P1
> **Estimate**: ~6–8h
> **Assigned to**: unassigned
> **Session**: 2026-09-26 Codex worktree-permission design

## 🎯 Objective

Make the isolated worktrees introduced by Task 051 usable from Codex without a
separate filesystem approval for every edited file. Meridian must place task
worktrees below one user-selected shared root, namespace them by repository,
and provide an explicit, idempotent command that can configure that root in
the user's Codex permission profile.

The project initializer may offer this setup, but it must never modify
`~/.codex/config.toml` silently. Project-scoped command rules and user-scoped
filesystem permissions remain separate controls, and the resulting behavior
must not claim that ordinary worktree write access also grants unrestricted
access to protected Git metadata.

This task is the remaining host-integration prerequisite for the Task 051
worktree contract. No other open Meridian task may start until it is complete
and integrated.

## 📋 Acceptance Criteria

- [ ] Both local and generated workflow contracts derive a task worktree path
      below a configurable shared root using
      `<root>/<remote-host>/<owner>/<repository>/<canonical-task-id>`. A
      repository without a usable remote uses a deterministic local identity
      containing a normalized repository name and a short hash of its
      canonical Git common-directory path.
- [ ] Repository identity, task ID, and final path normalization reject empty,
      traversing, ambiguous, or colliding values. An existing path linked to a
      different Git common directory or task branch is `BLOCKED`; Meridian
      never silently reuses or repairs it.
- [ ] The CLI exposes an idempotent read-only check and an explicit apply
      operation, with an interface equivalent to
      `meridian codex configure --check|--apply --worktree-root <path>`.
      `--check` prints the exact effective state and proposed change without
      writing outside the project.
- [ ] `--apply` updates the user's Codex configuration only after explicit
      invocation. It preserves unrelated keys and comments, performs an atomic
      replacement, creates a recoverable backup before the first changed
      write, and becomes a no-op when the requested configuration is already
      effective.
- [ ] The configurator uses one supported Codex permission model at a time. It
      detects incompatible legacy sandbox settings, managed restrictions,
      malformed TOML, or an unavailable configuration layer and returns a
      diagnostic instead of combining models or overwriting the conflict.
- [ ] The configured profile extends the bounded workspace permission and adds
      only the selected worktree root. It does not authorize the user's home
      directory, a source-code parent containing unrelated repositories, or
      unrestricted filesystem/network access.
- [ ] Initialization detects Codex without making it mandatory, shows the
      proposed user-configuration diff, and offers the explicit apply step.
      Declining or lacking permission leaves repository initialization valid
      and reports the exact manual command required later.
- [ ] Lean Delivery and Governed SDD install the same narrowly scoped Codex
      command policy needed by the worktree lifecycle. The decision table
      distinguishes ordinary file writes from protected `.git` operations and
      does not permit generic `git`, destructive branch deletion, reset,
      rebase, cherry-pick, or force-push.
- [ ] A Codex preflight/doctor reports project trust, active permission model,
      effective worktree-root write access, command-policy availability, and
      Git-metadata behavior separately as `ready`, `approval-required`, or
      `blocked`. Static configuration never counts as proof of effective host
      access.
- [ ] Existing active legacy worktrees remain discoverable and recoverable;
      Meridian does not move or delete them automatically. Newly prepared
      worktrees use the shared namespaced root after activation.
- [ ] Automated tests cover repository namespacing, equal task IDs in different
      repositories, local-repository fallback identity, collision rejection,
      check/apply idempotence, preservation of existing TOML, backup and
      atomic-failure behavior, conflicting configuration models, initializer
      opt-in/decline behavior, and the command-rule decision table.
- [ ] Managed-template changes include the required migration, capability
      markers, and baseline updates so existing adopters receive the new path
      and preflight contract through `meridian upgrade`.
- [ ] A real Codex host probe demonstrates that an ordinary file below the
      configured worktree root can be changed without per-file user approval.
      Protected Git operations are recorded independently and may remain
      approval-reviewed when the narrower command policy cannot authorize them
      safely.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Codex configuration, path derivation, preflight, and lifecycle helpers. |
| `commands/meridian-init.md` | Explicit initialization-time Codex setup offer. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | Meridian's local worktree and host-boundary contract. |
| `templates/workflows/lean-delivery/` | Lean Delivery worktree path, Codex rules, and initialization-facing guidance. |
| `templates/workflows/governed-sdd/` | Governed worktree path, Codex rules, preflight, and lifecycle guidance. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Supported Codex profile, activation facts, and evidence boundary. |
| `tests/test_meridian_cli.py` | Configuration, initialization, migration, and failure-path tests. |
| `tests/test_codex_rules.py` | Exact command-policy decision table for both workflow modes. |
| `tests/test_task_worktree_isolation.py` | Cross-repository namespace and lifecycle evidence. |
| `migrations/`, `templates/` | Managed delivery to new and existing consumers. |

## 🧩 Technical Context

- **Current behavior**: Task 051 creates sibling paths such as
  `<primary-checkout>-task-015`. A Codex session rooted at the primary checkout
  treats that sibling as outside its writable workspace, so editing files such
  as `meridian-task-015/scripts/meridian.py` can trigger approval per file.
- **Current Codex configuration**: project trust and project rules do not make
  an external filesystem path writable. Conversely, adding a writable root
  does not remove Codex's separate protection for `.git` and a linked
  worktree's resolved shared Git directory.
- **Collision risk**: a global `<root>/<task-id>` layout collides when different
  repositories use the same task ID. Repository-qualified paths remove that
  ambiguity without authorizing every repository beside the primary checkout.
- **Desired behavior**: one deliberately authorized root contains isolated,
  repository-qualified worktrees; routine source edits happen without repeated
  user prompts; protected Git actions remain narrowly governed and observable.

## 🔨 Suggested Implementation

1. Add pure helpers for canonical repository identity, safe path components,
   local fallback hashing, and deterministic task-worktree paths.
2. Add `meridian codex configure` with a read-only planner and an explicit,
   atomic apply path. Use a TOML editing mechanism that preserves unknown
   configuration and comments; do not regenerate the entire user file.
3. Add a Codex doctor/preflight that reports filesystem, project trust,
   command-policy, and Git-metadata capabilities as separate facts.
4. Route the initializer through the planner, display the proposed change, and
   execute apply only after explicit user consent.
5. Replace the Task 051 sibling-path convention in local and managed workflow
   documents, distribute the Codex rules to both modes, and migrate existing
   adopters without relocating active worktrees.
6. Add deterministic unit/integration tests and record one profile-qualified
   Codex activation probe before claiming the adapter enforced.

## ⚠️ Constraints and Considerations

- Never write `~/.codex/config.toml` merely because a project is opened,
  inspected, locked, adopted, upgraded, or initialized non-interactively.
- Do not commit machine-specific absolute paths to a project repository.
- Do not mix Codex permission profiles with legacy `sandbox_mode` settings in
  one generated recommendation. Detect and explain the active model.
- Do not interpret `approval_policy = "never"` as additional sandbox access.
- Do not widen an allow rule to generic `git` or use unrestricted/full-access
  mode as the normal solution.
- Backups may contain sensitive user configuration; keep them beside the source
  with restrictive permissions and never copy their contents into task logs.
- Repository artifacts and generated configuration descriptions are English.

## Host impact

Classification: REQUIRED
Policy outcome: Codex can edit ordinary files in Meridian-managed task
worktrees without per-file user approval while retaining bounded filesystem
and Git protections.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Codex desktop / trusted project / selected user permission profile | advisory | enforced | The user explicitly applies the proposed profile, starts a new session, and the host accepts the selected worktree root. | Report `approval-required` or `blocked`; do not create or edit the task worktree. |
| Codex CLI / trusted project / selected user permission profile | unverified | enforced | The CLI version supports the selected permission model and the user explicitly applies and selects it. | Print the manual configuration and retain normal approval prompts. |
| Claude Code plugin session | advisory | advisory | The shared worktree path contract is installed; Codex user configuration is not used. | Continue using Claude's own permission mechanism without claiming Codex parity. |

Evidence plan:
- Static: path, TOML-preservation, initialization, migration, and command-policy decision-table tests.
- Host execution: create or select a task worktree under the configured root and modify an ordinary file without a user approval prompt; probe Git metadata separately.
- Manual activation: record configuration-layer selection, project trust, session restart, and the host's effective permission status.

Completion evidence:
- Codex desktop / trusted project / selected user permission profile: unverified until the named host probe is recorded.
- Codex CLI / trusted project / selected user permission profile: unverified until the named host probe is recorded.
- Claude Code plugin session: retained advisory; no enforcement claim is introduced.

## 🔗 Dependencies

- **Depends on**: 055
- **Blocks**: 015, 039, 046, 047, 053, and transitively every other open task

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/054-configure-codex-worktree-access.md)"$'\n\nExecute this task in the current project.'
```
