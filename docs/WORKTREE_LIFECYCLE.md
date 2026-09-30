# Bounded Worktree Lifecycle

`meridian worktree` is the host-neutral authority for routine task worktree
creation, inspection, integration, and cleanup. Hosts may authorize these exact
commands, but host policy never changes their repository, identity, path, or
state checks. Every command exits `0` on success, `2` for a blocked lifecycle
transition, and `64` for command-line usage errors.

## Commands

All paths are absolute after resolution. `--project`, when supplied, must name
the current repository's primary checkout. `--worktree-root` must equal
`MERIDIAN_WORKTREE_ROOT` when that environment variable is set.

- `meridian worktree path <TASK-ID> --project <primary> --worktree-root <root>
  [--format json]` prints the canonical repository-qualified path.
- `meridian worktree prepare <TASK-ID> --project <primary> --worktree-root
  <root> [--base main] --format json` creates both the canonical branch and
  worktree, or selects the exact existing pair. Partial or mismatched state is
  retained and blocked. The result contains `branch`, `worktree`,
  `worktree_root`, `base_commit`, `task_commit`, `created`, and `next_action`.
- `meridian worktree check <TASK-ID> --project <primary> --worktree-root <root>
  --format json` is read-only. It succeeds only inside the exact prepared
  worker directory and reports repository, path, branch, HEAD, base, clean
  state, handoff-state consistency, active integration state, errors, and the
  next action. `wrong-worktree` is distinct from registration, branch, state,
  and cleanliness failures.
- `meridian worktree integrate stage <TASK-ID> --project <primary>
  --worktree-root <root> --evidence <handoff.json> --format json` atomically
  acquires the repository integration lease, verifies the task and accepted
  validation evidence, performs only `git merge --no-ff --no-commit`, and
  returns `REUSE`, `BOUNDED`, or `FULL` with the exact candidate tree.
- `meridian worktree integrate finalize <TASK-ID> --project <primary>
  --evidence <candidate-validation.json> --format json` creates the fixed merge
  commit only when successful evidence matches the staged candidate and
  required validation scope.
- `meridian worktree integrate abort <TASK-ID> --project <primary> --format
  json` aborts only the requested Meridian-owned merge and releases its lease.
- `meridian worktree cleanup <TASK-ID> --project <primary> --worktree-root
  <root> --format json` removes the clean canonical worktree and non-force
  deletes its merged branch only after local integration and, when an origin
  exists, pushed `main` are proven.

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

Candidate validation runs outside the lifecycle command in the ordinary
sandbox. Its JSON object contains the returned `candidate_tree`, `passed:
true`, `scope` (`bounded` or `full`), and a non-empty `commands` array. Missing,
failed, stale, or mismatched evidence is blocked without creating a merge
commit. Lifecycle commands never execute shell, hook, validation, smoke, or
project-provided commands.

Lifecycle state is stored under the repository's absolute Git common
directory. Interruptions retain enough ownership and candidate identity for
`check`, `integrate abort`, or an idempotent retry. Stale leases, force deletes,
abandoned branches, and arbitrary paths have no routine command and require an
explicitly authorized exceptional recovery outside the allowlisted surface.
