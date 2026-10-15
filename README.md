# Meridian

**Two deliberate workflows for building software with AI coding agents: Lean Delivery and Governed SDD.**

Meridian turns a project plan into small, explicit, verifiable tasks that agents can implement without rediscovering the project on every session. It provides templates, Claude Code commands, a queue briefing hook, and companion skills for a delivery process proportionate to risk.

It is deliberately stack-agnostic: Meridian defines the process; each project supplies its own architecture, invariants, and validation commands.

> **Project status:** the stable compatibility promise starts at 1.3.0. See the [public surface classification](docs/PUBLIC_SURFACE.md) and [versioning and deprecation rules](CONTRIBUTING.md#versioning-and-deprecation).

Start with the [adopter quick start](docs/QUICKSTART.md): install a pinned release,
initialize a project, and close your first Lean Delivery task.

## Why Meridian?

AI agents are fast, but a prompt alone is a weak engineering contract. A request such as “add authentication” leaves an agent to infer the architecture, scope, constraints, acceptance criteria, and validation strategy.

Meridian makes the necessary decisions explicit. Lean Delivery tasks record a
bounded objective, acceptance criteria, context, and validation; Governed SDD
adds authority, expected code surface, non-goals, dependencies, and review
policy. The result is less rediscovery, safer handoffs, and a useful record
after the chat is gone.

## Choose a workflow mode

| Mode | Best for | Task lifecycle |
|---|---|---|
| **Lean Delivery** | Small projects, POCs, demos, experiments, and reversible low-risk work. | `[ ]` → `[/]` → `[x]` |
| **Governed SDD** | Long-running projects or changes that need architecture decisions, dependency gates, and controlled integration. | `QUEUED` → `IN_PROGRESS` → `READY_FOR_REVIEW` → `ACCEPTED` |

Each initialized project contains a `PROJECT_WORKFLOW.md` mode lock. Its local
workflow documents take precedence over global or remembered agent
instructions. An agent must not import Lean Delivery lifecycle rules into a
Governed SDD project, or governed branches and review gates into Lean Delivery.
If the local workflow documents cannot be read or conflict, agents stop with
`BLOCKED` before changing repository or Git state.

**SDD means spec-driven development:** before implementation, an agent receives an explicit, durable specification of the change—its authority, scope, constraints, acceptance criteria, and validation. In Meridian, a task file is that specification.

In governed SDD, low-risk documentation, mechanical configuration, scaffolding, and narrowly scoped tests may use the direct `QUEUED` → `IN_PROGRESS` → `ACCEPTED` path. Changes to domain rules, public APIs, dependencies, state transitions, persistence, deterministic behavior, security, or unresolved design decisions require review.

Only an `ACCEPTED` task satisfies another task's dependency.

## Platform support

Supported means Meridian's repository checks and full test suite run in CI on
that OS. Best-effort features depend on a local host, terminal, or desktop
integration that CI does not exercise end to end. Unsupported platforms and
features have no support commitment.

| Platform or requirement | macOS | Linux | Windows |
|---|---|---|---|
| Meridian CLI and workflow tooling | Supported (`macos-latest` CI) | Supported (`ubuntu-latest` CI) | Unsupported |
| Python 3.12 or later | Supported (3.12); best-effort (newer versions) | Supported (3.12); best-effort (newer versions) | Unsupported |
| Git on `PATH`, including linked worktrees | Supported (runner-provided Git) | Supported (runner-provided Git) | Unsupported |
| Claude Code host integration | Best-effort (local installation required) | Best-effort (local installation required) | Unsupported |
| Codex host integration | Best-effort (local installation and effective worktree access required) | Best-effort (local installation and effective worktree access required) | Unsupported |
| Console snapshot (`--once`) and interactive view | Supported (interactive view requires a TTY) | Supported (interactive view requires a TTY) | Unsupported |
| Console copy to clipboard | Best-effort (`pbcopy`) | Best-effort (`wl-copy` or `xclip`) | Unsupported |
| Console agent launch | Best-effort (iTerm2 and `osascript` required) | Unsupported | Unsupported |

Both CI jobs run `python3 scripts/check_repository.py` and
`python3 scripts/run_tests.py --parallel` with Python 3.12. Newer Python
versions are best-effort until tested in CI. Git uses the version supplied by
each runner; no separate minimum Git version is certified. Tests that require
unavailable local tools report their own named skips. CI does not validate
live Claude Code or Codex sessions, desktop clipboard access, or an actual
iTerm2 agent launch. The console keeps the directive available for manual copy
when clipboard or launch integration is unavailable.

## Quick start with Claude Code

First install and authenticate Claude Code, and ensure Python 3.12+ and Git
are on its shell PATH. See the [shared prerequisites](docs/QUICKSTART.md#prerequisites).


Meridian is distributed as a GitHub-hosted Claude Code marketplace. Pin it to a
release tag so you stay on a known release until you choose to move. Replace
`<version>` with a release listed on the
[Releases page](https://github.com/biagiolibe/meridian/releases), for example
`1.2.15`:

```text
/plugin marketplace add biagiolibe/meridian#v<version>
/plugin install meridian@meridian
```

The plugin cache holds the tagged tree, so `${CLAUDE_PLUGIN_ROOT}/bin/meridian`
is the CLI for that release. Nothing moves the pin automatically.

Then open the project you want to initialize and run:

```text
/meridian-init
```

For a first project, follow the [adopter quick start](docs/QUICKSTART.md).
Console details are in [Agent operations](docs/AGENT_OPERATIONS.md#project-console).

### Updating Meridian

Update the framework before the project: a project manifest can only be read by
a CLI at least as new as its `protocolVersion`.

To upgrade a project in one guided run, see
[How to upgrade a project](docs/HOW_TO_UPGRADE.md); the steps below are the
manual procedure it wraps.

1. Read the release notes on the Releases page or in `CHANGELOG.md`. The first
   line of each section says whether the release is CLI-only or
   template-changing.
   Optionally run `meridian self-check --check-latest` to compare the installed
   framework with the latest public GitHub Release. This is the only Meridian
   command that performs an update-discovery network request; it uses no
   credentials and writes no cache or state. Exit `0` means `UP_TO_DATE`, exit
   `10` means `UPDATE_AVAILABLE`, and exit `11` means `UNKNOWN` because the
   request was offline, rate-limited, or malformed. These informational results
   never block `upgrade` or other Meridian work.
2. Move the pin. Re-adding a marketplace at a different ref is refused, and
   removing a marketplace also uninstalls its plugins, so reinstall afterwards:

   ```text
   /plugin marketplace remove meridian
   /plugin marketplace add biagiolibe/meridian#v<new-version>
   /plugin install meridian@meridian
   ```

   If the marketplace was declared in `extraKnownMarketplaces` in user or
   managed settings, adding the new pin can instead fail with
   `Cannot add marketplace "meridian": its source doesn't match its extraKnownMarketplaces entry in user or managed settings`.
   That settings entry still names a different source or ref. Change its `ref`
   to the new tag, or remove the entry, then run `/plugin marketplace update
   meridian` or use the remove, add, and install sequence above. The entry may
   be in user settings or managed settings; a developer cannot change a managed
   entry, so its owner must update or remove it.

   A marketplace added without a pin can instead be refreshed with
   `/plugin marketplace update meridian`.

   To stop moving the pin by hand, set the entry's `ref` to `"stable"` once. The
   `stable` branch is advanced by each release's `publish` to the commit of its
   `v<version>` tag, so later releases need only `/plugin marketplace update
   meridian`. This documentation does not claim that Claude Code refreshes a
   third-party marketplace on its own. Exact tags remain the way to pin a
   version or roll back: set `ref` back to `v<version>`.

   To read the installed plugin version, use `/plugin`, read the `version` and
   `gitCommitSha` recorded for `meridian@meridian` in
   `~/.claude/plugins/installed_plugins.json`, or run `meridian self-check
   --check-latest`, which also prints a `Plugin ref:` line for the `ref` it can
   read from `extraKnownMarketplaces.meridian.source.ref` in user settings
   (`stable`, a current tag, an older tag with its remedy, or `unknown`). It
   never writes settings.
3. From the project, run `meridian upgrade --check`.
4. On a clean plan, apply it in a dedicated branch, validate the project, and
   commit the diff (see [Framework upgrades](#framework-upgrades)). Never
   hand-edit `.meridian/manifest.json`.

Confirm the move by comparing the installed framework version with the
project's `frameworkVersion` in `.meridian/manifest.json` after
`upgrade --apply`, rather than trusting the plugin manager alone.

To confirm the version Claude Code has actively installed, use these checks in
order:

1. In Claude Code, open `/plugin` and inspect the Meridian entry. This most
   directly shows the enabled plugin and its version. The interactive view was
   previously observed in a real user installation; this task rechecked the
   equivalent `claude plugin list` command in that installation.
2. Read `~/.claude/plugins/installed_plugins.json` and find the `version` in
   the `meridian@meridian` record. This identifies the active installed version
   and its install path.
3. Run `meridian self-check --check-latest`. With a successful network lookup,
   its `Installed`, `Latest`, and `Status` lines compare the installed framework
   with the newest release. This task ran the command from the active install;
   its lookup was blocked by DNS, so the `Latest` line was not re-verified here.

The plugin cache can retain older version folders. Those folders are not proof
that an older version is active; use the installed-plugin record or the plugin
list instead.

### Migrating from `meridian-local`

Earlier instructions registered a local clone as the `meridian-local`
marketplace. The marketplace is now named `meridian`, so the install id changes
from `meridian@meridian-local` to `meridian@meridian`. Migrate once:

```text
/plugin uninstall meridian@meridian-local
/plugin marketplace remove meridian-local
/plugin marketplace add biagiolibe/meridian#v<version>
/plugin install meridian@meridian
```

The migration can leave `~/.claude/plugins/cache/meridian-local/` on disk. It is
not used any more and can be deleted.

### Language behavior

During initialization, choose the language used for agent-developer conversation. Meridian stores that preference in `LANGUAGE_POLICY.md`; agents must keep using it even when an individual prompt is written in another language. The file also establishes an unconditional invariant: every persistent repository artifact—including code, documentation, comments, identifiers, user-facing strings, tests, configuration text, and commit messages—must be in English.

To change the conversation language later, explicitly request the change and update `LANGUAGE_POLICY.md` in the same edit. Prompt language alone never changes the preference.

In Claude Code, the Meridian `UserPromptSubmit` hook reprints a valid configured
conversation language and the repository-English invariant at every prompt. It
is a salience aid, not a policy-enforcement mechanism. In Codex, the generated
project `AGENTS.md` and the Meridian skill load the same project-owned policy;
the language value is never duplicated in host configuration.

When you are ready to scope work, run:

```text
/meridian-task
```

The hook stays silent outside a project containing either `LANGUAGE_POLICY.md`
or `tasks/QUEUE.md`.

## Framework upgrades

Meridian-generated projects lock their installed workflow baseline in
`.meridian/manifest.json`. This makes framework changes deterministic rather
than dependent on a manual prompt.

The manifest tracks three independent version axes:

- `frameworkVersion` is the Meridian release version (the CLI and plugin). It
  moves with every release.
- `workflowBaselineVersion` is the version of the governed template baseline a
  project has installed. It is derived from the migrations and moves only when
  a release ships one, so it may lag behind `frameworkVersion`.
- `protocolVersion` is the manifest shape the CLI reads and writes. It moves
  only when an older CLI could not safely read the manifest.

A CLI-only release changes `frameworkVersion` but ships no migration: the
baseline stays where it was, and `upgrade --check` reports no managed-file
changes. A template-changing release adds a migration, which advances
`workflowBaselineVersion` to that release's version and produces the plan that
`upgrade --apply` performs. Each release is recorded in `releases/<version>.json`.

Check an upgrade from the installed Meridian source:

```bash
${MERIDIAN_ROOT}/bin/meridian upgrade --project /path/to/project --check
```

When the plan has no conflicts, apply it in a dedicated branch, validate the
project, and commit the resulting diff:

```bash
${MERIDIAN_ROOT}/bin/meridian upgrade --project /path/to/project --apply
```

The CLI performs a three-way merge between the installed baseline, the local
project file, and the new framework template. It applies no changes when a
managed file conflicts; resolve that bounded conflict in a dedicated upgrade
change and rerun the command. Do not edit `.meridian/manifest.json` or its
baseline snapshots by hand.

For a project created before framework locking was available, use the packaged
baseline that matches its installed Meridian version. For example, a compatible
`1.0.0` Governed SDD project can safely preview its migration with:

```bash
${MERIDIAN_ROOT}/bin/meridian adopt --project /path/to/project \
  --mode governed-sdd --from 1.0.0 --check
```

`adopt --apply` writes the manifest only after a clean plan. It refuses to
guess an unrecorded baseline; add an explicit snapshot before supporting a
different legacy version.

If an established project has intentionally adapted workflow documents, use
capability-aware adoption instead of forcing template merges:

```bash
${MERIDIAN_ROOT}/bin/meridian adopt --project /path/to/project --assisted --check
```

`--mode` and `--from` are detected automatically when unambiguous. The command
recomputes a single `NEXT_ACTION` (`IMPLEMENT_MIGRATION`, `REVIEW_MIGRATION`,
`ADDRESS_REVIEW`, `FINALIZE`, or `BLOCKED`) from the project's detected
capabilities and `.meridian/adoption-review.md` on every run, mapped onto the
CLI's exit codes (`3` for agent work required, `0` when ready to finalize, `2`
when blocked) — so an orchestrator, human, or the packaged Claude Code skill
can drive the whole migration by repeatedly running the same command and
acting on its `NEXT_ACTION`, dispatching the emitted implementer and reviewer
prompts to independent sessions (Task-tool subagents in Claude Code, separate
fresh chats otherwise) without ever copying context between them. Run
`meridian finalize-adoption` only after the reviewer records an unconditional
`APPROVE`; a developer who personally reviewed the migration may pass
`--owner-accepted` instead. See [assisted adoption](commands/meridian-adopt.md).

### Support policy

- **Upgrade window.** Every published release from `v1.1.49` forward upgrades
  to the newest release in a single `upgrade --apply`. `v1.1.49` is the oldest
  release published as a tag, and the test suite proves this path.
- **Skipping releases** is supported; step through intermediate releases only
  if you prefer to.
- **Fixes land only in the newest release.** There are no backport branches; a
  correction ships as a new release.
- **Not supported:** downgrades, manifests whose installed baseline is not
  recorded (use `meridian adopt`), and unreleased `main`.
- **Projects older than `v1.1.49`**, including the packaged `1.0.0` baseline,
  are adopted with `meridian adopt` on a best-effort basis. A pristine `1.0.0`
  project currently adopts with conflicts against the newest release.

## Quick start with Codex

Install a tagged checkout and configure the host using the
[Codex installation path](docs/QUICKSTART.md#install-for-codex). The guide covers
Python/Git prerequisites, initialization from the command instructions,
consented setup, restart and effective access checks, and a first closed task.
There is no `meridian init` CLI subcommand in v1.2.15.

For permission diagnostics, the read guard, and local usage reports, see
[Agent operations](docs/AGENT_OPERATIONS.md).

## How the governed workflow works

```text
Project plan → architecture decisions → atomic task → implementation → independent review → acceptance/integration
                                                     ↖ requested changes ↙
```

The project keeps durable process artifacts close to the code:

```text
PROJECT_WORKFLOW.md             # Lifecycle, precedence, roles, and Git rules
AGENTS.md / CLAUDE.md           # Agent-specific project instructions
LANGUAGE_POLICY.md              # Persistent conversation language and English-only repository text
docs/ARCHITECTURE_DECISIONS.md  # Accepted architecture decisions
docs/CONTEXT_BUDGET_POLICY.md   # Task-first context policy
tasks/QUEUE.md                  # Canonical dependency and status queue
tasks/TASK-NNN.md               # One bounded unit of work
tasks/reviews/TASK-NNN.md       # Reviewer evidence and requested-change handoff
```

### Bounded exploration and durable evidence

For a focused source already named by a task, the worker reads it directly.
For broad or uncertain-yield research, the task instead records a bounded
question and the distilled answer. This preserves a small implementation
context without concealing the investigation from review:

```text
Declared task authority
        │
        ├─ targeted, named source ───────────────→ direct read
        │
        └─ broad or uncertain question
                    │
                    ▼
          bounded isolated exploration
          (question, scope, sources, finding)
                    │
                    ▼
          .meridian/execution-evidence.json
                    │
                    ▼
      completion handoff + ready-check cross-check
```

The worker or host used for the exploration is not normative. Delegating work
does not erase its declared investigation budget, and a completion report is
not accepted as a substitute for durable validation or exploration evidence.

### Task contract

A governed task declares:

- the decision or specification that authorizes it;
- its expected code surface and explicit non-goals;
- dependencies;
- `REQUIRED` or `NOT_REQUIRED` review policy;
- measurable acceptance criteria and validation commands.

The task is the agent’s initial navigation map. It reads its authority and expected code surface first, then widens context only when evidence is insufficient or a blocker requires it.

### Roles and integration

Meridian separates the roles that make a code change from those that accept it:

- The **tech designer** records decisions and creates scoped tasks.
- The **implementer** works on one task in a dedicated branch/worktree and validates it.
- The **reviewer-integrator** independently reviews required-review work in a fresh session, verifies the task branch is a fast-forward descendant of `main`, and integrates only after approval.

If the verdict is `CHANGES_REQUESTED`, the reviewer records prioritized,
file-or-command-backed findings in `tasks/reviews/<TASK-ID>.md`, returns the
task to `IN_PROGRESS`, and creates a local handoff commit. The implementer can
then simply run `Address review <TASK-ID>`: it resolves only the unchecked
findings, records resolution evidence, validates, and opens the next review
attempt. This keeps the chat as a notification channel instead of the system
of record.

### Governed execution evidence

For source/build tasks, the execution-evidence profile is resolved into the
task before implementation. This makes the task—not a separately remembered
policy document—the operational contract for validation, evidence budgets, and
the review handoff.

```text
Create or materially re-scope task
        |
        +-- declare authority, scope, acceptance criteria, budget caps,
        |   and named literal validation commands
        |
        +-- meridian execution contract <TASK-ID> --project .
              records the profile digest and resolved contract in the task
        |
meridian execution preflight <TASK-ID> --project .
        |
        +-- requires a current profile digest, executable task state,
        |   complete task contract, and matching task/queue state
        |
Implement and collect evidence
        |
        +-- meridian execution validate <TASK-ID> <validation-id>
        +-- meridian execution evidence <TASK-ID> diagnostic|expansions --gap <reason>
        +-- meridian execution evidence <TASK-ID> captures --gap <reason>
        |      --criterion <AC-ID> --artifact <absolute-path>
        |
Completion report
        |
meridian execution ready-check <TASK-ID> <report> --project .
        |
        +-- verifies preflight and structured handoff evidence
        |
READY_FOR_REVIEW --> independent review --> APPROVE --> ACCEPTED/integration
                    |                         |
                    +-- CHANGES_REQUESTED ----+--> IN_PROGRESS/remediation
```

The wrapper records validation exit statuses and budgeted evidence in
`.meridian/execution-evidence.json`; task-attempt counters live in
`.meridian/budget.json`. A project upgrades its templates before using these
gates, then backfills only non-terminal tasks with their resolved contracts.

For a fully delegated required-review task, `Run lifecycle <TASK-ID>` adds a
coordination-only agent that starts distinct implementer and reviewer sessions,
loops through the durable review record when changes are requested, and
integrates only after approval and all repository and forge gates. See
[lifecycle orchestration](templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md).

This is a process boundary, not a claim that every project needs bureaucracy. Use Lean Delivery when the work is low-risk and reversible; use stronger gates when a mistake is expensive.

## Documentation

- [Adopter quick start](docs/QUICKSTART.md)
- [Agent operations](docs/AGENT_OPERATIONS.md)
- [Lean Delivery workflow guide](WORKFLOW_GUIDE.md)
- [Lean Delivery workflow template](templates/workflows/lean-delivery/PROJECT_WORKFLOW.md)
- [Governed SDD workflow template](templates/workflows/governed-sdd/PROJECT_WORKFLOW.md)
- [Task template](templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md)
- [Review and integration prompt](templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md)
- [Read-only workflow audit prompt](templates/workflows/governed-sdd/docs/AUDIT_PROMPT_READ_ONLY.md)
- [Governed-SDD operator prompts](templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md)
- [Consumer router-adoption playbook](docs/CONSUMER_ROUTER_ADOPTION_PLAYBOOK.md)
- [Framework upgrade CLI](commands/meridian-upgrade.md)
- [Distribution and update channel design](docs/DISTRIBUTION_AND_UPDATE_DESIGN.md)
- [Capability-marker integrity audit](commands/meridian-audit.md)
- [Consumer profiles and project-owned sections](docs/CONSUMER_PROFILES.md)

## Development and contributions

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository layout, validation,
managed-copy maintenance, and the [release procedure](CONTRIBUTING.md#release-procedure).

## Roadmap

See the [open task queue](tasks/QUEUE.md) and [project plan](PROJECT_PLAN.md)
for current work and delivery status.

## Community and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and follow the
[code of conduct](CODE_OF_CONDUCT.md). Report suspected vulnerabilities privately
using the [security policy](SECURITY.md).

## License

Copyright © 2026 Biagio Liberto. Meridian is available under the [MIT License](LICENSE).
