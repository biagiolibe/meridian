# Task 040 — Ship Codex command-approval rules as a managed governed-SDD template file

> **ID**: `040`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3–4h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Deliver a project-scoped Codex execution-policy file,
`.codex/rules/meridian.rules`, to governed-SDD consumers through the normal
`meridian upgrade` path, so that a Codex session following the governed
workflow no longer stalls on approval prompts for the workflow's own Git and
`meridian` commands, and is never silently allowed a command the workflow
forbids.

Evidence (Palimpsest, milestone M30, sessions of 2026-09-19): 201 escalated
tool calls across the recorded Codex sessions. In one implementation session a
`git switch -c <task-branch>` failed inside the sandbox
(`Unable to create '.git/refs/heads/<branch>.lock': Operation not permitted`)
and the retry waited about 7.5 minutes for a manual approval. A hand-written
user-level `~/.codex/rules/default.rules` (15 rules) was evaluated with
`codex execpolicy check` against the commands those sessions actually ran:

- **Not covered** (still prompt): `git switch <existing-branch>`,
  `git merge-base --is-ancestor`, `git rev-parse main` / `--short HEAD`,
  `git commit --author=… -m …` (the reviewer-integrator acceptance commit),
  `git -C <path> …`, `git fetch`, `git stash`, `git restore`,
  `git cherry-pick`.
- **Over-permissive** (allowed although the workflow forbids them): any
  `git push` argument list, including `--force`, `-f`, and
  `--force-with-lease`; `git branch -D`; `git merge --no-ff`; a bare
  `meridian` prefix that also allows `upgrade` and mutating
  `execution reconcile`.
- Rules in `~/.codex/rules/` are user-global, so they apply to every
  repository on the machine, not only to the governed one.

A project-scoped file, versioned with the consumer and refreshed by the
framework, fixes the scope problem and lets the workflow's own command set be
the single source of truth.

## 📋 Acceptance Criteria

- [ ] `templates/workflows/governed-sdd/.codex/rules/meridian.rules` exists
      and contains `prefix_rule(...)` entries that:
      - `allow` the routine governed commands (see the validated starting
        draft below);
      - `forbid` `git push` with `--force`, `-f`, `--force-with-lease`,
        `--delete`, and `--mirror`;
      - use `prompt` for `git branch -D` / `--delete` / `--force` / `-f`;
      - allow only the `meridian` subcommands recorded under Decision D1.
- [ ] A decision-table fixture (command → expected decision) covers at least
      the 26 commands in the evidence table below. A test evaluates it with
      `codex execpolicy check --rules <file> -- <command…>` when `codex` is on
      `PATH`, and is skipped with an explicit reason otherwise. A second,
      Codex-independent test asserts that every `prefix_rule` line in the
      template is well formed (single-line, `pattern=[…]`, a valid
      `decision`).
- [ ] The framework's managed-file enumeration
      (`managed_files_for_workflow()` in `scripts/meridian.py`) includes the
      new path for `governed-sdd` only, and `lean-delivery` does not receive
      it. Today that enumeration is a fixed list plus `docs/**/*.md`, so a
      `.rules` file under `.codex/` is not enumerated without this change.
- [ ] `meridian upgrade --check` and `--apply` on a consumer that has no
      `.codex/` directory plan an `add` ("new managed file") for the rules
      file and create it. On a consumer that already carries a locally edited
      copy, the existing three-way merge preserves local rules and reports a
      real conflict exactly like any other managed file. Both cases have
      tests.
- [ ] A new migration record (next contiguous number; `041` at the time of
      writing) lists the new file in `managedPaths`, with a `delta` and
      `verification` entries, and the `VERSION`, `CHANGELOG.md`, and
      `.claude-plugin` versions follow the repository's current release
      convention. If the open Phase 5 version-split tasks (015–021) have
      landed by then, follow the version scheme they introduced instead of
      assuming `1.1.x`. `check_migrations()` passes.
- [ ] Decision D3 (marker protection) is recorded in the task's completion
      notes and implemented accordingly.
- [ ] **Chained-command behaviour is determined, not assumed.** In a scratch
      repository with the rules installed under `<repo>/.codex/rules/` in a
      trusted project, observe in a real Codex session whether a shell line
      such as `git status && git diff --check` runs without a prompt when
      every part is allowed, and what happens when one part is `forbidden`
      or unmatched. Record the transcript evidence in the completion notes.
      If chains are not evaluated per part, the template header comment and
      the docs state that governed sessions must issue one command per call.
      (The offline checker does not parse `bash -lc '…'`, so it cannot answer
      this; Codex sessions chain most commands, so the answer decides whether
      the rule set is effective.)
- [ ] **Activation is observable, not assumed.** The docs and the template
      header state that a project's `.codex/rules/` loads only when the
      project's `.codex/` layer is trusted (user-level trust in
      `~/.codex/config.toml`, which Meridian cannot ship or grant), that an
      untrusted project silently ignores the file, and give a one-command
      check of the file itself
      (`codex execpolicy check --rules .codex/rules/meridian.rules -- git status`)
      plus the manual check that proves activation (a governed session
      running an allowed command that previously prompted no longer prompts).
