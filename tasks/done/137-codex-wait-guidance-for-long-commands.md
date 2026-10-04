# Task 137 — Tell Codex agents to wait once for long commands

> **ID**: `137`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Call-count and polling analysis, 2026-10-03

## Objective

Task 120 added a rule that a command expected to run longer than one minute runs
"in the foreground with a timeout of up to 600 seconds, or in a persistent
terminal session; never detach it and poll for completion". That wording follows
Claude Code's foreground timeout. Codex runs a command in a session and returns
control after `yield_time_ms`, and an agent then polls with an empty
`write_stdin`. In seven Codex sessions on Meridian on 2026-10-03, five contained
8 to 13 model calls made only of such polls (`chars` empty, `yield_time_ms`
30000 while the suite ran about two minutes), 16 to 24 percent of those
sessions' calls. Each call re-sent a context averaging about 70,000 tokens, so
the polling cost roughly 0.6 to 0.9 million input tokens per session. Give Codex
agents an equivalent instruction that removes the polling, and state when the
full suite is run so it is not repeated without a code change.

## Acceptance Criteria

- [x] `docs/EXECUTION_EVIDENCE_PROFILE.md` and the Lean Delivery and Governed SDD
  template profiles gain a host-neutral statement and a Codex-specific one:
  a command expected to take longer than one minute is started with a wait long
  enough to cover its expected duration in the same call, and an agent polls an
  already running command at most once and only after that wait expired.
- [x] Before writing the Codex wording, verify on the installed Codex version the
  actual semantics and the maximum allowed value of the wait parameter
  (`yield_time_ms` for `exec_command`) and of the output-bound parameter, and
  record the version and the values in the handoff. If the maximum is lower than
  the duration of the full suite, the text says to use the maximum once and then a
  single further wait, not repeated short polls.
- [x] The wording is stated as observable behavior (a wait that covers the
  expected duration, no empty `write_stdin` loop) and does not name a private
  tool signature that can change; the exact parameter names appear only with the
  verified version noted.
- [x] The profile also states the suite-run rule, host-neutral: during
  implementation run only the tests of the modules the task touches; run the full
  suite once, after the last code change, as the validation of record; rerun it
  only when code changed since. It must not weaken the declared candidate
  validation (`REUSE`, `BOUNDED`, `FULL`), which stays as defined by tasks 121,
  122, and 125. In the seven sessions measured, `unittest` ran about five times
  per session.
- [x] The existing Claude Code wording stays and remains correct: foreground with a
  timeout of up to 600 seconds, never detached and polled.
- [x] The expected duration of this project's full suite is stated in this
  repository's profile (measured on 2026-10-03: about two minutes) so the agent
  does not need to guess, and is marked as a measurement that can change.
- [x] Changes to managed template text follow the capability-marker and migration
  rules. The change is additive; it shares the unreleased template-changing
  migration with other pending template tasks if one exists (confirm the current
  state of migrations and `VERSION` before adding another).
- [x] A recorded check after adoption, using `meridian usage report` if task 135
  is integrated and otherwise a manual count from the host's session log counters,
  compares the share of calls made only of empty polls before and after, on at
  least two sessions each. The handoff states whether it dropped; if the data is
  not available the handoff says so.
- [x] One changelog fragment with an Upgrade note is added per `CONTRIBUTING.md`.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Project profile and measured suite duration. |
| `templates/workflows/lean-delivery/docs/EXECUTION_EVIDENCE_PROFILE.md` | Shipped Lean wording. |
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Shipped Governed wording. |
| `docs/CONTEXT_BUDGET_POLICY.md` and templates | Cross reference only if the wording needs one. |

## Technical Context

- Measured on 2026-10-03 across seven Codex sessions on Meridian (Lean Delivery):
  41 to 68 model calls each; about 290 commands; 8 to 13 poll-only calls in five
  of the sessions; Codex already batches independent commands in one call (about
  one call in five), so batching exists and polling is a choice of the agent.
- The measurement counted commands of the form `{"cmd":"..."}` and may miss other
  forms, so the counts are lower bounds on commands and an estimate of polling.
- This task changes guidance only; shortening the suite is task 138.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the validation commands, the suite, any lifecycle command, or the Claude
Code wording, and measuring Claude Code sessions.

## Dependencies

- **Depends on**: —
- **Blocks**: none
