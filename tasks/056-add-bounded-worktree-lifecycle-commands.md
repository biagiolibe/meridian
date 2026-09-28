# Task 056 — Add bounded worktree lifecycle commands

> **ID**: `056`
> **Category**: Architecture / Host Integration
> **Priority**: 🔴 P1
> **Estimate**: ~8–12h
> **Assigned to**: unassigned
> **Session**: 2026-09-27 command-approval alignment design

## 🎯 Objective

Replace approval-prone raw Git mutations in the isolated-worktree lifecycle
with a host-neutral `meridian worktree` namespace whose arguments, repository,
paths, state transitions, and recovery behavior are validated before Git
metadata is changed. Claude Code, Codex, and direct terminal users must invoke
the same lifecycle commands; host-specific commands remain adapters for host
configuration and capability diagnosis only.

Project execpolicy rules may then allow the exact Meridian command prefixes
without allowing generic `git worktree`, merge, branch deletion, or other
arbitrary Git mutations outside the sandbox. Routine task preparation,
integration, and verified cleanup should complete without a manual command
approval while destructive exceptional recovery remains explicit.

## 📋 Acceptance Criteria

- [ ] The CLI exposes one stable lifecycle namespace with commands equivalent
      to `meridian worktree path`, `meridian worktree prepare`,
      `meridian worktree check`,
      `meridian worktree integrate stage|finalize|abort`, and
      `meridian worktree cleanup`. Command names, positional arguments, exit
      codes, and machine-readable outputs are documented and tested.
- [ ] `meridian codex worktree-path` remains a documented deprecated alias for
      `meridian worktree path` for one migration window. New templates,
      migrations, handoffs, and host instructions use only the host-neutral
      form, and equivalence tests prevent the alias from diverging.
- [ ] Every mutating command resolves the canonical Meridian project from the
      current working directory, verifies that any supplied `--project` names
      that same project, and rejects arbitrary repositories, paths, symlink
      escapes, unknown task IDs, non-canonical task branches, and worktree
      roots that differ from the effective configured root.
- [ ] `prepare` reuses Task 054's repository identity, namespaced path
      derivation, and collision detection, and consumes the project-selected
      identity resolver implemented by Task 063. Its mandatory preflight is
      host-neutral; a Codex or Claude capability probe is supplementary and
      cannot redefine lifecycle validity. It creates exactly one
      branch/worktree pair from the permitted base commit and writes the
      required handoff identity without silently repairing partial state.
- [ ] Lifecycle orchestration runs `prepare` before it creates an implementer,
      reviewer, or remediation worker session. The coordinator passes the
      returned absolute worktree path and branch as durable worker-launch
      inputs; a worker must not derive, choose, or create a second checkout.
- [ ] Every worker starts with its effective working directory bound to the
      exact existing worktree returned by `prepare` and immediately runs the
      read-only `check` before reading implementation files, computing a diff,
      changing task state, or writing files. `check` rejects the primary
      checkout and every other linked worktree even when the expected branch
      exists there or the checkout is clean.
- [ ] Claude Code orchestration does not use Desktop automatic session
      isolation, CLI `--worktree`, an isolated-worktree subagent option, or any
      equivalent host facility that creates another checkout after Meridian
      preparation. A host-created checkout is acceptable only when its
      registered real path, configured root, repository identity, canonical
      task leaf, branch, and HEAD already equal the `prepare` result; otherwise
      the lifecycle is `BLOCKED` and preserves both checkouts.
- [ ] If a host cannot launch or attach a fresh worker session with the exact
      prepared directory as its effective workspace, orchestration returns
      `BLOCKED` before implementation or review. It never falls back to
      `<project>/.claude/worktrees/`, the primary checkout, a sibling checkout,
      a new branch, or a host-selected path.
- [ ] `check` is read-only and reports branch, worktree, Git common directory,
      canonical prepared path, effective worker path, base commit, task commit,
      cleanliness, handoff consistency, active integration state, and the next
      permitted lifecycle action. Its machine-readable result distinguishes
      `wrong-worktree` from branch, HEAD, root, handoff, and cleanliness
      failures.
