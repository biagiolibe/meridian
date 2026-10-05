# Task 174 — Add `meridian worktree advance` to drive closure through its mechanical steps

> **ID**: `174`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Closure simplification follow-up to ADR stops and denials, 2026-10-05

## Objective

Closing a task asks the agent to sequence ten steps (C1–C10 in
`docs/TASK_CLOSURE_DESIGN.md`) from prose. `closure_status` already derives the
current step, stop reason, and resume command from Git and lifecycle state.
Add a driver that runs the mechanical steps itself and returns to the agent
only when the next step needs project code, a push, or a human decision. The
closure procedure moves from text into code.

This respects the rejected alternative in `TASK_CLOSURE_DESIGN.md`: the driver
never runs a test or any other project command.

## Acceptance Criteria

- [ ] `meridian worktree advance <TASK-ID> --project <primary> --format json
  [--validation-command CMD --validation-exit-code N]... [--accepted]` runs
  from the primary checkout. It repeatedly evaluates `closure_status` and
  performs each step that is mechanical and whose preconditions hold:
  - C5: records evidence from the supplied results, with the same logic and
    validation as `worktree evidence`;
  - C6: `integrate stage`;
  - C10: `cleanup`, once the push is proven.
- [ ] It stops and returns one JSON object with `step`, `action_required`,
  `commands`, `stop_code`, and `resume`:
  - `action_required` is `run-validation` (C1–C2), `run-candidate-validation`
    (C7), `push` (C9), `human` (a registered stop with `human_decision: true`),
    or `none` (done);
  - for C7, `commands` lists the commands required by the stage outcome
    (`REUSE`, `BOUNDED`, or `FULL`), from the project's candidate-validation
    declaration.
- [ ] C9 stays a plain `git push origin main` run by the agent, so the push
  remains under the host's per-command permission. The developer may change
  this decision before the task starts.
- [ ] Every stop goes through the registry helper from task 162. Every
  performed step and every stop is written to the journal from task 171.
- [ ] `advance` is idempotent: rerunning it after an interruption at any step
  continues from the derived state and never repeats a completed mutation. It
  never runs a command that the agent supplied.
- [ ] `meridian setup` adds `meridian worktree advance` to the Claude Code
  allowlist and to the Codex execution rules that already list the lifecycle
  commands.
- [ ] The existing single-step commands keep working unchanged.
- [ ] Tests cover a full run to C7, a rerun after an interruption at each
  mechanical step, missing validation results, a blocked stage, and an
  already-integrated task that reaches cleanup.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`; this is a CLI-only
  change.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `closure_status`, evidence, stage, cleanup, setup allowlists. |
| `.meridian/candidate-validation.json` | Example of the commands for each outcome. |
| `docs/WORKTREE_LIFECYCLE.md` | Command documentation. |
| `tests/test_meridian_cli.py` | Driver tests. |

## Technical Context

- Authority: `docs/TASK_CLOSURE_DESIGN.md` Decision 5 (the closure steps) and
  its rejected alternatives. `docs/ADR_STOPS_AND_DENIALS.md` lists this
  driver as a follow-up.
- `closure_status` reports C4 when the registered worktree is missing.
  `advance` does not change into the worktree; it uses the same path-based
  verification.
- Candidate validation and finalization (C7–C8) are task 175.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

C7–C8 (task 175), template text (task 176), pushing from Meridian, and running
any project command.

## Dependencies

- **Depends on**: 171
- **Blocks**: 175
