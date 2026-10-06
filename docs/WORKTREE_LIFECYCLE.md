# Bounded Worktree Lifecycle

`meridian worktree` is the host-neutral authority for routine task worktree
creation, inspection, integration, and cleanup. Hosts may authorize these exact
commands, but host policy never changes their repository, identity, path, or
state checks. Every command exits `0` on success, `2` for a blocked lifecycle
transition, and `64` for command-line usage errors.

## Commands

Routine closure uses `advance`, which the managed workflow text names. The
single-step commands below remain the documented path for diagnosis and manual
recovery.

All paths are absolute after resolution. `--project`, when supplied, must name
the current repository's primary checkout. The worktree root resolves from an
explicit `--worktree-root`, then `MERIDIAN_WORKTREE_ROOT`, then
`$XDG_CONFIG_HOME/meridian/config.json` (or
`~/.config/meridian/config.json`), then `~/.meridian/worktrees`. An explicit
value that conflicts with the environment is blocked and names both sources.
The explicit option remains available for finishing a worktree in an old root.

- `meridian worktree path <TASK-ID> --project <primary> [--format json]`
  prints the canonical repository-qualified path.
- `meridian worktree prepare <TASK-ID> --project <primary> [--base main]
  --format json` creates both the canonical branch and
  worktree, or selects the exact existing pair. Partial or mismatched state is
  retained and blocked. The result contains `branch`, `worktree`,
  `worktree_root`, `base_commit`, `task_commit`, `created`, and `next_action`.
  Its lifecycle state records `started_at` as an ISO-8601 UTC timestamp when it
  first creates the worktree; repeat preparation preserves that value. Older
  state files without it remain valid and report timing as unavailable.
  With `--resume`, `prepare` also accepts an existing canonical worktree of that
  task that has uncommitted changes. Only the console's Resume directive for a
  dirty worktree uses it; ordinary preparation still refuses a dirty worktree.
  A resume never creates, moves, removes, resets, stages, or commits anything,
  leaves `started_at` and `base_commit` as recorded, and refuses when the task
  has no worktree, on every mismatch ordinary preparation blocks, and while an
  integration lease or staged merge names the task. It adds `resumed: true`,
  `dirty`, `changed_paths`, and `untracked_paths` (counts only, never names or
  contents) to the result; a dirty result has `next_action` `inspect-dirty`, and
  `check` then reports `dirty-worktree` and no other error. The agent reads
  `git status` and the diff before continuing.
- `meridian worktree check <TASK-ID> --project <primary> --format json` is
  read-only. It succeeds only inside the exact prepared
  worker directory and reports repository, path, branch, HEAD, base, clean
  state, handoff-state consistency, active integration state, errors, and the
  next action. `wrong-worktree` is distinct from registration, branch, state,
  and cleanliness failures.
- `meridian worktree evidence <TASK-ID> --project <primary>
  --validation-command <command> --validation-exit-code <code> --accepted
  --format json` records the task and base commits plus changed paths from Git
  in an untracked lifecycle-state JSON file. Repeat each validation option for
  every completed command. It records results supplied by the agent and never
  executes a validation command.