- [ ] `integrate stage` acquires the Task 051 integration lease atomically,
      verifies the accepted handoff and recorded commits, checks a clean
      primary checkout on `main`, and performs only the prescribed
      `git merge --no-ff --no-commit`. Conflicts trigger a clean abort and do
      not create a merge commit.
- [ ] `integrate stage` returns Task 055's deterministic validation decision
      (`REUSE`, `BOUNDED`, `FULL`, or `BLOCKED`) and the candidate tree identity.
      It never executes task-provided, project-provided, shell, validation, or
      hook commands while running under an execpolicy `allow` rule.
- [ ] Required smoke or full validation runs separately inside the ordinary
      sandbox and records evidence bound to the staged candidate tree.
      `integrate finalize` creates the merge commit only when Task 055 evidence
      for that exact candidate is sufficient. Stale, missing, mismatched, or
      failed evidence is `BLOCKED`.
- [ ] `integrate abort` aborts only a Meridian-owned staged integration whose
      lease and merge state match the requested task. It releases that lease
      after a clean abort and preserves the task branch and worktree.
- [ ] `cleanup` removes the task worktree and then deletes the non-force local
      branch only after it proves that the recorded task commit is integrated,
      the required push is complete when applicable, no integration lease or
      merge is active, and both relevant checkouts are clean. Abandoned-state,
      stale-lease, force-delete, and mismatch cleanup remain unavailable or
      require explicit developer authorization outside the allowlisted path.
- [ ] Mutating commands are idempotent where repeating a completed operation is
      safe and otherwise fail closed with a diagnostic naming the retained
      state and recovery command. Interruptions between Git operations have a
      deterministic inspect/abort/resume path.
- [ ] The canonical lifecycle executable form is defined by the host-neutral
      namespace and verified without reading host configuration. `meridian
      codex doctor` additionally checks whether Codex can execute the exact
      bounded prefixes without approval. Project instructions invoke the same
      argv form; source-checkout, installed CLI, Claude plugin, and Codex
      project contexts must not document a form that silently misses their
      applicable command policy.
- [ ] Lean Delivery and Governed SDD install equivalent project rules that
      allow only the bounded lifecycle prefixes and the established safe
      read-only/status commands. Raw `git worktree add|remove|prune`, raw
      integration merge/finalization, forced branch deletion, reset, rebase,
      cherry-pick, and force-push remain prompt-controlled or forbidden as
      appropriate.
- [ ] `codex execpolicy check` decision-table tests prove that every canonical
      lifecycle invocation is `allow`, malformed or non-canonical forms do not
      inherit the allow decision, cleanup escape hatches remain prompt or
      forbidden, and the most restrictive existing Git rules still win.
- [ ] Real temporary-repository tests cover prepare/check, unchanged-base
      evidence reuse, advanced-main bounded/full decisions, conflict abort,
      stale evidence, interrupted staged integration, finalize, verified
      cleanup, cross-repository/path attacks, symlink escapes, and two tasks
      integrating serially without raw Git approval rules.
- [ ] Worker-routing tests prepare one canonical task worktree, then simulate a
      worker starting in the primary checkout, a sibling worktree, and
      `<project>/.claude/worktrees/task-<id>`. Every mismatch fails before task
      reads or writes; a worker rooted at the exact prepared path succeeds and
      implementation and review reuse that same registered checkout
      sequentially.
- [ ] Managed templates, initialization, upgrade migrations, capability
      markers, baselines, host contract, and lifecycle documentation deliver
      the commands and rules consistently to new and existing Lean and
      Governed SDD adopters.
- [ ] A profile-qualified Codex host probe demonstrates the canonical prepare,
      stage/finalize or abort, and cleanup flow without user command approvals;
      filesystem-profile activation, project trust, rule decision, Git result,
      and any remaining network/push approval are recorded separately.
