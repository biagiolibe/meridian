# meridian

AI-Ready project management protocol — template source for the Meridian agentic development workflow.

## Structure

```
templates/
  base/                        # Generic templates (all profiles)
    PROJECT_PLAN.md
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

WORKFLOW_GUIDE.md              # Methodology reference
```

## Usage

From any project in Claude Code, run:

- `/meridian-init` — Bootstrap a new project (picks a profile, copies templates, replaces placeholders)
- `/meridian-task` — Create a new numbered task file and update the queue

The workflow is automatically applied in any project that has `PROJECT_PLAN.md` or `tasks/QUEUE.md` (via `~/.claude/CLAUDE.md`).
