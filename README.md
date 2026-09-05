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

Choose `lean-delivery` for lightweight delivery or `governed-sdd` for controlled integration. `classic` remains a backwards-compatible alias for `lean-delivery`. The initializer creates the relevant planning, design, queue, task, and agent-instruction files in the target project. It does not overwrite existing workflow documents without showing a diff and obtaining a migration decision.

### Language behavior

During initialization, choose the language used for agent-developer conversation. Meridian stores that preference in `LANGUAGE_POLICY.md`; agents must keep using it even when an individual prompt is written in another language. The file also establishes an unconditional invariant: every persistent repository artifact—including code, documentation, comments, identifiers, user-facing strings, tests, configuration text, and commit messages—must be in English.

To change the conversation language later, explicitly request the change and update `LANGUAGE_POLICY.md` in the same edit. Prompt language alone never changes the preference.

When you are ready to scope work, run:

```text
/meridian-task
```

The queue briefing hook stays silent outside a project containing `tasks/QUEUE.md`.

## Quick start with Codex

Generated Lean Delivery and Governed-SDD projects work with Codex immediately because they include `AGENTS.md` and `PROJECT_WORKFLOW.md`.

For reusable Meridian operations across projects, install or symlink [`skills/meridian-lean-delivery/`](skills/meridian-lean-delivery/) and [`skills/meridian-governed-sdd/`](skills/meridian-governed-sdd/) into your local Codex skills directory. Set the location of this checkout once per machine:

```bash
export MERIDIAN_ROOT=/path/to/meridian
```

Then invoke the skill explicitly in Codex:

```text
$meridian-lean-delivery
# or
$meridian-governed-sdd
```

The selected skill supports its workflow without replacing project-specific rules. Lean Delivery keeps a lightweight explicit task-and-verification contract; Governed SDD adds architectural authority, dependency gates, formal review, and controlled integration.

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

This is a process boundary, not a claim that every project needs bureaucracy. Use Lean Delivery when the work is low-risk and reversible; use stronger gates when a mistake is expensive.

## Repository layout

```text
commands/                         Claude Code commands
hooks/                            Queue briefing hook
skills/                           Codex and Claude Code workflow skills
templates/base/                   Shared stack-agnostic templates
templates/workflows/lean-delivery/ Lean Delivery overlay
templates/workflows/governed-sdd/ Governed-SDD overlay
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
