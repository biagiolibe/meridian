# meridian

AI-Ready project management protocol — template source for the Meridian agentic development workflow.

## Structure

```
templates/
  base/                        # Generic templates, language/stack-agnostic
    CLAUDE.md
    README.md
    PROJECT_PLAN.md
    TECH_DESIGN.md
    .gitignore
    .claudeignore
    tasks/
      TASK_BLUEPRINT.md
      QUEUE.md
  workflows/
    governed-sdd/              # ADR/task/review overlay for gated SDD projects

WORKFLOW_GUIDE.md              # Methodology reference
skills/
  meridian-governed-sdd/             # Codex-compatible governed workflow skill source
  meridian-governed-sdd-claude-code/ # Claude Code-compatible governed workflow skill source
```

## Installation

This repo is a Claude Code plugin. To install it as a local plugin:

```
/plugin marketplace add /path/to/meridian
/plugin install meridian@meridian-local
```

The marketplace name (`meridian-local`) comes from `.claude-plugin/marketplace.json`, which declares this repo as a one-plugin marketplace (plugin `meridian`, source `./`). After installing, `/meridian-init` and `/meridian-task` become available, and the queue-briefing hook activates automatically in any project.

If you move this repo to a different path after installing, re-run `/plugin marketplace add` with the new path — the old registration keeps pointing at the stale location.

## Workflow modes

| Mode | Use it when | Task model |
|---|---|---|
| `classic` | The project is small, exploratory, or benefits from a lightweight checklist. | Checkbox queue: `[ ]` → `[/]` → `[x]`. |
| `governed-sdd` | You want repeatable agent roles, explicit architecture decisions, dependency gates, and controlled PR integration. | `QUEUED` → `IN_PROGRESS` → `READY_FOR_REVIEW` → `ACCEPTED`, with a direct low-risk path to `ACCEPTED`. |

`classic` remains fully supported. `governed-sdd` is an overlay; it does not put game, web, or domain-specific rules into Meridian's generic process.

## Start a project

From a project in Claude Code, run:

```text
/meridian-init
```

Choose a workflow mode. In `governed-sdd`, the initializer adds:

```text
PROJECT_WORKFLOW.md              # precedence, roles, lifecycle, Git rules
AGENTS.md                        # Codex repository instructions
CLAUDE.md                        # Claude repository instructions
docs/ARCHITECTURE_DECISIONS.md   # accepted technical decisions
docs/CONTEXT_BUDGET_POLICY.md    # task-first context and reasoning policy
docs/COMPLETION_REPORT_TEMPLATE.md # concise task/review handoff
docs/CODE_REVIEW_PROMPT.md       # reviewer-integrator prompt
docs/PULL_REQUEST_POLICY.md      # forge and merge constraints
tasks/QUEUE.md                   # canonical dependency/status queue
tasks/TASK_BLUEPRINT.md          # atomic task template
```

Then fill in project-specific commands and invariants in `CLAUDE.md`, `AGENTS.md`, and the selected `TECH_DESIGN.md`. Meridian supplies the process; the project supplies its architecture and validation commands.

To create a task in Claude Code, run:

```text
/meridian-task
```

In a governed project, it creates a `TASK-NNN` file with explicit dependencies, authority, expected code surface, out-of-scope boundary, reasoning profile, review policy, measurable acceptance criteria, and validation commands. It does not choose the next task automatically.

## Governed SDD lifecycle

Every governed task declares one review policy:

```text
Review: REQUIRED
```

or:

```text
Review: NOT_REQUIRED
```

Use `NOT_REQUIRED` only for low-risk documentation, mechanical configuration, simple scaffolding, or focused tests that add no production behavior. Domain rules, public APIs, dependencies, state transitions, persistence/history, deterministic behavior, security, and unresolved design questions require review.

```text
Review: REQUIRED
QUEUED → IN_PROGRESS → READY_FOR_REVIEW → ACCEPTED

Review: NOT_REQUIRED
QUEUED → IN_PROGRESS → ACCEPTED
```

Only `ACCEPTED` tasks satisfy dependencies.

## Context and reasoning discipline

Governed SDD intentionally adds a small per-task documentation baseline in exchange for less rediscovery and rework. The generated `docs/CONTEXT_BUDGET_POLICY.md` makes the task the navigation map: read only its authority and expected code surface, and expand context only when blocked or when evidence is insufficient. It sets `medium` as the default for implementation, review, and routine SDD work; `high` for complex design/architecture; and `xhigh` only when justified and supported by the active tooling. Completion handoffs use a concise shared template.

