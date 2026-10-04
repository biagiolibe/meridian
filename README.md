# Meridian

**Two deliberate workflows for building software with AI coding agents: Lean Delivery and Governed SDD.**

Meridian turns a project plan into small, explicit, verifiable tasks that agents can implement without rediscovering the project on every session. It provides templates, Claude Code commands, a queue briefing hook, and companion skills for a delivery process proportionate to risk.

It is deliberately stack-agnostic: Meridian defines the process; each project supplies its own architecture, invariants, and validation commands.

> **Project status:** early-stage / experimental. The workflow is usable today, but its public API and templates may evolve before a stable release.

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

## Quick start with Claude Code

Meridian is distributed as a GitHub-hosted Claude Code marketplace. Pin it to a
release tag so you stay on a known release until you choose to move. Replace
`<version>` with a release listed on the
[Releases page](https://github.com/biagiolibe/meridian/releases), for example
`1.2.0`:

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

### Project console

From any project that contains Meridian's queue and task records, launch the
read-only interactive project console with:

```text
meridian console
```

It reads the current project's queue, open task details, dependencies, Git
summary, worktrees, and next permitted directives. Its heading and `--once`
snapshot identify the running Meridian version and framework root, so an
installed release is distinguishable from a repository checkout. The view
refreshes local state every two seconds and never writes project files. Use `--project
/path/to/project` to inspect another project and `--interval 5` to change the
refresh interval (between 0.2 and 60 seconds).

The console supports both `LEAN_DELIVERY` and `GOVERNED_SDD` projects, selected
from the mode lock in `PROJECT_WORKFLOW.md`. Because lifecycle edits are
committed on each task branch, it reads a task's queue row, record, handoff,
and review record from that branch with read-only Git commands and shows the
effective state with its source. Disagreements the lifecycle does not produce
appear as `MISMATCH` with no launch directive.

For active tasks, the detail pane and `--once` output also show wall-clock
cycle time from canonical worktree preparation, last activity, and the ordered
lifecycle gates still pending. Cycle time can include idle or waiting periods;
it is not active-agent time, an estimate, or an ETA. Legacy or unreadable
timing data is shown as unavailable without preventing use of the console.

A task stays listed after `meridian worktree integrate stage` marks its queue
row done (`[x]` in Lean Delivery, `ACCEPTED` in Governed SDD), because
candidate validation, finalize, the `main` push, and cleanup remain. While its
canonical worktree is registered, the console shows it as `CLOSING` (a derived,
display-only state; the queue and plan keep their real status and nothing is
written), with the `closure-status` step and resume action, cycle time, and the
progress phase (candidate validation, push pending, cleanup pending). It is
never ready, offers no launch directive, and disappears once cleanup removes the
worktree. A transient lifecycle read failure shows progress as `unavailable`.
In Governed SDD a task waiting for approval shows its cycle time and a
`review pending` phase, and a reserved task worktree derives `IN_PROGRESS` or
`READY_FOR_REVIEW` from the task record because task branches do not edit the
queue.

For an eligible directive, `c` (or `[copy]`) keeps the copy-to-clipboard
fallback. On macOS with iTerm2, press `l` to open an isolated launch panel.
It shows the task, directive, project, agent choices, and safely discovered
configured model and effort defaults; press `1` for Claude Code or `2` for
Codex to revalidate and start that agent immediately, or `Esc` to cancel. The
shown defaults are informative and do not override agent configuration. The first launch may
cause macOS to ask permission for the terminal to automate iTerm2. Each launch
splits the console's current pane again, so repeated launches reduce the space
available to existing panes. Launching starts an agent that may modify the
project and counts as the developer's assignment of that task. The console does
not prepare worktrees: the permitted directive does so. If iTerm2, `osascript`,
the selected executable, or the console's iTerm2 session is unavailable,
the console reports the reason and `[copy]` remains available.

An ordinary `IN_PROGRESS` task offers **Resume** with the exact
`Proceed with <TASK-ID>` directive shown by `[copy]`. Resume is not a liveness
check: the console cannot tell whether another agent is still active, so it
requires an explicit warning confirmation before the agent choice. If the task
worktree has uncommitted changes, it requires a second, distinct confirmation.
The console reloads task state immediately before launch and refuses to proceed
if the directive or lifecycle changed. Closing tasks keep their lifecycle
resume command and never offer implementation Resume.

Repeating `Proceed with` is safe for an interrupted task: worktree preparation
selects the existing canonical branch and worktree, preserves its original
`started_at`, and does not create a second worktree. Resume still runs from the
primary checkout so the normal preparation and worktree checks remain in force.

The command is part of the tagged Meridian tree. Claude Code adopters receive
it through `${CLAUDE_PLUGIN_ROOT}/bin/meridian`; Codex adopters run the
`bin/meridian` launcher from their tagged checkout with `MERIDIAN_ROOT` pointing
at that checkout. No project-local copy, Python package, network service, or
background process is required.

Choose `lean-delivery` for lightweight delivery or `governed-sdd` for controlled integration. `classic` remains a backwards-compatible alias for `lean-delivery`. The initializer creates the relevant planning, design, queue, task, and agent-instruction files in the target project. It does not overwrite existing workflow documents without showing a diff and obtaining a migration decision.

### Updating Meridian

Update the framework before the project: a project manifest can only be read by
a CLI at least as new as its `protocolVersion`.

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

Generated Lean Delivery and Governed-SDD projects include `AGENTS.md` and
`PROJECT_WORKFLOW.md`. Codex also needs one consented machine-level filesystem
setup for task worktrees.

For reusable Meridian operations across projects, install Meridian from a tagged
checkout. The tag pins the release; nothing moves it for you.

```bash
git clone --branch v<version> https://github.com/biagiolibe/meridian ~/meridian
export MERIDIAN_ROOT=~/meridian   # add to your shell profile
export PATH="$MERIDIAN_ROOT/bin:$PATH"
```

Codex scans `$HOME/.agents/skills` for user skills and follows these symlinks
(verified with Codex CLI 0.159.2; see
[`docs/HOST_CAPABILITY_CONTRACT.md`](docs/HOST_CAPABILITY_CONTRACT.md)). Restart
Codex after linking. `bin/meridian` needs Python 3.11 or later on the `PATH` of
the shell Codex uses; with an older `python3` the launcher fails on
`import tomllib`. An older `~/.codex/skills` copy is also discovered, so remove
a stale one yourself rather than expecting Meridian to.

Have Meridian review and, after confirmation, create the skill links:

```bash
meridian codex doctor  # read-only permission-profile, skill-link, and MERIDIAN_ROOT check
meridian setup --check
meridian setup --apply
```

`meridian codex doctor` reports the current `permission-model`,
`profile-ownership`, `project-trust`, `command-policy`,
`claude-project-allowlist`, `lifecycle-command-policy`, `archive-rename-policy`,
`inspection-command-policy`, `validation-command-policy`, `worktree-root-write`,
`git-metadata`, `skill-links`, and `MERIDIAN_ROOT` states. Use it to inspect the machine
profile before allowing `setup --apply`; it does not modify the profile or
links.

To update, read the release notes, then fetch and move the pin before touching
any project:

```bash
git -C "$MERIDIAN_ROOT" fetch --tags
git -C "$MERIDIAN_ROOT" checkout v<new-version>
meridian upgrade --check   # from the project; apply with --apply on a dedicated branch
```

The skill symlinks follow the checkout, so no relinking is needed. Meridian does
not publish tags or move an adopter automatically.

Then review and apply the worktree, Codex, and project-local Claude Code setup
once, and restart the applicable host:

```bash
meridian setup --check
meridian setup --apply
```

The default root is `~/.meridian/worktrees`; a custom root is stored in the
versioned user configuration. With explicit `setup --apply`, Meridian also
adds its bounded command allowlist to the ignored
`.claude/settings.local.json` for the selected project (the current directory
by default, or `--project <path>`). It never writes that allowlist during
`setup --check`; `codex doctor` reports whether the project still needs it.
Its execution entries run whatever a task's `## Validation` declares, so review
declared commands in the task file rather than at the permission prompt.
The same apply adds `permissions.deny` prefix rules for the actions `Proceed
with` never authorizes: force and mirror pushes, remote ref deletion, `git tag`,
`git rebase`, `git reset --hard`, `git cherry-pick`, `git branch -D`, and
`git worktree remove --force`. Your own entries are kept, and plain pushes of
`main` and the task branch and `git branch -d` stay unblocked. These rules are
defense in depth: a reworded command can evade a prefix rule, and the managed
denial text remains in force. `setup` prints the same note.
For a new project, run `meridian init` (or `/meridian-init`) and lifecycle
commands resolve this root automatically. For an existing project, use
`meridian upgrade --check` and the consented `--apply` to receive current
workflow instructions. Existing worktrees stay in their old root; finish them
there and pass `--worktree-root <old-root>` to their final cleanup.

Then invoke the skill explicitly in Codex:

```text
$meridian-lean-delivery
# or
$meridian-governed-sdd
```

The selected skill supports its workflow without replacing project-specific rules. Lean Delivery keeps a lightweight explicit task-and-verification contract; Governed SDD adds architectural authority, dependency gates, formal review, and controlled integration.

### Codex command approvals in Governed SDD

After upgrading a Governed-SDD project, Meridian manages
`.codex/rules/meridian.rules`. It allows the workflow's routine Git commands
and narrow Meridian read-only or validation commands, forbids force-push
forms, and leaves all other commands to Codex's normal approval flow. Lean
Delivery projects do not receive this file.

Codex reads the project-local rules only after its `.codex` layer is trusted
in the user-level `~/.codex/config.toml`; Meridian cannot grant that trust, and
an untrusted project silently ignores the file. Inspect the file itself with:

```bash
codex execpolicy check --rules .codex/rules/meridian.rules -- git status
```

Then prove activation manually in a trusted Governed-SDD session: an allowed
command that previously prompted must run without an approval prompt. Project
rules combine with `~/.codex/rules/default.rules`, with the most restrictive
matching decision winning. `git -C <path> ...` cannot be covered by a prefix
rule, so use the execution tool's working-directory parameter instead.

Issue one command per execution call. In a trusted-project probe with Codex CLI
0.155.1, `git status && git diff --check` ran without a prompt and a chain
containing `git push --force` was refused, but `git status && git rebase main`
also ran without a prompt. Do not rely on later chain segments being evaluated.
The offline checker evaluates argument vectors rather than shell syntax.

### Codex large-file read guard in Governed SDD

Governed-SDD upgrades also manage `.codex/hooks.json`. After reviewing the
hook with `/hooks`, Codex invokes `meridian hook read-guard --host codex`
before Bash commands. It blocks recognised `cat`, `sed -n`, bounded
`head`/`tail`, and `nl | sed` reads when their combined effective output from
large files exceeds `Read-guard threshold` (400 lines by default). It does not
parse arbitrary shell, scripts, substitutions, heredocs, `awk`, or `python
-c`; those forms are allowed rather than falsely blocked.

Confirm activation in a trusted project by attempting `cat` on a file over the
threshold: Codex must deny it before execution. Use `rg -n` then ranged
`sed -n`, or `meridian context authority <TASK-ID>` / `meridian adr show
<ADR-ID>` for bounded source material. Declare a necessary file in task
Authority or raise `Read-guard threshold` only when the larger read is needed.

### Local session token usage

`meridian usage report --format text` summarizes local Codex and Claude Code
session counters without reading or exposing message content. Filter a host,
project name, or date with `--host`, `--project`, and `--since`; add
`--breakdown` to identify the call where input grew most. The command is
read-only and local: it prints only timestamps, project directory names, model
metadata when recorded, and aggregate counters—not prompts, tool arguments,
file contents, or full paths. For both hosts `input` is the total input of a
call including cached input (Claude Code: `input_tokens` plus cache-read and
cache-creation tokens); `cached` is the cache-read part and `cache_ratio` is
`cached / input`. In JSON, `first_call_input`, `mean_call_input`,
`peak_call_input`, and `cumulative_input` use that total. A Claude Code call
with no usage counters is excluded and counted in `unavailable_calls`. Private host log formats can change; an absent or
unrecognized format reports `unsupported` clearly.

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

## Repository layout

```text
commands/                         Claude Code commands
hooks/                            Queue briefing hook
bin/                              Framework maintenance CLI
capabilities/                     Machine-readable framework capability catalog
docs/                             Architecture, workflow, and operator documentation
migrations/                       Versioned deterministic upgrade records
release-baselines/                Archived release baseline templates
releases/                         Immutable release ledger records
schemas/                          JSON schemas for Meridian records
scripts/                          Repository validation and release tooling
skills/                           Codex and Claude Code workflow skills
tasks/                            Active task records, queue, and handoffs
templates/base/                   Shared stack-agnostic templates
templates/workflows/lean-delivery/ Lean Delivery overlay
templates/workflows/governed-sdd/ Governed-SDD overlay
tests/                            Unit tests
.github/workflows/                GitHub Actions workflows
WORKFLOW_GUIDE.md                 Lean Delivery workflow reference
CONTRIBUTING.md                   Contribution guidance and validation
```

## Documentation

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

Meridian's maintenance commands and test suite support Python 3.11 and later;
CI uses Python 3.11 as the minimum-version baseline.

Meridian’s templates are the product. Before proposing a change, run:

```bash
python3 scripts/check_repository.py
```

For changes to the framework-upgrade mechanism, also run:

```bash
python3 -m unittest discover -s tests -v
```

The check validates JSON metadata, Bash syntax, required repository files, and local Markdown links. Read [CONTRIBUTING.md](CONTRIBUTING.md) for workflow-specific contribution guidance.

### Releases

The maintainer writes the changelog entries and any required migration before
preparing a release. Run `python3 scripts/release.py prepare --bump patch` (or
the appropriate bump) to make and validate the local release commit. Then run
`python3 scripts/release.py publish --confirm v<version>`: `publish` pushes
`main` and the tag only after that exact confirmation. The complete procedure
is in [CONTRIBUTING.md](CONTRIBUTING.md#release-procedure).

## Roadmap

The immediate goals are the open queue items, starting with the hands-off task closure
follow-ups and the completion-handoff evidence for commits that cannot contain
their own SHA.

## License

Copyright © 2026 Biagio Liberto. Meridian is available under the [MIT License](LICENSE).
