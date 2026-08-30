# [Project Name] — Agent Rules

Read `PROJECT_WORKFLOW.md` before acting. It defines the canonical task lifecycle, review rules, roles, and Git workflow.

Work only on the explicitly assigned task. Before implementation, read its governing documents, inspect the repository and `git status --short`, state a short plan, and stop if unrelated changes or an unresolved higher-precedence conflict exist.

Run the task validation plus the project baseline checks recorded in `CLAUDE.md`/project documentation. Never claim completion when required validation fails.

At completion, report changed files, acceptance-criteria evidence, validation results, branch, commit, and assumptions.

## Token discipline

Read progressively: assigned task first, then only cited documents and required files. Do not reload unrelated project history or repeat instructions already stored in repository documents. Keep plans to three bullets and final reports to ten lines unless reporting a blocker or failed validation.
