# Project Execution Evidence Profile

This project-owned profile applies Meridian's stack-agnostic execution-evidence
discipline to its actual tools. Configure it during bootstrap, or before the
next implementation after a framework upgrade adds this file. Keep commands and
tool choices current; the task's declared validation and acceptance criteria
remain mandatory.

## Context reuse

- Sources already supplied by the active agent environment: `[describe them]`.
- When an exact reread is justified: `[describe the evidence-gap standard]`.

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

## Diff inspection

- Change-summary command or procedure: `[command or procedure]`.
- Per-file/hunk inspection procedure: `[command or procedure]`.

## Manual evidence

- Primary deterministic evidence when available: `[tests or checks]`.
- Distinct capture views normally required and the escalation rule for more:
  `[policy]`.
- Direct capture path and interactive-tool fallback: `[tools or procedure]`.

## Runtime configuration

- Lowest reliable reasoning cap by task class: `[policy]`.
- How the task cap is checked against the chat's effective setting and how a
  mismatch is relaunched: `[procedure]`.
- Faster-execution-mode availability and constraints: `[policy]`.