- `meridian worktree advance <TASK-ID> --project <primary> --format json
  [--validation-command <command> --validation-exit-code <code>]... [--accepted]
  [--candidate-command <command> --candidate-exit-code <code>]...`
  runs from the primary checkout. It evaluates `closure-status` and performs
  each mechanical step whose preconditions hold: C5 records evidence from the
  supplied results with the logic of `evidence` (`--accepted` and exit code `0`
  for every command are required, otherwise it stops with `ACCEPTANCE_UNMET` or
  `VALIDATION_FAILED`), C6 runs `integrate stage`, and C10 runs `cleanup`. It
  returns one JSON object with `step`, `action_required`, `commands`,
  `stop_code`, `resume`, and the `performed` steps. `action_required` is
  `run-validation` (C1-C2 and missing results), `run-candidate-validation`
  (C7; `commands` lists `git diff --check` and the declared fragments for the
  staged outcome), `push` (C9; the agent runs `git push origin main`), `human`
  (a registered stop with `human_decision: true`), `resolve` (any other
  registered stop; follow `resume`), or `none` (closure is done). It exits `2`
  on a stop and `0` when the agent only has to act. It never runs a command
  that the agent supplied, never changes into the worktree, and a rerun
  continues from the derived state without repeating a completed step.
  At C7, supplied `--candidate-command` and `--candidate-exit-code` pairs are
  the agent's candidate validation results. When every exit code is `0` and
  every command that the staged outcome requires is present, `advance` writes
  the candidate-bound evidence file (the schema above, bound to the staged
  `candidate_tree`), runs `integrate finalize` (C8), and returns `push` for
  `git push origin main`. A non-zero exit code stops with
  `CANDIDATE_VALIDATION_FAILED`, and a missing required command stops with
  `UNDECLARED_VALIDATION_COMMANDS` and lists the commands to run; both run
  `integrate abort` first and never finalize on partial evidence. A candidate
  tree that changed after stage stops with `EVIDENCE_MISMATCH` and leaves the
  staged merge for `integrate abort` and a restage. A rerun after an
  interruption between finalize and push returns `push` again.
- `meridian worktree closure-status <TASK-ID> --project <primary> [--format json]`
  is read-only. It reports the next closure `step`, any `stop_reason`, and a
  `resume` command from the registered worktree, lifecycle files, and Git
  history. Text-mode blocked results print `BLOCKED <CODE>: <detail>; resume: <command>`.
  Every CLI stop is emitted through one helper that accepts only codes listed in
  `capabilities/stop-codes-v1.json`.
  After finalization, it reports `PUSH_PENDING` at C9 when local `main` is
  ahead of the already fetched `origin/main`.
  When the recorded `<id>.evidence.json` is accepted, passed, and names the
  branch's current commit, it reports step `C6` with the `integrate stage`
  command instead of `EVIDENCE_INCOMPLETE`.
- `integrate stage` requires the primary checkout to be clean and on `main`, with
  `main` equal to the already fetched `origin/main` or ahead of it with commits
  not yet pushed; those commits are pushed with the integration. It stops with
  `MAIN_BEHIND_ORIGIN`, naming the local and fetched commits, only when local
  `main` is behind the fetched `origin/main`.
- `meridian worktree integrate stage <TASK-ID> --project <primary>
  --evidence <handoff.json> --format json` atomically
  acquires the repository integration lease, verifies the task and accepted
  validation evidence, performs `git merge --no-ff --no-commit`, then
  reads the project's `PROJECT_WORKFLOW.md` mode lock, then deterministically
  completes its known queue rows. Lean Delivery also completes the matching
  `PROJECT_PLAN.md` row; Governed SDD has no plan requirement and changes a
  `NOT_REQUIRED` review row to `ACCEPTED`. For Governed SDD, the containing
  table is recognized by named `ID` and `Status` columns, in any order; stage
  changes only that status cell. If it has no `Review` column, the task record
  supplies `REQUIRED` or `NOT REQUIRED`. Missing required columns, duplicate or
  missing IDs, mismatched row cells, and unknown statuses remain blocked without
  changing lifecycle records. A `REQUIRED` row becomes `ACCEPTED` only when its
  merged review record's latest attempt is `APPROVE`; otherwise stage reports
  `REVIEW_PENDING`, retains its status, and still relinks an archived task
  record. A task record with `Class: SPIKE` needs no review record: stage sets its
  row to its terminal `ANSWERED` or `INCONCLUSIVE` status. A spike may integrate
  only its task record or exact archive rename, handoff, ADR log, documentation
  paths named in its deliverable, and changelog fragments; any other task diff
  path blocks stage before a lease or merge. Any fully closed section moves to
  `tasks/QUEUE_ARCHIVE.md` using that
  mode's template table shape, creating it when needed; a project-shaped
  Governed section is not archived. It returns `REUSE`, `BOUNDED`, or `FULL`
  with the exact candidate tree. Unknown row or section shapes are blocked
  without changing the candidate's lifecycle records.
