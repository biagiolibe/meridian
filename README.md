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

## Usage

From any project in Claude Code, run:

- `/meridian-init` — Bootstrap a new project (picks a profile and `classic` or `governed-sdd` workflow mode)
- `/meridian-task` — Create a new numbered task file and update the queue

The workflow is automatically applied in any project that has `PROJECT_PLAN.md` or `tasks/QUEUE.md` (via `~/.claude/CLAUDE.md`).

## Governed SDD mode

`governed-sdd` is the reusable version of Meridian's stricter delivery workflow: ADR precedence, atomic task dependencies, explicit review policy, dedicated task branches/worktrees, reviewer-integrator, and PR governance. It preserves the existing `classic` mode for lightweight projects.

The Codex skill source lives at `skills/meridian-governed-sdd/`. Install or symlink that folder into your Codex skills directory to make `$meridian-governed-sdd` available; generated governed projects also contain `AGENTS.md` and `PROJECT_WORKFLOW.md`, so CLI and desktop agents follow the same repository rules.
