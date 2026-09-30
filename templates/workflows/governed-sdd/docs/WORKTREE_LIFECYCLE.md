# Bounded Worktree Lifecycle

Use the host-neutral `meridian worktree` namespace for task checkout lifecycle
operations. Commands exit `0` on success, `2` when blocked, and `64` on usage
errors.

- `path <TASK-ID> --project <primary> --worktree-root <root> [--format json]`
  derives the canonical path.
- `prepare <TASK-ID> --project <primary> --worktree-root <root> --format json`
  creates or selects the exact branch/worktree pair before any worker starts.
- `check <TASK-ID> --project <primary> --worktree-root <root> --format json`
  is read-only and must be the implementer, reviewer, or remediation worker's
  first action in that same prepared directory.
- `integrate stage <TASK-ID> --project <primary> --worktree-root <root>
  --evidence <handoff.json> --format json` owns the lease and no-commit merge
  and returns `REUSE`, `BOUNDED`, or `FULL` plus the candidate tree.
- Run the selected validation outside the lifecycle command, then use
  `integrate finalize <TASK-ID> --project <primary> --evidence
  <candidate-validation.json> --format json`, or `integrate abort` on failure.
- `cleanup <TASK-ID> --project <primary> --worktree-root <root> --format json`
  removes only a clean, integrated, pushed worktree and non-force-deletes its
  merged branch.

Stage evidence records acceptance, successful validation, full validated task
and base object IDs, the full-validation flag, a complete advanced-main
assessment flag, and arrays for task paths, dependencies, behavioral surfaces,
and matching advanced-main identities. Candidate evidence records the exact
candidate tree, `passed: true`, the required `bounded` or `full` scope, and the
successful commands. The CLI rejects stale or incomplete evidence and never
executes project-provided commands.

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
