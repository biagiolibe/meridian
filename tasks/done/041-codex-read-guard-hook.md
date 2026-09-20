# Task 041 — Codex `PreToolUse` read guard, gated by an empirical probe

> **ID**: `041`
> **Category**: Feature (probe-gated)
> **Priority**: 🟡 P2
> **Estimate**: ~1h probe + ~4h implementation if the gate passes
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Give Codex sessions the same mechanical file-read discipline that
`hooks/read-guard.sh` (task 035) gives Claude Code sessions, or record with
evidence that the current Codex hook surface cannot provide it.

`hooks/read-guard.sh` is registered for the Claude `Read` tool only
(`hooks/hooks.json`, matcher `Read`). Codex has no `Read` tool: it reads files
by running `sed -n`, `cat`, `nl`, and `rg` through its shell tool, so the
existing hook has never fired in a Codex session, and the read-size discipline
that `docs/CONTEXT_BUDGET_POLICY.md` states in prose is not mechanically
enforced there.

Evidence (Palimpsest, milestone M30, Codex sessions of 2026-09-19, measured
from the recorded session logs):

- `M30-SELECT-001` implementation + remediation: 91 model requests, 9.99M
  input tokens processed (97% served from cache), of which the implementation
  turn alone was 3.46M. The first three tool calls returned ~110k characters
  (~27k tokens) that were re-sent on each of the ~40 following requests
  (~1.1M, about a third of that turn). Reasoning was under 0.1% of the volume.
