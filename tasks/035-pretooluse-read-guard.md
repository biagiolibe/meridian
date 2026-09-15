# Task 035 — `PreToolUse` guard against unranged large-file reads

> **ID**: `035`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned

## Objective

Block (with an actionable message) a `Read` of a large file with no
`offset`/`limit`, in a Meridian project. `docs/PROPOSAL_CONTEXT_ENFORCEMENT.md`
(M2, and D1) found that the file-read discipline `CONTEXT_BUDGET_POLICY.md`
already states in prose ("read only the minimum files needed") was violated
in the measured session even though it was never ambiguous — whole-file reads
of `simulation.rs` (~7k tokens for ~60 needed lines) and the ADR log happened
anyway. Mechanical enforcement is the only lever that held in that same
session (the queue-briefing hook). This task generalizes it to reads.

## Acceptance Criteria

- [ ] A new hook script (e.g. `hooks/read-guard.sh` or `.py`, matching the
      existing hook's language choice) registered on `PreToolUse` for the
      `Read` tool in `hooks/hooks.json`.
- [ ] The hook only activates when the current directory is a Meridian
      project (`PROJECT_WORKFLOW.md` present) — mirrors the existing
      queue-briefing hook's silent-exit-elsewhere behavior.
- [ ] Denies a `Read` when: no Meridian workflow file exists at all → does
      not deny (inactive); the target file exceeds a line-count threshold
      (default 400, overridable via a documented `EXECUTION_EVIDENCE_PROFILE.md`
      setting) AND neither `offset` nor `limit` is present in the tool call.
      Allows the read otherwise.
- [ ] Denial message names: the file's line count, the threshold, and the
      two cheap alternatives (`grep -n` then a ranged `Read`, or
      `meridian context authority`/`meridian adr show` from task 034 when the
      target is the ADR log or a spec file).
- [ ] Exemption list, checked before the threshold: the file the session's
      active task assigns (from the resolved `Authority`/task path, reusing
      034's resolution when present), `LANGUAGE_POLICY.md`, and any file the
      project's entry router declares as always-loaded. Exemptions are
      project-declared, not hardcoded paths, so a non-Palimpsest project
      does not inherit Palimpsest-specific exemptions.
- [ ] `docs/EXECUTION_EVIDENCE_PROFILE.md`'s template gains a documented,
      overridable `read-guard threshold` setting (numeric, default 400)
      alongside the existing profile settings.
- [ ] Hook tests: file under threshold (allowed), over threshold without
      range (denied with the expected message), over threshold with
      `offset`/`limit` (allowed), exempted file over threshold (allowed),
      run outside a Meridian project (inactive/allowed).
- [ ] False-positive check: a legitimately large file the task must read in
      full (e.g. a generated fixture) is not silently unreadable — the
      denial message must state the override path (declare it in the task's
      `Authority`/exemption, or the developer sets a higher threshold),
      never a dead end.

## Relevant Files

| File | Role |
|------|------|
| `hooks/hooks.json` | Register the new `PreToolUse` hook alongside the existing `UserPromptSubmit` one. |
| `hooks/read-guard.sh` (new) | The guard logic: threshold check, exemption resolution, denial message. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Template addition for the overridable threshold. |
| `docs/CONTEXT_BUDGET_POLICY.md` | One line noting the guard exists and is mechanical, not a new restatement of the existing prose rule it backs. |
| `docs/PROPOSAL_CONTEXT_ENFORCEMENT.md` | Source measurement and rationale (§3, M2; risk note on legitimate large-file reads). |

## Constraints

- Advisory-safe on failure: if the hook cannot determine line count or
  parse the tool call (unexpected host payload shape), it must allow the
  read rather than block on an internal error.
- Does not touch `Write`, `Edit`, or any tool besides `Read`.
- Must not regress the exemption for the task's own assigned file — a
  worker blocked from reading its own task file is a correctness bug, not
  a discipline win.
- Same distribution model as the queue-briefing hook: runs from
  `$CLAUDE_PLUGIN_ROOT`, no per-project copy; only the profile-template
  addition and the `CONTEXT_BUDGET_POLICY.md` line ship via migration.

## Validation

- `python3 -m unittest discover -s tests` (hook logic covered by a
  subprocess-driven test harness, matching how `queue-briefing.sh` is
  tested if such a harness exists — check first; add one if not)
- `python3 scripts/check_repository.py`
- Manual: in a Meridian project, attempt to `Read` a >400-line non-exempt
  file with no range and confirm denial text names the alternatives; then
  confirm a ranged read of the same file succeeds.

## Dependencies

- **Depends on**: none (the exemption-resolution reuse of 034 is optional;
  ship a minimal path-list exemption first if 034 is not yet merged)
- **Blocks**: none (independent of 034)

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/035-pretooluse-read-guard.md)"$'\n\nExecute this task in the current project.'
```
