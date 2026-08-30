# meridian

AI-Ready project management protocol — template source for the Meridian agentic development workflow.

## Structure

```
templates/
  base/                        # Generic templates (all profiles)
    CLAUDE.md
    README.md
    PROJECT_PLAN.md
    .gitignore
    .claudeignore
    tasks/
      TASK_BLUEPRINT.md
      QUEUE.md
  profiles/
    generic/                   # Any software project
      TECH_DESIGN.md
    game-rust-bevy/            # Rust games with Bevy engine
      TECH_DESIGN.md
    web-typescript/            # TypeScript web projects
      TECH_DESIGN.md
  workflows/
    governed-sdd/              # ADR/task/review overlay for gated SDD projects

WORKFLOW_GUIDE.md              # Methodology reference
skills/
  meridian-governed-sdd/       # Codex-compatible governed workflow skill source
```

## Installation

This repo is a Claude Code plugin. To install it as a local plugin:

```
/plugin marketplace add /path/to/meridian
/plugin install meridian@meridian-local
```

The marketplace name (`meridian-local`) is derived by Claude Code from the directory name when a local path is added directly as a single-plugin source (no `.claude-plugin/marketplace.json` needed). After installing, `/meridian-init` and `/meridian-task` become available, and the queue-briefing hook activates automatically in any project.

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

Choose a stack profile and then a workflow mode. In `governed-sdd`, the initializer adds:

```text
PROJECT_WORKFLOW.md              # precedence, roles, lifecycle, Git rules
AGENTS.md                        # Codex repository instructions
CLAUDE.md                        # Claude repository instructions
docs/ARCHITECTURE_DECISIONS.md   # accepted technical decisions
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

In a governed project, it creates a `TASK-NNN` file with explicit dependencies, governing documents, scope/non-goals, review policy, measurable acceptance criteria, and validation commands. It does not choose the next task automatically.

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

## Agent roles and Git workflow

- **Tech designer** writes ADRs/specifications and creates scoped tasks. It does not implement feature code unless explicitly assigned.
- **Implementer** receives one task ID, works in a dedicated branch/worktree, validates, commits, and updates the task to `READY_FOR_REVIEW` or `ACCEPTED` according to its policy.
- **Reviewer-integrator** is independent from the implementer. For a required-review task, it reviews the diff, reports `APPROVE`, `CHANGES_REQUESTED`, or `BLOCKED`, then after approval updates the two status records, pushes, and merges the existing PR when all repository gates pass.

Use one writer per worktree and one branch per task. Branches use normalized task IDs without provider prefixes, for example `task-012`.

GitHub does not allow a pull-request author to approve its own PR. With a single account, the reviewer-integrator provides the internal SDD gate but not a GitHub approval. If branch protection requires an approving review, add a distinct authorized reviewer identity; otherwise the reviewer-integrator leaves the PR open as `BLOCKED`.

## Codex support

Generated governed projects work with Codex immediately because they contain `AGENTS.md` and `PROJECT_WORKFLOW.md`.

For reusable Meridian operations across projects, the Codex skill source is at `skills/meridian-governed-sdd/`. Install or symlink that folder into the local Codex skills directory, then invoke it explicitly as:

```text
$meridian-governed-sdd
```

The skill helps bootstrap, design, implement, review/integrate, and audit the governed workflow. It does not replace project-specific rules.

## Existing projects

Do not copy the governed overlay onto an existing project blindly. Compare each generated document first and migrate only with an explicit decision, especially when the project already has a task queue, agent instructions, or branch policy.

The classic queue hook continues to work. Governed queues receive a compact briefing for active, review-ready, queued, and accepted tasks.
