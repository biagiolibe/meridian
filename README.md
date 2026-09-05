# Meridian

**A governed, spec-driven development (SDD) workflow for building software with AI coding agents.**

Meridian turns a project plan into small, explicit, verifiable tasks that agents can implement without rediscovering the project on every session. It provides templates, Claude Code commands, a queue briefing hook, and companion skills for a disciplined spec-driven workflow.

It is deliberately stack-agnostic: Meridian defines the process; each project supplies its own architecture, invariants, and validation commands.

> **Project status:** early-stage / experimental. The workflow is usable today, but its public API and templates may evolve before a stable release.

## Why Meridian?

AI agents are fast, but a prompt alone is a weak engineering contract. A request such as “add authentication” leaves an agent to infer the architecture, scope, constraints, acceptance criteria, and validation strategy.

Meridian makes those decisions explicit. Each task has a bounded objective, authority, expected code surface, non-goals, measurable acceptance criteria, dependencies, review policy, and validation commands. The result is less rediscovery, safer handoffs, and a review trail that remains useful after the chat is gone.

## Choose a workflow mode

| Mode | Best for | Task lifecycle |
|---|---|---|
| **Classic** | Small projects, prototypes, and lightweight work. | `[ ]` → `[/]` → `[x]` |
| **Governed SDD** | Long-running projects or changes that need architecture decisions, dependency gates, and controlled integration. | `QUEUED` → `IN_PROGRESS` → `READY_FOR_REVIEW` → `ACCEPTED` |

**SDD means spec-driven development:** before implementation, an agent receives an explicit, durable specification of the change—its authority, scope, constraints, acceptance criteria, and validation. In Meridian, a task file is that specification.

In governed SDD, low-risk documentation, mechanical configuration, scaffolding, and narrowly scoped tests may use the direct `QUEUED` → `IN_PROGRESS` → `ACCEPTED` path. Changes to domain rules, public APIs, dependencies, state transitions, persistence, deterministic behavior, security, or unresolved design decisions require review.

Only an `ACCEPTED` task satisfies another task's dependency.

## Quick start with Claude Code

Clone Meridian and register it as a local Claude Code marketplace:

```bash
git clone https://github.com/biagiolibe/meridian.git
cd meridian
```

In Claude Code, register and install the plugin:

```text
/plugin marketplace add /path/to/meridian
/plugin install meridian@meridian-local
```

Then open the project you want to initialize and run:

```text
/meridian-init
```

Choose `classic` for a lightweight queue or `governed-sdd` for the full workflow. The initializer creates the relevant planning, design, queue, task, and agent-instruction files in the target project. It does not overwrite existing workflow documents without showing a diff and obtaining a migration decision.

### Language behavior

During initialization, choose the language used for agent-developer conversation. Meridian stores that preference in `LANGUAGE_POLICY.md`; agents must keep using it even when an individual prompt is written in another language. The file also establishes an unconditional invariant: every persistent repository artifact—including code, documentation, comments, identifiers, user-facing strings, tests, configuration text, and commit messages—must be in English.

To change the conversation language later, explicitly request the change and update `LANGUAGE_POLICY.md` in the same edit. Prompt language alone never changes the preference.

When you are ready to scope work, run:

```text
/meridian-task
```

The queue briefing hook stays silent outside a project containing `tasks/QUEUE.md`.

## Quick start with Codex

Generated governed-SDD projects work with Codex immediately because they include `AGENTS.md` and `PROJECT_WORKFLOW.md`.

For reusable Meridian operations across projects, install or symlink [`skills/meridian-governed-sdd/`](skills/meridian-governed-sdd/) into your local Codex skills directory. Set the location of this checkout once per machine:

```bash
export MERIDIAN_ROOT=/path/to/meridian
```

Then invoke the skill explicitly in Codex:

```text
$meridian-governed-sdd
```

The skill supports workflow bootstrap, task design, implementation, review and integration, owner acceptance, and read-only process audits. It never replaces project-specific rules.

## How the governed workflow works

```text
Project plan → architecture decisions → atomic task → implementation → independent review → acceptance/integration
```

The project keeps durable process artifacts close to the code:

```text
PROJECT_WORKFLOW.md             # Lifecycle, precedence, roles, and Git rules
AGENTS.md / CLAUDE.md           # Agent-specific project instructions
LANGUAGE_POLICY.md              # Persistent conversation language and English-only repository text
docs/ARCHITECTURE_DECISIONS.md  # Accepted architecture decisions
docs/CONTEXT_BUDGET_POLICY.md   # Task-first context and reasoning policy
tasks/QUEUE.md                  # Canonical dependency and status queue
tasks/TASK-NNN.md               # One bounded unit of work
```

### Task contract

A governed task declares:

- the decision or specification that authorizes it;
- its expected code surface and explicit non-goals;
- dependencies and a reasoning profile;
- `REQUIRED` or `NOT_REQUIRED` review policy;
- measurable acceptance criteria and validation commands.

The task is the agent’s initial navigation map. It reads its authority and expected code surface first, then widens context only when evidence is insufficient or a blocker requires it.

### Roles and integration

Meridian separates the roles that make a code change from those that accept it:

- The **tech designer** records decisions and creates scoped tasks.
- The **implementer** works on one task in a dedicated branch/worktree and validates it.
- The **reviewer-integrator** independently reviews required-review work in a fresh session, verifies the task branch is a fast-forward descendant of `main`, and integrates only after approval.

This is a process boundary, not a claim that every project needs bureaucracy. Use the lightweight mode when the risk is low; use stronger gates when a mistake is expensive.

## Repository layout

```text
commands/                         Claude Code commands
hooks/                            Queue briefing hook
skills/                           Codex and Claude Code governed-SDD skills
templates/base/                   Stack-agnostic classic workflow templates
templates/workflows/governed-sdd/ Governed-SDD overlay
WORKFLOW_GUIDE.md                 Classic workflow reference
CONTRIBUTING.md                   Contribution guidance and validation
```

## Documentation

- [Classic workflow guide](WORKFLOW_GUIDE.md)
- [Governed SDD workflow template](templates/workflows/governed-sdd/PROJECT_WORKFLOW.md)
- [Task template](templates/workflows/governed-sdd/tasks/TASK_BLUEPRINT.md)
- [Review and integration prompt](templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md)
- [Read-only workflow audit prompt](templates/workflows/governed-sdd/docs/AUDIT_PROMPT_READ_ONLY.md)
- [Governed-SDD operator prompts](templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md)

## Development and contributions

Meridian’s templates are the product. Before proposing a change, run:

```bash
python3 scripts/check_repository.py
```

The check validates JSON metadata, Bash syntax, required repository files, and local Markdown links. Read [CONTRIBUTING.md](CONTRIBUTING.md) for workflow-specific contribution guidance.

## Roadmap

The immediate goals are to stabilize the public documentation, validate the workflow across real projects, and make installation and release management smoother for both supported agent environments.

## License

Copyright © 2026 Biagio Liberto. Meridian is available under the [MIT License](LICENSE).
