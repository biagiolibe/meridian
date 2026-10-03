# Project Execution Evidence Profile

This default profile is fully configured and may be tightened by an explicit
task contract. A project may replace command names with its own equivalents,
but unresolved placeholders are never verification evidence.

## Context and diagnostics

- Reuse unchanged sources and successful results from the active session.
- Locate a large-file range before reading it; the default threshold is 400
  lines.
- Allow at most two context expansions and three diagnostic hypotheses per
  failure. Stop with `BLOCKED` when the applicable task contract is exhausted.
- Start with the failing check's ordinary bounded output, then run the
  narrowest single-test or file-specific diagnostic. Use verbose output or a
  full trace only when those two levels cannot identify the cause.

## Validation output

Run required checks with a producer-status-preserving bound:

```bash
set -o pipefail
<required validation command> 2>&1 | tail -n 200
```

The task record supplies each required validation command. Record the literal
command, its exit status, and the material final lines. Never treat the example
placeholder above as an executable project check.

Run a command expected to take longer than one minute in the foreground with a
timeout of up to 600 seconds, or in a persistent terminal session; never
detach it and poll for completion.

## Diff and manual evidence

- Before and after material edits, use `git status --short` and
  `git diff --stat`; inspect every changed hunk with `git diff -- <path>`.
- Prefer unit, integration, schema, hash, and command-output checks. Capture a
  manual view only for a genuinely perceptual acceptance criterion, with at
  most two distinct views per criterion unless the task explicitly authorizes
  more.

## Runtime configuration

Use the lowest reasoning level that can satisfy the task. A task-level cap,
when present, overrides this default and must be checked before substantive
work. Faster execution is allowed only when it preserves required evidence.