- `M30-PRESENT-001` implementation: 64 requests, 5.75M input tokens. Six of the
  first calls each returned ~41k characters (the tool's output cap), for
  ~61k tokens of reads in the first minutes; one `rg '^## …|^### '` over the
  5771-line ADR log returned 755 lines, truncated at 17,948 tokens.
  `meridian context authority` was not called at all.
- The waste was **not** unranged whole-file reads. It was mid-sized ranged
  reads chained in one command, for example
  `sed -n '1,240p' A && sed -n '1,240p' B && sed -n '1,300p' C && sed -n '1,260p' D`.
  A guard that only checks "no `offset`/`limit`" would not have stopped any of
  them.

## 📋 Acceptance Criteria

### Step 0 — Probe (gate)

- [ ] In a throwaway scratch repository (never a consumer repository), install
      a **logging-only** `PreToolUse` hook with matcher `.*` in
      `<scratch>/.codex/hooks.json`. It appends the raw stdin JSON to a log
      file and exits `0`. The developer performs the one-time manual trust
      review of the hook (`/hooks` in Codex); a session started before that
      review does not run it. Record that the review was done and where Codex
      stored the trust state.
- [ ] Drive a real Codex session with at least: a plain read
      (`sed -n '1,5p' <file>`), a chained line
      (`git status && sed -n '1,5p' <file>`), a `cat`, and an `rg`. Use the
      same model/configuration a governed session uses, so the tool path
      matches the recorded logs, where the shell call is a `custom_tool_call`
      named `exec` wrapping JavaScript that calls
      `tools.exec_command({"cmd": …})`.
- [ ] Record, verbatim (paths redacted), for each call: `hook_event_name`,
      `tool_name`, the keys and values of `tool_input`, `cwd`, and whether the
      hook fired at all. Save the redacted payloads as test fixtures under
      `tests/fixtures/codex_hook_payloads/`.
- [ ] Probe a **deny**: a second hook that exits `2` with a reason on stderr and
      emits the JSON form
      (`hookSpecificOutput.permissionDecision: "deny"` plus a reason).
      Record whether the command was prevented from running, and what the
      model actually received as the reason. Confirm that a chained command
      is blocked as a whole.
- [ ] Record the exact `hooks.json` schema Codex accepted for a project-level
      hook (event name, `matcher`, `type`, `command`, `timeout`), and how the
      command is resolved (working directory, `PATH`, environment variables
      available, including whether `PLUGIN_ROOT` or a `MERIDIAN_ROOT`-style
      variable is set).
- [ ] Classify the outcome and write it in the task's completion notes:
      - **A** — the hook fires with a shell tool name (documented as `Bash`)
        and `tool_input.command` holds the shell string. Proceed.
      - **B** — the hook fires for the outer `exec` tool and `tool_input`
        carries the JavaScript source, with the shell `cmd` string embedded in
        it. Proceed only if the `cmd` values can be extracted reliably
        (including `Promise.all` batches); otherwise treat as C.
      - **C** — the hook does not fire for the code-mode shell path, or does
        not receive enough to identify a read. **Stop.** Deliver only the
        probe record and fixtures, mark this task done with the finding, and
        list the follow-up options in the notes (for example a different
        approval/permission mechanism, or a documented prompt-level rule).
        Do not implement steps 1–5.

### Probe evidence recorded 2026-09-20

A scratch repository probe using Codex CLI `0.155.1` reached classification
**A** for the tested project-session profile: a trusted project-local
`PreToolUse` hook received `tool_name: "Bash"` and the complete shell input in
`tool_input.command`. A multiline input containing a plain `sed`, a chained
`git status && sed`, `cat`, and `rg` arrived as one command string. A deny
hook that wrote its reason to stderr, emitted the structured deny JSON, and
exited `2` blocked both sides of an `&&` chain before either command ran.

The same probe showed that structured JSON alone is not sufficient when the
hook exits `2`: Codex reported the missing stderr reason and allowed the
command. The implementation must therefore emit stderr as the required
blocking channel; structured JSON is supplementary evidence, not an
alternative failure path for this profile. Changing the hook definition also
required a new manual trust review.

This evidence does **not** complete Step 0 or authorize steps 1–5 by itself.
The implementation task must still record the trust-state location, PATH and
environment evidence, redacted fixture payloads, and individually captured
plain-read, chain, `cat`, and `rg` calls under the governed session profile.

### Step 0 completion record (2026-09-20)

Classification: **A**. In scratch repository `<redacted>`, Codex CLI `0.155.1`
with model `gpt-5.6-terra` invoked a trusted project-local `PreToolUse` hook
as `tool_name: "Bash"`. The four individual captures are redacted in
`tests/fixtures/codex_hook_payloads/`: plain `sed -n '1,5p'`, an `&&` chain,
`cat`, and `rg`. Each has `hook_event_name: "PreToolUse"`, `cwd`, and the full
shell string in `tool_input.command`.

The developer reviewed the logging hook in `/hooks`. Codex persisted its trust
record in `~/.codex/config.toml`, under
`[hooks.state."<project>/.codex/hooks.json:pre_tool_use:0:0"]`, keyed by a
definition hash. The hook process had project `cwd`, `MERIDIAN_ROOT`, and a
`PATH` including `<MERIDIAN_ROOT>/bin`; no `PLUGIN_ROOT` was present. A changed
definition required another `/hooks` review. The denial variant emitted the
same reason on stderr and as structured `permissionDecision: deny` output,
exited `2`, and prevented both sides of `git status && sed -n '1,5p'` before
execution. The model received: `Task 041 probe denial: chained command blocked
before execution.`

### Steps 1–5 — only if the probe outcome is A or B

- [ ] **Command parser.** A host-adapter that extracts, from the Codex tool
      input, the read targets of read-shaped commands: `sed -n '<a>,<b>p' <file>`
      (and `sed -n '<a>p'`), `cat <file…>`, `head`/`tail` with `-n` or `-<n>`,
      and `nl … <file>` piped into `sed -n`, in every part of a
      `&&` / `;` / `|` chain. Anything it does not understand (command
      substitution, heredocs, variables in paths, unknown flags, `awk`,
      `python -c`) is ignored and the guard **allows**.
- [ ] **Effective-lines rule.** Denies when the *effective* lines a single tool
      call would return from files over the threshold exceed the budget.
      Effective lines are clamped to the real file: `sed -n '1,240p'` on a
      45-line file counts 45. A `cat` or open-ended read of a file over the
      threshold counts as its full length. The budget defaults to the existing
      `Read-guard threshold` (`docs/EXECUTION_EVIDENCE_PROFILE.md`, default
      400); see Decision H2. Files at or under the threshold never trigger it.
- [ ] **Same exemptions as the Claude guard**: `LANGUAGE_POLICY.md`, the active
      task's own file, every source `meridian context authority <ACTIVE>`
      resolves, and files an entry router declares always-loaded. Active only
      when `PROJECT_WORKFLOW.md` exists in the payload `cwd`.
- [ ] **Advisory-safe.** Any parse or resolution failure, unknown payload
      shape, missing file, or timeout allows the call. The hook never blocks
      on an internal error and never rewrites the command.
- [ ] **Denial message** states the file(s), effective line count, and budget;
      names the cheap alternatives (`rg -n` to locate, then a ranged
      `sed -n`; `meridian context authority <TASK-ID>` or
      `meridian adr show <ADR-ID>` for the ADR log or a spec file); and states
      the override path (declare the file in the task's `Authority`, or raise
      `Read-guard threshold`). Emitted in whichever form the probe showed the
      model receives.
- [ ] **Claude behaviour unchanged.** `tests/test_read_guard.py` passes without
      modification, and `hooks/hooks.json` keeps its current registrations.
- [ ] **Tests.** A decision table of command lines → allow/deny, including
      verbatim-shaped lines from the evidence above (chained ranged reads over
      several large files, a single small read, `cat` of a large file, an
      `rg` search, a command the parser cannot understand, an exempt file, a
      non-Meridian `cwd`), plus tests driven by the recorded probe fixtures.
- [ ] **Distribution.** The template
      `templates/workflows/governed-sdd/.codex/hooks.json` registers the hook
      using the schema recorded by the probe, and a new migration (next
      contiguous number) lists it in `managedPaths`, following the mechanism
      task 040 introduces for `.codex/` files. The hook command is
      addressable from a project-level file (Decision H3). Versions and
      `CHANGELOG.md` follow the repository's current release convention.
- [ ] **Trust and activation are documented, not assumed.** The docs state that
      Codex requires the developer to review and trust a non-managed hook once
      (`/hooks`), that an untrusted or unreviewed hook does not run, and give
      a smoke test that proves activation (read a file over the threshold in
      a governed session and observe the denial).
- [ ] `python3 -m unittest discover -s tests`,
      `python3 scripts/check_repository.py`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `hooks/read-guard.sh` | Existing Claude guard: threshold, exemptions, deny protocol (exit `2` + `permissionDecision: deny`). Behaviour must not change. |
| `hooks/hooks.json` | Claude registrations (`UserPromptSubmit`, `PreToolUse`/`Read`). Not changed. |
| `tests/test_read_guard.py` | Existing guard tests; the pattern for hook payload tests. |
| `docs/PROPOSAL_CONTEXT_ENFORCEMENT.md` | Rationale for mechanical (not prose) enforcement, §3 M2 and D1. |
| `docs/EXECUTION_EVIDENCE_PROFILE.md` (template) | Documents the `Read-guard threshold` setting; a new setting is avoided by default (H2). |
| `scripts/meridian.py` | CLI entry point, if Decision H3 selects a `meridian hook` subcommand; also the managed-file enumeration extended by task 040. |
| `templates/workflows/governed-sdd/.codex/hooks.json` (new, conditional) | Project-level Codex hook registration. |
| `tests/fixtures/codex_hook_payloads/` (new) | Redacted payloads recorded by the probe. |

## 🧩 Technical Context

- **Codex hook surface** (per the Codex documentation and `codex features list`,
  Codex CLI 0.155.1, `hooks` stable and enabled): hooks load from
  `~/.codex/hooks.json`, `<repo>/.codex/hooks.json`, plugin-bundled
  `hooks/hooks.json`, and managed `requirements.toml`; `PreToolUse` matches on
  `tool_name`; the payload carries `session_id`, `hook_event_name`, `cwd`,
  `turn_id`, `tool_name`, `tool_input` (documented: `tool_input.command` holds
  the shell command), `tool_use_id`, and `transcript_path`. The tested profile
  requires a denial to exit `2` **and** write its reason to stderr;
  `hookSpecificOutput.permissionDecision: "deny"` may accompany that response
  but is not a substitute. Non-managed hooks need an explicit one-time trust
  review before they run; hosted tools such as web search are not intercepted.
  The probe exists because the documentation does not say which `tool_name` a
  call issued through the code-mode `exec` wrapper presents, and the recorded
  sessions show exactly that wrapper.
- **Observed but unverified**: the user's `~/.codex/config.toml` already
  carries `[hooks.state."<plugin>:plugin.json#hooks[0]:stop:0:0"]` entries,
  which suggests trust state is stored per hook definition in user config.
- **Current behaviour**: the read-size discipline is prose-only for Codex.
- **Desired behaviour**: an over-budget read command is denied with an
  actionable message before it runs; everything else is untouched.

## 🧭 Decisions to confirm with the developer before merging

Defaults are stated so the implementer can proceed; record the final choice in
the completion notes.

- **H1 — Reuse strategy.** Default: leave `hooks/read-guard.sh` as the Claude
  entry point, byte-for-byte in behaviour, and add the Codex host adapter and
  effective-lines rule beside it, sharing the exemption resolution through a
  small common helper only if that can be done without changing the existing
  script's tests. A wholesale port of the bash guard to Python is a refactor
  and is out of scope here.
- **H2 — Budget setting.** Default: reuse the existing `Read-guard threshold`
  as the per-call effective-lines budget for files over the threshold, so no
  profile-template text changes and no capability-marker migration is needed.
  A separate `Read-guard span` setting is the alternative and would require
  one.
- **H3 — How a project-level file addresses the hook.** A consumer's
  `.codex/hooks.json` cannot reference a plugin root. Default: a host-neutral
  `meridian hook read-guard --host codex` CLI subcommand, conditional on the
  implementation proving that `meridian` resolves from a project hook's PATH.
  Do not infer that availability from an agent-session PATH or prior logs. If
  the hook environment lacks the command, use only a probe-verified
  framework-root environment variable or return an advisory-safe allow with a
  diagnostic; do not ship an unresolved command path.
- **H4 — Scope beyond Codex.** Default: Codex only. Registering the same
  shell-read guard for Claude's `Bash` tool would also apply it to Claude
  sessions and is a separate decision.

## 🔨 Suggested Implementation

1. Run Step 0 first and classify the outcome. Stop at C.
2. Write the command-line reader as a small pure function (input: command
   string; output: list of `(file, first, last-or-open)` targets) with its own
   table-driven tests, before touching hook wiring.
3. Add the effective-lines rule and exemptions on top, reusing the existing
   exemption behaviour.
4. Wire the hook entry point (per H3) and the deny protocol recorded by the
   probe.
5. Add the template `.codex/hooks.json`, the migration, docs, and changelog.
6. Run the baseline gates.

## ⚠️ Constraints and Considerations

- Lean Delivery applies to this repository; do not add branch or reviewer
  procedures. Repository text is English-only.
- Do not write to `~/.codex/`, do not trust hooks on the developer's behalf,
  and do not modify any consumer repository. The probe runs only in a scratch
  repository the implementer creates.
- Parsing shell is approximate by nature. Prefer a false allow to a false deny:
  a wrongly blocked read stalls real work; a missed read costs tokens only.
- The guard reduces read waste; it cannot prevent reads through
  `python -c`, `awk`, `perl`, or scripts, and it does not bound command
  output size. State this in the docs.
- Depends on task 040 for the managed-file enumeration of `.codex/` files.
  Step 0 does not depend on it and may run first.

## 🚫 Non-goals

- Rewriting a command through `updatedInput`, or clamping the tool's
  `max_output_tokens`.
- Porting `hooks/queue-briefing.sh` to Codex's `UserPromptSubmit`
  (separate task; not verified that Codex sessions currently receive it).
- `PostToolUse` or `PermissionRequest` hooks, or hooks for non-shell tools.
- `lean-delivery` consumers, and a user-level installer for `~/.codex/`.
- Changing the Claude `Read` guard's behaviour or thresholds.

## 🔗 Dependencies

- **Depends on**: task 040 (steps 1–5 only; Step 0 is independent).
- **Blocks**: none.
- **Interaction to watch**: the open Phase 5 version-split tasks (015–021)
  may change the migration version scheme; re-check before numbering the
  migration.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/041-codex-read-guard-hook.md)"$'\n\nExecute this task in the current project.'
```

## Completion notes (2026-09-20)

Implemented classification A's Codex Bash adapter as `meridian hook read-guard
--host codex`, distributed it through governed-SDD `.codex/hooks.json`, and
added migration 042. The adapter recognises only static `sed`, `cat`, bounded
`head`/`tail`, and `nl | sed` reads, calculates clamped combined effective
lines, shares the documented threshold and exemptions, and allows every unknown
or failed parse. The Claude Read hook and registrations are unchanged.

The developer completed the manual `/hooks` trust review and the final
activation smoke test in the scratch project: `cat big.txt` was denied before
execution at 401 effective lines against the 400-line budget. Verification:
`python3 -m unittest discover -s tests` (164 tests),
`python3 scripts/check_repository.py`, and `git diff --check` all passed.