- `meridian worktree integrate finalize <TASK-ID> --project <primary>
  --evidence <candidate-validation.json> --format json` creates the fixed merge
  commit only when successful evidence matches the staged candidate and
  required validation scope.
- `meridian worktree integrate abort <TASK-ID> --project <primary> --format
  json` aborts only the requested Meridian-owned merge and releases its lease.
- `meridian worktree cleanup <TASK-ID> --project <primary> --format json`
  removes the clean canonical worktree and non-force
deletes its merged branch only after local integration and, when an origin
  exists, pushed `main` are proven.

Existing worktrees in a previous root are never moved or deleted
automatically. Finish them in place and pass that old root explicitly to
`check`, integration staging, and `cleanup`; new work resolves to the current
machine-level root.

`meridian codex worktree-path` is a deprecated alias for `meridian worktree
path` for one migration window. It prints a deprecation notice to standard
error; new automation must use the host-neutral form.

The absolute worktree path is a runtime value and is never written to a tracked
file. `path`, `prepare`, and `check` also return `handoff_worktree`, the path
relative to the worktree root (for example `github.com/<owner>/<repository>/task-<n>`),
which is the value completion handoffs record. Resolving it against the worktree
root yields the same path on every machine. A repository without a usable remote
uses a local name plus a Git-common-directory hash, so its value is stable only
on the machines that share that hash. `check` also accepts a legacy absolute
`Worktree:` value in an existing handoff.

## Lifecycle journal

`prepare`, `check`, `closure-status`, `advance`, `evidence`, `integrate stage`,
`integrate finalize`, `integrate abort`, and `cleanup` each append one JSON line
to `<git-common-dir>/meridian-journal.jsonl`; the Claude Code `Stop` hook
(`hook stop-audit`) appends one line per unbacked or declared `BLOCKED` code. The file is local and untracked,
and every worktree of the repository shares it, so the lines of concurrent tasks
interleave as whole lines. The read-only commands
(`check`, `closure-status`, and `prepare --resume`) append to it too; the journal
is not lifecycle state, so they still change no lifecycle state. It exists to measure how often the lifecycle stops
and where, not to audit an agent.

| Field | Meaning |
|-------|---------|
| `version` | Always `1`. |
| `ts` | UTC time of the result, `YYYY-MM-DDTHH:MM:SSZ`. |
| `command` | The command name, for example `integrate stage`. |
| `task` | The canonical task ID, when the argument or the result names one. |
| `step` | The closure step or `next_action` the command reported, when it reports one. |
| `result` | `ok` (exit `0`), `blocked` (a stopped lifecycle transition), or `error`; the Stop hook adds `unbacked_block` and `declared_block` (see below). |
| `stop_code` | The registered stop code, only when `result` is `blocked` and the stop carries one. |
| `exit` | The command's exit status. |
| `resume` | `true` only on a `prepare --resume` run. |

Privacy boundary: a line holds only these fields. It never contains an absolute
path, a command line or option value supplied by the agent, a message, or error
text; a stop is recorded by its registered code, never by its message.

### Unbacked stop reports

The Claude Code `Stop` hook (`hooks/stop-audit.sh`, 5 second timeout) runs
`meridian hook stop-audit`. It reads only the final assistant message, from the
`last_assistant_message` field of the hook input (documented for `Stop`), and
falls back to the last assistant entry of `transcript_path`. For each registered
`BLOCKED <CODE>` at the start of a line it looks for a `blocked` journal line
with the same code since the session's first transcript timestamp (24 hours
when unavailable), restricted to the active task when the hook runs in a registered task worktree
(resolved as `meridian worktree active` does; from the primary checkout the
line is not task-scoped and records `task: null`). A `tool` code with no match is appended as `result:
unbacked_block`; a `command-exit` or `judgment` code is appended as
`declared_block`, because no command emits it. The line holds `stop_code` and
`task` only. The hook ignores unregistered codes, does nothing outside a
Meridian project or without an existing journal, never blocks the stop, and
always exits `0`. Codex documents a `Stop` event that also carries
`last_assistant_message`, but this hook is registered for Claude Code only and
Codex configuration is deliberately unchanged.

