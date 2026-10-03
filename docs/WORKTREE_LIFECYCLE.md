# Bounded Worktree Lifecycle

`meridian worktree` is the host-neutral authority for routine task worktree
creation, inspection, integration, and cleanup. Hosts may authorize these exact
commands, but host policy never changes their repository, identity, path, or
state checks. Every command exits `0` on success, `2` for a blocked lifecycle
transition, and `64` for command-line usage errors.

## Commands

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
- `meridian worktree closure-status <TASK-ID> --project <primary> [--format json]`
  is read-only. It reports the next closure `step`, any `stop_reason`, and a
  `resume` command from the registered worktree, lifecycle files, and Git
  history. Text-mode blocked results print `BLOCKED <REASON>; resume: <command>`.
  After finalization, it reports `PUSH_PENDING` at C9 when local `main` is
  ahead of the already fetched `origin/main`.
  When the recorded `<id>.evidence.json` is accepted, passed, and names the
  branch's current commit, it reports step `C6` with the `integrate stage`
  command instead of `EVIDENCE_INCOMPLETE`.
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
  record. Any fully closed section moves to `tasks/QUEUE_ARCHIVE.md` using that
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
merge commit.

Lifecycle state is stored under the repository's absolute Git common
directory. Interruptions retain enough ownership and candidate identity for
`check`, `integrate abort`, or an idempotent retry. Stale leases, force deletes,
abandoned branches, and arbitrary paths have no routine command and require an
explicitly authorized exceptional recovery outside the allowlisted surface.

After validation, `integrate stage` permits lifecycle changes only to the task
record, its queue row, handoff, review record, `PROJECT_PLAN.md`, and
`tasks/QUEUE_ARCHIVE.md`. A task record may be archived only as an exact
100%-similarity Git rename from its active path to `tasks/done/` with the same
file name. A task already archived at validation needs no rename; an active
task may otherwise change only its active record path. Deletions, separate
additions, changed-content renames, other destinations, and records belonging
to another task are blocked before lifecycle state is written.
