# Project Execution Evidence Profile

This project-owned profile applies Meridian's stack-agnostic execution-evidence
discipline to its actual tools. Configure it during bootstrap, or before the
next implementation after a framework upgrade adds this file. Keep commands and
tool choices current; the task's declared validation and acceptance criteria
remain mandatory.

The diagnostic-attempt, evidence-capture, and context-expansion budgets below
are caps, not targets: reaching one requires `BLOCKED`, never a silently
raised cap. Raising a default above its stated value requires a recorded
rationale, in the same shape the task blueprint's `Reasoning justification`
field already uses.

## Context reuse

- Sources already supplied by the active agent environment: `[describe them]`.
- When an exact reread is justified: `[describe the evidence-gap standard]`.
- Context-expansion budget and the condition that requires `BLOCKED` rather
  than another expansion: `Context expansions`: 2 per task. One expansion is
  one read beyond the task's declared `Authority` and `Expected code
  surface` — a file, ADR, specification, or prior chat opened to resolve a
  blocker or verify an acceptance criterion. Override with the task's
  `Context expansions` field.

## Successful validation output

Record each required check as the complete literal command string that is
actually run, including its own output-bounding stage — not a bare command
plus a prose instruction to summarize or truncate the output afterwards. A
bound stated only in prose can govern nothing but how the output gets
*restated* once it has already been returned to the session and billed in
full; the command string is the only point that controls how much output
ever enters context at all. The shell shape is:

```bash
set -o pipefail
<validation command> 2>&1 | tail -n <this project's chosen bound>
```

`set -o pipefail` is not optional: without it, a pipeline reports the exit
status of its last stage (here, `tail`), which is always success, so a
failing validation command silently reads as passing. Where the shell lacks
`pipefail`, capture `${PIPESTATUS[0]}` explicitly instead.

- Required validation commands, each as the exact string executed —
  command, redirection, and output bound together: `[commands]`.
- Exit-status mechanism this project uses (`set -o pipefail` or
  `${PIPESTATUS[0]}`) and how the captured status is reported: `[method]`.
- The output bound itself (line count, byte count, or equivalent) is this
  project's own choice; record the chosen value and where it is applied:
  `[bound]`.

## Failure diagnostics

- First targeted diagnostic or bounded-log procedure: `[procedure]`.
- Conditions for full traces, verbose output, or complete logs: `[conditions]`.
- Diagnostic-attempt budget and the condition that requires `BLOCKED` rather
  than another implementation hypothesis: `Diagnostic attempts`: 3 per
  failure. One attempt is one diagnostic action that changes the
  implementation hypothesis — a new targeted probe, log capture, or
  parameter change aimed at a different cause. Override with the task's
  `Diagnostic attempts` field.

## Diff inspection

- Change-summary command or procedure, run before the first code edit and
  after each material change: `[command or procedure]`.
- Per-file/hunk inspection procedure: `[command or procedure]`.

## Manual evidence

- Primary deterministic evidence when available: `[tests or checks]`.
- Distinct capture views normally required and the escalation rule for more:
  `Evidence captures`: 2 per acceptance criterion. One capture is one
  distinct manual-evidence view — one screenshot, log export, or
  interactive-tool session — gathered for a single acceptance criterion.
  Override with the task's `Evidence captures` field.
- Direct capture path and interactive-tool fallback: `[tools or procedure]`.

## Runtime configuration

- Lowest reliable reasoning cap by task class: `[policy]`.
- How the task cap is checked against the chat's effective setting and how a
  mismatch is relaunched: `[procedure]`.
- Faster-execution-mode availability and constraints: `[policy]`.
