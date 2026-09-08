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

- Required validation commands and concise success-output forms: `[commands]`.
- How command exit status is retained and reported: `[method]`.

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

- Lowest reliable reasoning setting by task class: `[policy]`.
- Faster-execution-mode availability and constraints: `[policy]`.
