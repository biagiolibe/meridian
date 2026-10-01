# Task 099 — Skip the AppleScript compile test when `osacompile` cannot run

> **ID**: `099`
> **Category**: Test reliability
> **Priority**: 🔴 P1
> **Estimate**: ~0.5h
> **Assigned to**: unassigned
> **Session**: Agent runs blocked by the full test suite inside the Codex sandbox

## Objective

`AgentLaunchTest.test_split_payload_compiles_as_applescript` compiles the iTerm2
split payload with `osacompile`. Inside the Codex sandbox `osacompile` exists but
cannot reach macOS services and fails with an XPC `Connection invalid` error,
so the full suite (`python3 -m unittest discover -s tests`) fails for every task
an agent runs there, although the task did not touch the payload. Outside the
sandbox the test passes. Make the test skip, with a recorded reason, when the
environment cannot run `osacompile`, while still failing when the environment
works and the payload does not compile.

## Acceptance Criteria

- [ ] Before compiling the real payload, the test runs a probe that compiles the
  iTerm2 dictionary control script `tell application "iTerm2" to get unique id
  of current session of current tab of current window` with `osacompile`, using
  the same output handling and a timeout. If the probe exits non-zero or times
  out, the test calls `skipTest` with a message that starts with `osacompile
  cannot resolve the iTerm2 dictionary in this environment:` and includes the
  probe's stderr (or `timed out`).
- [ ] If the probe succeeds and the real payload does not compile, the test
  fails exactly as it does today, with the compiler's stderr in the failure
  message.
- [ ] The existing `skipUnless` conditions (macOS, `osacompile` on `PATH`,
  iTerm2 installed) are kept.
- [ ] A new test replaces `subprocess.run` with a double and covers: the probe
  failing with `-2741`/`-2740` dictionary-resolution text leads to a skip, the
  probe timing out leads to a skip, and the probe succeeding with a failing
  payload compile leads to a failure. The probe logic is a small helper so the
  double can exercise it without running AppleScript.
- [ ] No production code changes: `scripts/project_console.py` is untouched.
- [ ] The skip is visible: running the suite in an environment where the probe
  fails prints the skip reason in the unittest output (`-v`), so a handoff can
  record it as a named skip rather than a pass.
- [ ] `CONTRIBUTING.md` states, in its validation section, that this test
  proves the AppleScript payload compiles only where `osacompile` works, that a
  skipped result must be reported as a skip in the handoff, and that the
  maintainer runs the full suite outside the agent sandbox before a release.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass; on a
  machine where `osacompile` works the compile test still runs and passes.

## Relevant Files

| File | Role |
|------|------|
| `tests/test_project_console.py` | `test_split_payload_compiles_as_applescript` and its `skipUnless`. |
| `CONTRIBUTING.md` | Validation section. |

## Technical Context

- **Observed**: in an agent run, `python3 -m unittest discover -s tests` ran 441
  tests and failed only on this test. The developer confirmed that the payload
  compiles on their machine; compiling it against an app with no iTerm2
  dictionary reproduces `Expected “then” … found property (-2741)`.
- The repository already uses `skipUnless` with a stated reason, for example
  `tests/test_codex_rules.py` when `codex` is not on `PATH`.
- The control probe deliberately needs the iTerm2 scripting dictionary, the
  same external capability the real payload needs.
- **Accepted trade-off**: where the probe fails, a payload syntax error is not
  caught by this test. The check remains in the maintainer's run outside the
  sandbox and in any CI job that runs on macOS; the handoff must label the skip.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py' -v`
- Evidence tier: the skip and failure decisions are program-computed and
  asserted with test doubles; no manual evidence is required.

## Amendment — 2026-10-01

The developer replaced the `return 1` probe with the iTerm2 dictionary control
probe above. The trivial probe succeeds in the agent sandbox even when the
iTerm2 dictionary is unavailable, which would leave a valid payload failing
with dictionary-resolution syntax errors. This amendment preserves failure for
a bad payload while skipping only environments that cannot resolve iTerm2.

## Out of scope

Replacing the compile check with a text-only assertion, changing the AppleScript
payload, granting the sandbox access to macOS services, and any other test.

## Dependencies

- **Depends on**: 086
- **Blocks**: none
