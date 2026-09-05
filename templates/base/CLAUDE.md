# [Project Name]

[Brief project description in one or two sentences.]

Read `LANGUAGE_POLICY.md` before responding or writing. It fixes the conversation language independently of prompt language and requires English for every persistent repository artifact.

## Commands

```bash
# [primary commands: run, test, lint, format]
```

## Documents

| File | Contents |
|---|---|
| `TECH_DESIGN.md` | Architecture, conventions, and technical decisions. |
| `tasks/QUEUE.md` | **What to do next.** |

## Conventions

- [Project-specific code and documentation conventions.]
- [Architecture invariants that must not be violated.]

## Workflow (Meridian)

Work on one task at a time. After completing a task:

1. verify the acceptance criteria in the task file;
2. move the file from `tasks/` to `tasks/done/`;
3. update its status to `[x]` in `tasks/QUEUE.md` and `PROJECT_PLAN.md`.

## Approach

- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