- [ ] The docs describe how the file interacts with a user-level
      `~/.codex/rules/default.rules` (rules combine; the most restrictive
      decision wins — confirmed for `allow` + `forbidden` in the draft
      evaluation), and that `git -C <path> …` cannot be covered by a
      prefix rule, so sessions should use the tool's working-directory
      parameter instead.
- [ ] `python3 -m unittest discover -s tests`,
      `python3 scripts/check_repository.py`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/.codex/rules/meridian.rules` (new) | The managed rules file. |
| `scripts/meridian.py` | `managed_files_for_workflow()` enumeration; `plan_upgrade()` already has an `add` action for a file with no baseline/local copy. |
| `migrations/041-…json` (new) and `migrations/README.md` | Migration record and its authoring rules. |
| `migrations/CAPABILITY_MARKERS.md` | Marker design, needed for Decision D3. |
| `tests/test_meridian_cli.py` and a new rules test module | Planner/`add`/three-way-merge cases and the decision table. |
| `README.md`, `CHANGELOG.md`, `VERSION`, `.claude-plugin/plugin.json` | Docs and release bookkeeping. |
| `scripts/check_repository.py` | Baseline gate; verify managed-path and migration checks accept a non-Markdown file. |

## 🧩 Technical Context

- **Current behaviour**: Meridian ships nothing for Codex approvals.
  `default.rules`, `prefix_rule`, and `execpolicy` do not appear in the
  repository. Consumers rely on the user's global Codex rules or on manual
  approvals.
- **Codex facts verified while designing this task** (Codex CLI 0.155.1):
  - `codex execpolicy check --rules <file> -- <command…>` evaluates a rule
    file offline and prints `{"matchedRules":[…],"decision":"…"}`; an empty
    `matchedRules` means no rule matched (Codex then follows its normal
    approval flow).
  - A rule pattern is an exact token prefix. Alternatives per position are
    written as a list (`["git", ["status","diff"]]`). A path cannot be
    wildcarded, so `git -C <path> …` cannot be covered generally.
  - Project rules live in `<repo>/.codex/rules/` and load only when the
    project's `.codex/` layer is trusted.
  - When several rules match, the most restrictive decision wins
    (`forbidden` over `prompt` over `allow`), as checked for
    `git push --force` against an `allow` on `git push`.
- **Desired behaviour**: `meridian upgrade --apply` installs the file into a
  governed-SDD consumer; the routine governed Git/`meridian` commands run
  without approval; force-push flags are refused; everything else keeps its
  normal approval behaviour.

### Validated starting draft

This draft was evaluated against 26 commands with `codex execpolicy check`;
the results in the next table are the observed ones. It is a starting point,
not a mandated final file.

```text
prefix_rule(pattern=["git", ["status","diff","log","show","rev-parse","merge-base","branch","add"]], decision="allow")
prefix_rule(pattern=["git", "switch"], decision="allow")
prefix_rule(pattern=["git", "commit", "-m"], decision="allow")
prefix_rule(pattern=["git", "merge", "--ff-only"], decision="allow")
prefix_rule(pattern=["git", "push"], decision="allow")
prefix_rule(pattern=["meridian", ["execution","context","budget","locations","adr","audit"]], decision="allow")
prefix_rule(pattern=["git", "push", ["--force","-f","--force-with-lease","--delete","--mirror"]], decision="forbidden")
prefix_rule(pattern=["git", "branch", ["-D","--delete","--force","-f"]], decision="prompt")
```

The evaluated draft also carried one project-specific rule for the
reviewer-integrator acceptance commit (Decision D2). The `meridian` line above
is the broad form that Decision D1 asks the implementer to narrow.

| Command | Observed decision |
|---|---|
| `git switch m30-present-001`, `git switch -c m30-verify` | allow |
| `git rev-parse main`, `git rev-parse --short HEAD` | allow |
| `git merge-base --is-ancestor main x`, `git merge --ff-only x` | allow |
| `git merge --no-ff x` | no match (prompt) |
| `git commit -m x` | allow |
| `git commit --author=<override> -m y` | allow only for the exact override token |
| `git commit --author="Someone Else <a@b>" -m y`, `git commit --amend -m x` | no match (prompt) |
| `git push -u origin x`, `git push origin main` | allow |
| `git push --force origin main`, `-f`, `--force-with-lease` | **forbidden** |
| `git branch -d x`, `git branch --show-current` | allow |
| `git branch -D x` | prompt |
| `meridian execution validate …`, `meridian context authority …` | allow |
| `meridian upgrade --project .` | no match (prompt) |
| `git rebase main`, `git reset --hard HEAD~1`, `git fetch origin` | no match (prompt) |

## 🧭 Decisions to confirm with the developer before merging

Defaults are stated so the implementer can proceed; record the final choice in
the completion notes.

- **D1 — `meridian` allow scope.** Default: allow the read-only and
  validation subcommands (`context`, `locations`, `adr`, `budget`,
  `execution` `validate` / `ready-check` / `handoff-check` / `preflight` /
  `evidence` / `contract` / `investigate`) and leave `execution reconcile`,
  `upgrade`, `adopt`, `lock`, `finalize-adoption`, and `generate-*` to a
  normal prompt. The alternative is a bare `meridian` allow; it is
  recorded here as the rejected default because it lets state-mutating
  commands ride in on a prefix match.
- **D2 — Reviewer-integrator author override.** The acceptance commit uses
  `git commit --author="<PROJECT_NAME> Reviewer-Integrator <…@<slug>.local>" -m …`.
  A prefix rule needs the literal token, but the template only knows
  placeholders. Default: ship the rule as a commented example with the
  placeholder form and an instruction that the project adds its resolved
  line locally (the three-way merge preserves it).
- **D3 — Marker protection.** Existing capability markers are HTML comments,
  and this file uses `#` comments. Default: no protected region and no
  `meridian audit` check for this file; plain three-way merge only, because
  projects are expected to append local rules. Choosing protection instead
  requires extending the marker parser and audit and is a larger task.
