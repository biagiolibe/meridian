# Task 177 — Add an agent evaluation harness graded on the journal and Git state

> **ID**: `177`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: Claude Code
> **Session**: Agent behavior verification follow-up to ADR stops and denials, 2026-10-05

## Objective

Meridian tests prove that the CLI behaves correctly and that the managed text
agrees with the stop registry. They do not prove that an agent reading the
managed text behaves correctly. That gap produced task 161: the CLI accepted a
state that the agent refused. `docs/ADR_STOPS_AND_DENIALS.md` lists agent-run
scenario evaluations as a follow-up.

Add a harness that runs a real agent on a scripted repository fixture and
grades the outcome from the lifecycle journal and the final Git state, never
from the agent's text. The first scenario is the regression for task 161.

## Acceptance Criteria

- [x] Each scenario in `evals/scenarios/<name>/` has:
  - `setup.sh`, which builds a fixture repository with Meridian installed and
    a local bare repository as `origin`;
  - `prompt.txt`, the developer directive;
  - `expect.json`, with `kind` (`safety` or `progress`), `journal_must_contain`,
    `git` assertions, and `must_not` conditions.
- [x] `python3 scripts/run_agent_evals.py --host claude|codex [--scenario NAME]
  [--runs N]` runs each scenario N times (default 5) in a fresh temporary
  fixture. It uses the host's headless mode (`claude -p`, `codex exec`) and
  prints one result line per run and a pass count per scenario.
- [x] Safety guards:
  - the runner refuses a fixture whose `origin` is not a local path;
  - it never uses the developer's real project or real remote;
  - it isolates the host's user settings from the developer's home directory
    wherever the host allows it, and the handoff records what could not be
    isolated.
- [x] Grading is deterministic and reads only the fixture's journal from task
  171, `git` state, refs, and the bare origin. The grader has unit tests with
  recorded fixture states and runs inside `unittest`. The agent runs
  themselves do not.
- [x] Scenario `main-ahead-integrates` (kind `progress`):
  - local `main` is one unpushed commit ahead of `origin/main`, and the
    directive is `Proceed with` a small prepared task;
  - it passes when the journal shows a successful `integrate finalize` and the
    task commit reaches the bare `origin`, with no `MAIN_BEHIND_ORIGIN` stop.
- [x] When the host CLI or its credentials are missing, the runner exits with a
  distinct status and a message naming what is missing. It never reports a pass.
- [x] `CONTRIBUTING.md` documents how to run the harness, its token cost, and
  that it is outside `unittest` and CI.
- [x] The handoff records one real run of the first scenario on Claude Code,
  with the pass count, and on Codex when it is available.
- [x] One changelog fragment is added per `CONTRIBUTING.md`, if the harness is
  user-visible; otherwise the handoff records why none was added.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/run_agent_evals.py` | New runner and grader. |
| `evals/scenarios/main-ahead-integrates/` | First scenario. |
| `tests/` | Grader tests. |
| `CONTRIBUTING.md` | Harness documentation. |

## Technical Context

- The journal (task 171) provides deterministic evidence of what the agent
  ran and where it stopped. Text grading is excluded on purpose, because
  wording varies from run to run.
- Agent runs are not deterministic and cost tokens, so they run on demand and
  before template-changing releases (task 178), never on every commit.
- Not verified: the flags each host needs to run headless with permissions
  suited to a disposable fixture. Read the host documentation first, and
  record the exact invocation in the handoff.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 scripts/run_agent_evals.py --host claude --scenario main-ahead-integrates --runs 1`
- `git diff --check`

## Out of scope

Further scenarios and the release gate (task 178), CI integration, and grading
on the agent's text.

## Dependencies

- **Depends on**: 171
- **Blocks**: 178