- [ ] A real Claude Code lifecycle probe starts from the primary project,
      prepares the repository-qualified Meridian worktree, launches a fresh
      worker bound to that existing path, and proves that no additional entry
      appears below `.claude/worktrees` or elsewhere. A host that only offers
      automatic new-worktree sessions is recorded as unsupported and returns
      `BLOCKED`, not as a successful advisory integration.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Lifecycle command parser, state machine, path checks, lease ownership, and Git operations. |
| `.codex/rules/meridian.rules` | Meridian repository's exact execpolicy prefixes. |
| `templates/workflows/lean-delivery/.codex/rules/meridian.rules` | Generated Lean command policy. |
| `templates/workflows/governed-sdd/.codex/rules/meridian.rules` | Generated Governed command policy. |
| `PROJECT_WORKFLOW.md`, `AGENTS.md`, `CLAUDE.md` | Local canonical invocation and lifecycle contract. |
| `templates/workflows/lean-delivery/` | Lean preparation, integration, evidence, and cleanup instructions. |
| `templates/workflows/governed-sdd/` | Governed implementation, review, integration, and cleanup instructions. |
| `templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md` | Prepare-before-spawn ordering and exact worker-worktree binding. |
| `.claude-plugin/`, `hooks/` | Claude-facing routing or guard surfaces needed to prevent host-created substitute worktrees. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Trust, permission, execpolicy, sandbox, and host-evidence boundary. |
| `tests/test_codex_rules.py` | Canonical and adversarial execpolicy decision table. |
| `tests/test_task_worktree_isolation.py` | Real Git lifecycle and interruption scenarios. |
| `tests/test_meridian_cli.py` | CLI parsing, repository/path validation, migration, and diagnostics. |
| `migrations/`, `templates/` | Managed delivery to existing and new adopters. |

## 🧩 Technical Context

- **Current filesystem state**: Task 054's `meridian-worktrees` permission
  profile permits ordinary file writes below the shared worktree root after a
  new Codex session loads it.
- **Current command policy**: status, add, commit, push, and worktree listing
  have allow rules; raw `git worktree add|remove|prune` are `prompt`; the
  required `git merge --no-ff --no-commit` has no matching allow rule.
- **Security gap**: changing those raw Git prefixes to `allow` would let an
  agent choose arbitrary repositories, paths, branches, and cleanup targets
  outside Meridian's task invariants. A command allowed outside the sandbox
  must not become a wrapper for arbitrary shell or validation execution.
- **Desired behavior**: the elevated surface is the smallest deterministic
  Meridian state machine. Project code and validation continue to run inside
  the ordinary sandbox; only validated Git metadata transitions use the
  allowlisted lifecycle commands.
- **Observed Claude routing failure**: a Palimpsest `Run lifecycle
  M35-EXEC-001` prepared no bound worker workspace before starting the fresh
  implementation session. Claude Desktop applied its own session isolation and
  registered `<project>/.claude/worktrees/task-m35-exec-001`, while Meridian's
  resolver returned the repository-qualified shared-root path ending in
  `palimpsest/m35-exec-001`. The alternate checkout was clean and on the
  expected branch, but its path and root were non-canonical. This proves that
  instructions to "use the dedicated worktree" are insufficient without a
  prepare-before-spawn contract and worker-side path verification.

## 🔨 Suggested Implementation

1. Extract side-effect-free lifecycle inspection and transition planning from
   the existing Task 051, 054, and 055 helpers.
2. Define durable staged-integration state bound to repository identity, task,
   lease owner, base/task/current-main commits, candidate tree, and validation
   decision. Specify recovery before adding mutations.
3. Implement prepare/check first, including the machine-readable launch
   contract and wrong-worktree diagnostics. Execute Git with argument arrays,
   never shell strings, and reject unknown or repeated options rather than
   forwarding them.
4. Update lifecycle orchestration so preparation completes before delegation,
   every worker is launched against the returned existing directory, and the
   worker proves that binding with `check` before substantive work.
5. Add exact Codex project rules for the host-neutral executable and
   subcommands, and route Claude instructions through the same CLI surface.
   Keep raw Git mutation policy restrictive and verify rule precedence with
   the real Codex execpolicy evaluator when available.
