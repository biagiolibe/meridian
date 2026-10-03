# Task 123 — Complete the unattended-closure command policy for Codex and Claude Code

> **ID**: `123`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h (kept as one task so consumers take a single baseline migration)
> **Assigned to**: unassigned
> **Session**: Follow-up of the unattended-closure gap observed on 2026-10-03

## Objective

`Proceed with <TASK-ID>` is meant to run implementation, validation,
integration, push, and cleanup without approval prompts (task 100, Decision 1).
Several commands that the closure flow uses still prompt, most visibly on
Codex. Close that gap with narrowly scoped allowances in both host policies,
Codex first, and ship them to existing projects through one explicit managed-file
migration.

Known gaps:

- `git mv` for the task-record archive rename into `tasks/done/` is allowed in
  neither host policy.
- `.codex/rules/meridian.rules` lacks `meridian worktree evidence` and
  `meridian worktree closure-status`; the Claude Code allowlist already has
  both.
- Read-only inspection and the repository validation commands (for example
  `sed`, `rg`, and the `python3` check and test commands) prompt on Codex.
  The full set is not yet known and is produced by the inventory below.

## Acceptance Criteria

### Inventory

- [ ] Before changing any rule, build a catalogue of every command the closure
  flow runs, taken from `docs/WORKTREE_LIFECYCLE.md`,
  `docs/EXECUTION_EVIDENCE_PROFILE.md`, `closure-status` resume actions, the
  shipped workflow documents, and the most recent task handoffs and
  transcripts. Include the inspection tools agents commonly use.
- [ ] Classify each command with `codex execpolicy check --rules ...` as
  `allow`, `prompt`, or `forbidden` under the current rules, and record the
  result in the task handoff. A command that cannot be evaluated is listed as
  an evidence gap, not guessed.

### Rules

- [ ] Add an allow rule for the task-record archive rename and nothing broader.
  Decide and document whether the pattern can restrict the destination to
  `tasks/done/`; if execpolicy prefixes cannot, state the limitation and the
  residual risk instead of implying a narrower rule.
- [ ] Add `meridian worktree evidence` and `meridian worktree closure-status` to
  the Codex rules.
- [ ] Allow only commands that cannot write outside the task worktree or execute
  other programs: read-only inspection in forms that are safe, and the exact
  validation commands from the execution evidence profile. Forms that write
  or execute (for example `sed -i`, `rg --pre`, `find -exec`, `-delete`) stay
  prompting or forbidden, and each exclusion is stated with its reason.
- [ ] Where a command has no safe prefix form, leave it prompting and list it
  in the documentation as an intentional approval point.
- [ ] No other command becomes allowed, and every existing `forbidden` and
  `prompt` rule is unchanged (`git reset`, `rebase`, `cherry-pick`, force push,
  branch deletion, `worktree add|remove|prune`).
- [ ] The rules are present in this repository's `.codex/rules/meridian.rules`
  and in both `templates/workflows/*/.codex/rules/meridian.rules`.
- [ ] `meridian codex doctor` probes every new rule with `execpolicy check` and
  reports each as ready or as a named gap, like the existing rules.
- [ ] The Claude Code allowlist offered by `meridian setup` gains the equivalent
  entries (the `git mv` entry scoped to `tasks/`, and the safe inspection and
  validation commands), remains consent-based and additive, and is covered by
  the setup tests.

### Distribution

- [ ] A new migration under `migrations/` updates `.codex/rules/meridian.rules`
  for both workflow modes, following the precedent of migrations `041`, `047`,
  and `051` (file left unmarked so project-local rules appended by adopters are
  preserved by the three-way merge).
- [ ] The release is template-changing: it raises `workflowBaselineVersion`,
  adds a `release-baselines/` snapshot, and its `CHANGELOG.md` section includes
  an Upgrade notes subsection naming the managed path, the required
  `meridian upgrade --apply`, the likely conflict when a project edited the same
  block, and the follow-up `meridian codex doctor`.
- [ ] The documentation states the two delivery paths: Codex rules arrive through
  `meridian upgrade --check` and `--apply`; the Claude Code allowlist arrives
  through consented `meridian setup`.
- [ ] A test proves an existing adopter project with local rules appended
  receives the new rules by `upgrade --apply` without losing its local rules,
  and that the oldest supported baseline still upgrades in one apply.

### Hygiene

- [ ] Tests cover the rule text in each shipped file, each doctor probe result,
  the allowlist entries, and that an unrelated `git mv`, `sed -i`, and
  `rg --pre` are not allowed.
- [ ] One changelog fragment is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `.codex/rules/meridian.rules` | Project Codex policy. |
| `templates/workflows/lean-delivery/.codex/rules/meridian.rules` | Shipped Lean policy. |
| `templates/workflows/governed-sdd/.codex/rules/meridian.rules` | Shipped Governed policy. |
| `scripts/meridian.py` | Claude allowlist constant and `codex doctor` execpolicy probes. |
| `migrations/` and `release-baselines/` | New migration and baseline snapshot. |
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | Upgrade path and release-note contract. |
| `docs/WORKTREE_LIFECYCLE.md` | States the archive-rename requirement. |
| `tests/test_meridian_cli.py` | Doctor, setup, and upgrade tests. |

## Technical Context

- `docs/WORKTREE_LIFECYCLE.md` requires an exact 100%-similarity rename from the
  active record path to `tasks/done/` with the same file name.
- Plain `git add` is already allowed, so `mv` plus `git add` would create the
  same rename, but `mv` also prompts.
- Codex prefix rules match leading arguments only, so argument-sensitive safety
  (destination of `git mv`, flags of `sed` and `rg`) may not be expressible;
  resolve this first and prefer an explicit statement of the residual risk over
  a rule that looks narrower than it is.
- Codex applies the rules file only in a trusted project layer, so the doctor
  result, not the file's presence, is the evidence of activation.
- The rules file is an unmarked managed file; migrations `041`, `047`, and `051`
  are the template for the migration shape.
- Lifecycle commands must stay free of project-provided command execution; this
  task only changes host approval policy.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Allowing any write-capable or program-executing command, changing
`integrate stage` archive validation, relaxing forbidden or prompting rules, and
the console visibility of staged tasks (task 124).

## Dependencies

- **Depends on**: —
- **Blocks**: none