The journal is rotated to `meridian-journal.1.jsonl` when it exceeds 5 MB, and
only that one previous file is kept. A journal write that fails never changes a
command's result or exit status; the command prints one warning to standard
error.

### Flow report

`meridian report flow [--project <primary>] [--since YYYY-MM-DD] [--format
text|json]` reads the current and the rotated journal and changes nothing. It
reports, per task, the lead time from the first successful `prepare` to the
successful `integrate finalize` (falling back to the lifecycle `started_at` only
when the journal holds no `prepare` for the task), the stops by code, the
`integrate abort` runs, and the `prepare --resume` runs. It totals them with the
median lead time and groups stops by code and by the class in
`capabilities/stop-codes-v1.json`; a `blocked` line without `stop_code` is
`uncoded`. `--since` filters records by time; a task's lead time still uses its
whole history. Malformed lines are counted and skipped; an empty or missing
journal gives an empty report and exit status `0`.

A task may declare `> **Origin**: capability | friction | maintenance | release`
in its record or archive; the report gives each origin's share and counts a task
without it as `unknown`. `friction` means the task fixes a problem that
Meridian's own rules or tools caused.

`.meridian/flow-targets.json` (version 1) declares targets before any data
exists, so the data cannot shape them: `unbacked_blocks` (`window`, `max`),
`lead_time_regression` (`window`, `max_percent`; the median of the last `window`
integrated tasks against the `window` before them), and `friction_share`
(`window`, `max_percent`; over the last `window` integrated tasks that declare
an origin). Windows count tasks, not days, so `--since` does not change them.
Each target prints as `met`, `missed`, or `insufficient data`; a missed target
never changes the exit status, and a missing file shows only the measurements.
Change a declared value only through a separate, recorded decision.

The report also lists the registered `tool`-class stop codes not emitted in the
period, with the period length. They are candidates for removal, not a decision:
some gates guard rare but real conditions.

## Evidence boundary

### External validation evidence

`schemas/validation-evidence-v1.schema.json` defines an attestation for a
validation run that completed outside the agent host. Verify it without running
the recorded command with:

```text
meridian validation check <record.json> --project <primary> [--commit <sha>] --format json
```

The command uses only read-only Git plumbing and returns JSON with one of
`VALIDATION_PASSED`, `VALIDATION_RUNNING`, `VALIDATION_UNAVAILABLE`, or
`VALIDATION_FAILED`, its level, and field-specific reasons. Passed exits zero;
running or unavailable exits one; failed or invalid exits two.

Every record binds its command, result, test count, commit, and commit tree.
Its state is `running`, `unavailable`, `failed`, or `passed`. The three levels
are `T1_CI` (a successful CI run for that commit), `T2_SHARDED` (a complete,
consistent shard coverage proof), and `T3_ATTESTED` (a dated developer
statement). Each level states what evidence was supplied; none is an
unforgeable proof. A passed record also requires exit code zero, a positive test
count, and level-specific evidence: CI conclusion and head SHA, complete shard
indexes and matching digest/total, or a developer/date/statement respectively.

Stage evidence is a JSON object with these required fields:

```json
{
  "accepted": true,
  "validation_passed": true,
  "validated_task_commit": "<40-hex-object-id>",
  "validated_base_commit": "<40-hex-object-id>",
  "full_validation_required": false,
  "interaction_assessment_complete": true,
  "task_paths": ["path/owned-by-task"],
  "task_dependencies": [],
  "task_behavioral_surfaces": [],
  "main_advanced_dependencies": [],
  "main_advanced_behavioral_surfaces": []
}
```