Do not use a reviewer for a valid `Review: NOT_REQUIRED` task, and do not run parallel agents unless their scopes and worktrees are independent.

## Agent roles and Git workflow

- **Tech designer** writes ADRs/specifications and creates scoped tasks. It does not implement feature code unless explicitly assigned.
- **Implementer** receives one task ID, works in a dedicated branch/worktree, validates, creates the task commit, pushes the task branch exactly once, records the branch/implementation/base-`main` commits in the handoff, and leaves the primary checkout clean on the task branch. For `NOT_REQUIRED`, it then performs the acceptance commit and main integration.
- **Reviewer-integrator** is independent from the implementer and uses the same primary checkout in a fresh agent session. For a required-review task, it reviews the diff, reports `APPROVE`, `CHANGES_REQUESTED`, or `BLOCKED`, never pushes the task branch again, then after approval verifies fast-forward ancestry, creates the local status-only acceptance commit, fast-forwards and pushes `main` exactly once, and deletes the local task branch.

Use one writer per worktree and one branch per task. Branches use normalized task IDs without provider prefixes, for example `task-012`.

Before changing either status record, the reviewer verifies `git merge-base --is-ancestor main <task-branch>`. If it fails, do not mark the task `ACCEPTED`; return `BLOCKED` without fetching, rebasing, using a non-fast-forward merge, or force-pushing. If a reviewer session starts on clean `main`, it runs `git switch <task-branch>`; a missing local branch or dirty checkout that prevents switching is an exact-condition `BLOCKED`. The reviewer's `ACCEPTED` commit uses only this author override:

```bash
git commit --author="meridian Reviewer-Integrator <reviewer-integrator@meridian.local>" -m "docs: reviewer-integrator pass <TASK-ID>; independently re-verified diff, cited sources, acceptance evidence, and validation"
```

The fresh-session independence control and reviewer-specific author control are both mandatory. The override applies only to the `ACCEPTED` commit; keep the operator's normal committer identity, do not change global or repository Git config, and verify it with `git log --format='%an <%ae>'`. Owner acceptance remains status-only and does not automatically integrate the branch.

GitHub does not allow a pull-request author to approve its own PR. With a single account, the reviewer-integrator provides the internal SDD gate but not a GitHub approval. If branch protection requires an approving review, add a distinct authorized reviewer identity; otherwise the reviewer-integrator leaves the PR open as `BLOCKED`.

## Codex support

Generated governed projects work with Codex immediately because they contain `AGENTS.md` and `PROJECT_WORKFLOW.md`.

For reusable Meridian operations across projects, the Codex skill source is at `skills/meridian-governed-sdd/`. Install or symlink that folder into the local Codex skills directory, then invoke it explicitly as:

```text
$meridian-governed-sdd
```

Codex has no plugin system to resolve the Meridian repo path automatically, so set `MERIDIAN_ROOT` once per machine to your local clone:

```bash
export MERIDIAN_ROOT=/path/to/meridian
```

The skill reads `$MERIDIAN_ROOT/templates/workflows/governed-sdd/` for its bootstrap assets. Without it set, the skill asks for the path instead of guessing one.

The skill helps bootstrap, design, implement, review/integrate, and audit the governed workflow. It does not replace project-specific rules.

## Claude Code support

Generated governed projects also work with Claude Code immediately because they contain `CLAUDE.md` and `PROJECT_WORKFLOW.md`, and `/meridian-init` / `/meridian-task` (this plugin's commands) already speak the governed-SDD lifecycle.

For the same reusable, cross-project operations the Codex skill offers — bootstrap, design, implement, review/integrate, audit — the Claude Code counterpart is `skills/meridian-governed-sdd-claude-code/`. Since this repository is itself a Claude Code plugin, the skill loads automatically once the plugin is installed (see Installation above); no manual symlinking is needed. It routes to `/meridian-init` and `/meridian-task` where possible, reads `CLAUDE.md` (falling back to `AGENTS.md` for parity when a project targets both agents), and recommends running the reviewer-integrator step in an isolated context (a fresh chat, or a Task-tool subagent) instead of Codex's separate-invocation model.

## Existing projects

Do not copy the governed overlay onto an existing project blindly. Compare each generated document first and migrate only with an explicit decision, especially when the project already has a task queue, agent instructions, or branch policy.

The classic queue hook continues to work. Governed queues receive a compact briefing for active, review-ready, queued, and accepted tasks.
