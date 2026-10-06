# Bounded Worktree Lifecycle

<!-- MERIDIAN:BEGIN capability=worktree-lifecycle v2 -->
Use the host-neutral `meridian worktree` namespace for task checkout lifecycle
operations. Commands exit `0` on success, `2` when blocked, and `64` on usage
errors. The root resolves from an explicit option, the environment, user
configuration, or `~/.meridian/worktrees`, in that order.

- `path <TASK-ID> --project <primary> [--format json]`
  derives the canonical path.
- `prepare <TASK-ID> --project <primary> --format json`
  creates or selects the exact branch/worktree pair and returns durable worker
  launch inputs. Only a Resume directive adds `--resume`, which accepts that
  task's existing dirty worktree, creates and changes nothing, and reports
  `dirty` with `next_action` `inspect-dirty`; `check` then reports
  `dirty-worktree` and no other error.
- `check <TASK-ID> --project <primary> --format json`
  is read-only and must be the worker's first action in the prepared directory.
- `integrate stage <TASK-ID> --project <primary>
  --evidence <handoff.json> --format json` owns the lease and no-commit merge
  and returns `REUSE`, `BOUNDED`, or `FULL` plus the candidate tree.
- Run the selected validation outside the lifecycle command, then use
  `integrate finalize <TASK-ID> --project <primary> --evidence
  <candidate-validation.json> --format json`, or `integrate abort` on failure.
- `cleanup <TASK-ID> --project <primary> --format json`
  removes only a clean, integrated, pushed worktree and non-force-deletes its
  merged branch.

Legacy worktrees are never moved. Finish and clean one in its old root by
passing `--worktree-root <old-root>` explicitly.

Stage evidence records accepted and successful validation booleans, full
validated task/base object IDs, the full-validation flag, a complete advanced-
main assessment flag, and arrays for task paths, dependencies, behavioral
surfaces, and matching advanced-main identities. Candidate evidence records
the exact candidate tree, `passed: true`, the required `bounded` or `full`
scope, and the successful commands. The CLI rejects stale or incomplete
evidence, requires `git diff --check` in every candidate command list, and
never executes project-provided commands.

## Candidate validation by integration outcome

Run candidate validation outside the lifecycle command. `.meridian/candidate-validation.json`
is consumer-owned and versioned. It declares non-empty required command fragments
for every outcome (`declared`), or explicitly chooses `none`; a missing file or
`undeclared` state stops `integrate stage` before any lease or merge with
`BLOCKED UNDECLARED_VALIDATION_COMMANDS`. The stop reports the task's recorded
validation commands and a proposal; review it and write declared fragments or
`none`, or use `meridian setup --apply`. `upgrade --apply` never writes this file.
For every `REUSE`, `BOUNDED`, or `FULL` outcome, run the project's declared repository check and
`git diff --check` against the staged candidate tree. A `REUSE` outcome also
requires a deterministic proof that every non-governance path is unchanged:
run `git diff --name-only "$VALIDATED_TASK_COMMIT" "$CANDIDATE_TREE"` and allow
only the task record or its exact archive rename, that task's handoff, queue,
plan, queue archive, and changelog fragment. `BOUNDED` adds the tests for
modules changed by the task and advanced `main`; `FULL` adds the full test
suite. A project may always run the full suite for any outcome. Configure
candidate-evidence command requirements per outcome; they must match this gate.

`meridian codex worktree-path` is deprecated for one migration window. New
instructions and automation use `meridian worktree path`.

The absolute worktree path is a runtime value and is never written to a tracked
file. `path`, `prepare`, and `check` also return `handoff_worktree`, the path
relative to the worktree root (for example `github.com/<owner>/<repository>/task-<n>`),
which is the value completion handoffs record. Resolving it against the worktree
root yields the same path on every machine. A repository without a usable remote
uses a local name plus a Git-common-directory hash, so its value is stable only
on the machines that share that hash. `check` also accepts a legacy absolute
`Worktree:` value in an existing handoff.
<!-- MERIDIAN:END -->