6. Update both workflow modes and ship the managed changes through the normal
   migration/capability-baseline mechanism.
7. Record static, real-Git, actual Codex activation, and actual Claude
   existing-worktree binding evidence separately.

## ⚠️ Constraints and Considerations

- Do not allow a generic `meridian worktree` prefix if it also matches future,
  unknown, diagnostic, or escape-hatch subcommands. Allow exact action prefixes.
- Do not forward unparsed arguments to Git or accept arbitrary validation,
  hook, shell, commit-message, project, worktree, or lock paths.
- Do not run project-controlled code outside the sandbox merely because a
  lifecycle command needs protected Git metadata access.
- Do not treat an execpolicy `allow` decision as filesystem permission,
  project trust, command success, or host activation evidence.
- Do not auto-remove stale leases, abandoned branches, unintegrated worktrees,
  or remote branches.
- Do not move, rename, delete, or silently adopt a host-created substitute
  worktree when its path differs from the canonical prepared path. Report both
  paths and retain state for explicit recovery.
- Do not treat a fresh context as requiring a fresh Git worktree. Implementer,
  reviewer, and remediation contexts are distinct, but reuse one task worktree
  sequentially under the one-writer rule.
- Keep push/network behavior separate from local Git lifecycle authorization.
- Preserve Task 055's proportional validation policy, Task 054's
  repository-qualified shared worktree root, and Task 063's implemented task
  identity contract.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED
Policy outcome: every supported agent uses one Meridian task-worktree Git
lifecycle. Codex can execute its bounded transitions without repeated command
approvals while arbitrary Git and shell mutations remain outside the
allowlisted surface; Claude uses its own host permission mechanism without a
second lifecycle vocabulary.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Codex desktop / trusted project / active Meridian permission profile and project rules | advisory | enforced | Canonical Meridian executable resolves on PATH, project trust and permission profile are active, migrated rules load at startup, and the lifecycle host probe passes. | Report `approval-required` or `blocked`; retain raw Git prompts and all task state. |
| Codex CLI / trusted project / active Meridian permission profile and project rules | advisory | enforced | Supported CLI version loads the same project rule and the real execpolicy/lifecycle probe passes. | Use interactive approvals; do not widen raw Git rules. |
| Claude Code plugin session | automatic session worktrees can bypass the Meridian path | enforced by CLI and verified existing-worktree session binding; host authorization remains host-owned | The bounded CLI commands are installed, orchestration prepares before spawning, the host can launch a fresh context in the returned existing directory, and worker `check` passes. | Return `BLOCKED` when Claude can only create a new automatic worktree; never accept `.claude/worktrees` as a substitute unless it is the exact canonical prepared path. |
| Host-neutral Meridian CLI | unverified | enforced | Real-Git state-machine tests pass independently of any host approval system. | Fail closed and print the retained/recovery state. |

Evidence plan:
- Static: parser, state-transition, argument-rejection, worker-routing,
  rule decision-table, migration, and marker tests.
- Host execution: real temporary repositories, one supported Codex desktop/CLI
  lifecycle probe, and one Claude prepare-before-spawn/existing-worktree probe.
- Manual activation: record executable resolution, prepared and effective
  worker paths, Git registration, project trust, permission-profile selection,
  rule loading after restart, and remaining push/network behavior.

Completion evidence:
- Codex desktop / trusted project / active Meridian permission profile and project rules: unverified until the named end-to-end probe is recorded.
- Codex CLI / trusted project / active Meridian permission profile and project rules: unverified until the named end-to-end probe is recorded.
- Claude Code plugin session: unverified until the named existing-worktree
  binding probe completes without creating a substitute checkout.
- Host-neutral Meridian CLI: unverified until the real-Git lifecycle suite passes.

## 🔗 Dependencies

- **Depends on**: 054, 055, 059, 063
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/056-add-bounded-worktree-lifecycle-commands.md)"$'\n\nExecute this task in the current project.'
```
