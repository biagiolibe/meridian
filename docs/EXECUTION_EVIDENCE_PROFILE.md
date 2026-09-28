# Project Execution Evidence Profile

This Meridian profile is configured for the repository's Python checks and
Git-based delivery workflow. Task-specific checks remain mandatory.

## Context and diagnostics

- Reuse unchanged sources and successful results from the active session.
- Locate a large-file range before reading it; the threshold is 400 lines.
- Allow at most two context expansions and three diagnostic hypotheses per
  failure. Stop with `BLOCKED` when the task contract is exhausted.
- Start with the failing check's ordinary bounded output, then run the
  narrowest test method or file-specific diagnostic. Use verbose output or a
  full trace only when those levels cannot identify the cause.

## Validation output

Run the repository checks with producer-status-preserving bounds:

```bash
set -o pipefail
python3 scripts/check_repository.py 2>&1 | tail -n 200
python3 -m unittest discover -s tests -v 2>&1 | tail -n 200
git diff --check 2>&1 | tail -n 200
```

Record each literal command, its exit status, and the material final lines.

## Diff and manual evidence

- Before and after material edits, use `git status --short` and
  `git diff --stat`; inspect every changed hunk with `git diff -- <path>`.
- Prefer unit, integration, schema, hash, and command-output checks. This task
  has no perceptual acceptance criterion, so no manual capture is required.

## Runtime configuration

Use the lowest reasoning level that can satisfy the task. A task-level cap,
when present, overrides this default and must be checked before substantive
work. Faster execution is allowed only when it preserves required evidence.
