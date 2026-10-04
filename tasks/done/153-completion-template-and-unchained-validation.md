# Task 153 — Install the completion template here and keep validation commands unchained

> **ID**: `153`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Codex session log of task 152, 2026-10-04

## Objective

Codex sessions on this repository often show commands such as
`python3 scripts/check_repository.py && git diff --check && git status --short && sed -n '1,180p' docs/COMPLETION_REPORT_TEMPLATE.md && sed -n '1,120p' tasks/handoffs/151.md`
as `Failed (exit 1)`. In the task-152 session log the repository check,
`git diff --check`, and `git status` all succeeded; only
`sed: docs/COMPLETION_REPORT_TEMPLATE.md: No such file or directory` failed, which
stopped the chain before the last read. The same missing-file error appears six
times in that day's Codex logs.

Two causes:

1. This repository has no `docs/COMPLETION_REPORT_TEMPLATE.md`, although the Lean
   Delivery template ships one and the Governed skills (linked into
   `~/.agents/skills` for Codex) tell agents to use that path. Agents look for it
   and fail.
2. Agents chain validation commands with exploratory reads in one `&&` command, so
   any failing read marks the whole command failed, hides that validation passed,
   and skips the remaining reads.

## Acceptance Criteria

- [x] This repository has `docs/COMPLETION_REPORT_TEMPLATE.md`, installed from
  `templates/workflows/lean-delivery/docs/COMPLETION_REPORT_TEMPLATE.md` as a
  managed copy: its digest is recorded in `.meridian/manifest.json` and the
  self-hosting profile evidence where applicable, and `python3
  scripts/check_repository.py` and `meridian audit` pass. Existing handoffs in
  `tasks/handoffs/` are not rewritten.
- [x] `PROJECT_WORKFLOW.md` names `docs/COMPLETION_REPORT_TEMPLATE.md` as the
  handoff format, outside managed blocks, in one line.
- [x] This repository's `docs/EXECUTION_EVIDENCE_PROFILE.md` states, outside
  managed blocks: each validation command of record runs as its own command with
  its own exit status; it is never joined with `&&` or `;` to exploratory reads
  (`sed`, `cat`, `rg`, `ls`) or to other validation commands whose individual
  status must be reported. Reads may be batched with each other.
- [x] The handoff records whether the same profile rule should ship in the Lean
  and Governed templates, with the evidence for it; the templates are not changed
  in this task.
- [x] Tests or repository checks prove the managed copy is recorded and that the
  profile contains the rule.
- [x] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/COMPLETION_REPORT_TEMPLATE.md` | New managed copy. |
| `.meridian/manifest.json` | Managed-file digest and profile evidence. |
| `PROJECT_WORKFLOW.md` | One-line pointer to the handoff format. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` | Project rule for unchained validation commands. |
| `tests/` or `scripts/check_repository.py` | Presence checks. |

## Technical Context

- Observed in `~/.codex/sessions/2026/10/04/rollout-2026-10-04T18-16-23-*.jsonl`:
  output `Meridian repository checks passed.` followed by the `sed` error, exit 1.
- `~/.agents/skills` links both `meridian-lean-delivery` and
  `meridian-governed-sdd`; the Governed skill names
  `docs/COMPLETION_REPORT_TEMPLATE.md`.
- Task 139 checks managed-copy digest drift; use `--write-managed-digests` to
  record the new digest.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing template text, the skills, or Codex skill linking, and rewriting past
handoffs.

## Dependencies

- **Depends on**: —
- **Blocks**: none