- **D4 — `git push` breadth.** Default: allow any `git push` except the
  forbidden flag set above, matching the workflow's "push each validated task
  branch once and `main` once" policy.

## 🔨 Suggested Implementation

1. Read `migrations/README.md`, `migrations/CAPABILITY_MARKERS.md`, and the
   `plan_upgrade()` / `managed_files_for_workflow()` code paths; confirm the
   `add` action creates a file whose directory does not exist yet.
2. Add the template file, extend the enumeration for `governed-sdd`, and add
   the planner tests (no `.codex/`, edited local copy, lean-delivery
   unaffected).
3. Add the migration record, version/CHANGELOG bookkeeping, and the docs
   section.
4. Add the decision-table fixture and its two tests.
5. Perform the chained-command observation in a scratch repository and record
   the result; adjust the header comment and docs accordingly.
6. Run the baseline gates.

## ⚠️ Constraints and Considerations

- Lean Delivery applies to this repository; do not add branch or reviewer
  procedures. Follow the local Git conventions.
- Repository text is English-only.
- Do not write to `~/.codex/`, and do not modify any consumer repository
  (including Palimpsest) directly. Adoption in a consumer happens through
  `meridian upgrade` under that consumer's own workflow.
- Do not ship rules that allow `git rebase`, `git reset --hard`,
  `git commit --amend`, `git fetch`, or force-push forms: the governed
  workflow forbids or restricts them.
- The rules file controls command approval only. It cannot express line-count
  or file-size discipline; read-size enforcement for Codex is a separate
  follow-up (see Non-goals).

## 🚫 Non-goals

- A Codex equivalent of `hooks/read-guard.sh` (`<repo>/.codex/hooks.json`,
  `PreToolUse`): separate follow-up. It needs an empirical check of the live
  `tool_name` and payload shape first, and Codex requires a one-time manual
  trust of any non-managed hook.
- A user-level installer for `~/.codex/rules/`.
- Rules for `lean-delivery` consumers.
- A `meridian audit` check that the rules file is present or that the
  project's `.codex/` layer is trusted.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: a Codex read-guard hook task, which would share the
  `.codex/` template directory introduced here.
- **Interaction to watch**: Phase 5 (tasks 015–021) changes the version
  scheme used by migrations; re-check it before numbering the migration.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/040-codex-command-approval-rules-template.md)"$'\n\nExecute this task in the current project.'
```

## Completion notes

- Completed on 2026-09-20 with migration `041-codex-command-approval-rules`
  and framework version `1.1.38`.
- D1: accepted the default narrow `meridian` allow-list: `context`,
  `locations`, `adr`, `budget`, `audit`, and the named `execution` validation
  subcommands. `upgrade`, adoption/locking commands, generators, and
  `execution reconcile` remain unmatched.
- D2: accepted the default commented reviewer-integrator author-override
  example. A project must append its resolved literal-token rule locally.
- D3: accepted the default of no marker protection and no audit rule. This
  `#`-comment rules file uses ordinary three-way merge so projects can append
  local rules.
- D4: accepted the default broad `git push` allow with explicit `forbidden`
  rules for `--force`, `-f`, `--force-with-lease`, `--delete`, and `--mirror`.
- Trusted-project chain probe, Codex CLI 0.155.1: `git status && git diff
  --check` ran without approval; `git status && git push --force origin main`
  was refused before either segment ran; `git status && git rebase main` ran
  without approval and failed only because the scratch repository had no
  `main` upstream. The template and README therefore require one command per
  execution call.
- Verification passed: `python3 -m unittest discover -s tests -v` (156
  tests), `python3 scripts/check_repository.py`, and `git diff --check`.
