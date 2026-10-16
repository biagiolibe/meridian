# Task 230 — Give runnable candidate validation commands

> **ID**: `230`
> **Category**: Bugfix
> **Priority**: 🔴 P1
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 229 integration stop, 2026-10-16
> **Origin**: friction

## Objective

`.meridian/candidate-validation.json` declares, per outcome (`REUSE`,
`BOUNDED`, `FULL`), command **fragments**. `missing_candidate_validation_commands`
(`scripts/meridian.py`) checks them by substring against the commands that the
agent reports. `meridian worktree advance` at step `C7` nevertheless returns
those fragments in the `commands` field of `run-candidate-validation`, as if
they were runnable commands.

On 2026-10-16 the task 229 session ran the returned `scripts/check_repository.py`
literally. The file is not executable, the command exited 126, and `advance`
aborted the integration with `BLOCKED CANDIDATE_VALIDATION_FAILED`. Earlier
sessions had added `python3` on their own. The default proposed by
`proposed_candidate_validation_declaration` has the same defect and also
proposes `unittest discover`, which is not a command by itself.

Make `advance` return commands an agent can run unchanged, while keeping
existing declarations valid.

## Acceptance Criteria

- [ ] A declaration may hold complete runnable commands, for example
  `python3 scripts/check_repository.py`. The substring check accepts a
  reported command that contains the declared entry, as it does today, so an
  existing fragment-only declaration stays valid without migration.
- [ ] `meridian worktree advance` at `C7` returns two distinct fields: the
  runnable `commands` to execute, and the `required_fragments` it checks.
  `commands` contains only entries that run unchanged from the primary
  checkout: `git diff --check` and each declared entry that is a complete
  command. For a declared entry that is not runnable on its own, `advance`
  does not present it as a command; it names it under `required_fragments`
  with an explicit instruction that the agent must run a project command
  containing it.
- [ ] The rule for deciding whether an entry is runnable is deterministic and
  documented, for example: its first token resolves to an executable on
  `PATH`, or is an existing executable file in the project. No network access
  and no execution happens during the decision.
- [ ] `proposed_candidate_validation_declaration` proposes complete commands:
  `python3 scripts/check_repository.py` when that script exists, and a runnable
  test command (for example `python3 -m unittest discover`) instead of the bare
  `unittest discover`. `meridian setup --check` shows the proposal; it never
  rewrites an existing declaration without `--apply` and a displayed diff.
- [ ] This repository's own `.meridian/candidate-validation.json` declares
  complete commands: `python3 scripts/check_repository.py` and
  `python3 scripts/run_tests.py --parallel`.
- [ ] The workflow text and `docs/WORKTREE_LIFECYCLE.md` describe the
  candidate step with the two fields. If managed text inside capability markers
  must change, the change ships with its migration, and the handoff records
  that the release becomes template-changing; prefer wording that the current
  managed text already permits.
- [ ] Tests cover:
  - `advance` output with a complete-command declaration;
  - `advance` output with a fragment-only declaration;
  - acceptance of a reported command that contains a fragment;
  - the new setup proposal;
  - a candidate run that executes the returned `commands` unchanged in a
    fixture project and passes.
- [ ] A changelog fragment `changelog.d/230.md` records the fix under
  `Fixed`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `candidate_validation_declaration`, `proposed_candidate_validation_declaration`, `missing_candidate_validation_commands`, `advance` step `C7`. |
| `.meridian/candidate-validation.json` | This repository's declaration. |
| `docs/WORKTREE_LIFECYCLE.md` | Candidate validation step. |
| `templates/workflows/*/PROJECT_WORKFLOW.md`, `skills/*/SKILL.md` | Candidate validation wording. |
| `tests/` | Advance and setup tests. |

## Technical Context

- `advance` builds `commands = ["git diff --check", *fragments[decision]]`
  and returns it unchanged as `run-candidate-validation`.
- The declaration is consumer-owned project configuration, not a managed
  file. A consumer may keep fragments; the new output must still tell its
  agent what to run.
- The task 229 integration was aborted cleanly; no repository data needs
  repair.

## Out of scope

Changing the `REUSE`, `BOUNDED`, and `FULL` decision logic. Running candidate
validation from Meridian itself.

## Dependencies

- **Depends on**: none
- **Blocks**: none. Tasks 228 and 229 also edit `scripts/meridian.py`; start
  230 after 229 is integrated.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `git diff --check`

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/230-runnable-candidate-validation-commands.md)"$'\n\nExecute this task in the current project.'
```