`worktree evidence` also writes `validation_commands` and
`validation_exit_codes`. These fields are optional for hand-written legacy
evidence. During staging, Git is authoritative for task paths and paths that
`main` changed since the validated base. Declared task paths can expand that
surface; typed `main_advanced_*` fields can require `FULL` validation but
cannot reduce the scope selected from Git.

Candidate validation runs outside the lifecycle command in the ordinary
sandbox. Its JSON object contains the returned `candidate_tree`, `passed:
true`, `scope` (`bounded` or `full`), and a non-empty `commands` array. The
required gate for each `REUSE`, `BOUNDED`, or `FULL` decision is defined below.
Lifecycle commands never execute shell, hook, validation, smoke, or
project-provided commands.

### Candidate validation by integration outcome

The consumer-owned `.meridian/candidate-validation.json` declares command
fragments per `REUSE`, `BOUNDED`, and `FULL` outcome. It has `version: 1` and
one state: `declared` with a non-empty fragment array for every outcome, `none`
to accept any non-empty successful command list, or `undeclared`. A missing
file is also `undeclared`. The comparison is literal and executes nothing; it
accepts a `set -o pipefail;` prefix and output-bounding pipelines because the
declared fragment remains in the command entry.

An undeclared project stops at `integrate stage`, before a lease, merge, or
staged state exists, with `BLOCKED UNDECLARED_VALIDATION_COMMANDS`. The stop
shows the task validation commands and a detected-stack proposal. Explicitly
write declared fragments, choose `none`, or use `meridian setup --apply` after
reviewing its proposal, then rerun stage. `upgrade --apply` never writes this
consumer-owned file. This repository's own fragments live only in its
`.meridian/candidate-validation.json`.

- `REUSE` runs the project's declared repository gate and proves that the staged candidate differs
  from the validated task commit only in governance paths. Use the deterministic
  command `git diff --name-only "$VALIDATED_TASK_COMMIT" "$CANDIDATE_TREE"` and
  verify that every emitted path is the task record (active or its exact archive
  rename), that task's handoff, `tasks/QUEUE.md`, `PROJECT_PLAN.md`,
  `tasks/QUEUE_ARCHIVE.md`, or that task's changelog fragment. Any other path
  requires a `BOUNDED` or `FULL` outcome; it is not a valid `REUSE` proof.
- `BOUNDED` runs the `REUSE` gate and the tests for modules changed by both the
  task and advanced `main`. Select those tests from the staged candidate's
  changed-path evidence; the independent-change decision never permits omitting
  either side's affected modules.
- `FULL` runs the `REUSE` gate and the project's declared full suite. Its candidate evidence
  therefore records both the repository check and full-suite command.

A stricter gate is always permitted: an agent may run the full suite for any
outcome, and neither the lifecycle command nor this policy rejects it.
Missing, failed, stale, or mismatched evidence is blocked without creating a
merge commit. Every candidate evidence record, including one under a `none`
declaration, must include `git diff --check`.

Lifecycle state is stored under the repository's absolute Git common
directory. Interruptions retain enough ownership and candidate identity for
`check`, `integrate abort`, or an idempotent retry. Stale leases, force deletes,
abandoned branches, and arbitrary paths have no routine command and require an
explicitly authorized exceptional recovery outside the allowlisted surface.

When integration reports `PRIMARY_DIRTY`, it lists the staged or modified paths
(bounded to ten). A sole `.meridian/budget.json` entry is identified as the
legacy budget file; commit its deletion before rerunning stage.

After validation, `integrate stage` permits lifecycle changes only to the task
record, its queue row, handoff, review record, `PROJECT_PLAN.md`, and
`tasks/QUEUE_ARCHIVE.md`. A task record may be archived only as an exact
100%-similarity Git rename from its active path to `tasks/done/` with the same
file name. A task already archived at validation needs no rename; an active
task may otherwise change only its active record path. Deletions, separate
additions, changed-content renames, other destinations, and records belonging
to another task are blocked before lifecycle state is written.
