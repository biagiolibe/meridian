# Task Execution Queue

Only `ACCEPTED` tasks satisfy dependencies. Choose the highest-priority queued task whose dependencies are all accepted.

| Order | ID | Priority | Status | Review | Dependencies | Task file |
|---:|---|---|---|---|---|---|
| 1 | TASK-001 | P0 | QUEUED | REQUIRED | — | [TASK-001](TASK-001.md) |

Update a task's status here in the same commit that updates its task file.
