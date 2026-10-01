# Task 097 — Let a manually typed `Proceed with` prepare its own worktree in Governed SDD

> **ID**: `097`
> **Category**: Workflow template
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Developer report on F1-TREAT-001 in the palimpsest project (third occurrence)

## Objective

In Governed SDD, `docs/workflows/IMPLEMENTATION.md` says the coordinator runs
`meridian worktree prepare` and starts the implementer in the prepared
directory. When the developer types `Proceed with <TASK-ID>` into a session
opened in the primary checkout, no coordinator exists, `meridian worktree
check` correctly answers `missing-state`, `wrong-worktree`, and
`unregistered-worktree`, and the implementer stops. This happened for
M37-CAUSE-001, F1-FIGURE-001, and F1-TREAT-001, and each time the developer
prepared the worktree by hand.

Change the implementation procedure so that, when no coordinator supplied the
prepared worktree, the implementer prepares it for exactly the assigned task
and continues in it, as the Lean Delivery workflow already does. Ship the change
to adopters as a migration.

## Acceptance Criteria

- [ ] `templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md`
  states, inside the `task-worktree-boundary` capability (bumped one version),
  two start modes:
  - **Coordinator-launched** (a coordinator supplied the branch, absolute
    worktree path, primary checkout, and worktree root): unchanged. Start in that
    exact directory and run `meridian worktree check` before any task read.
  - **Manually triggered** (no such launch inputs): before reading the task,
    its handoff, implementation files, or any diff, the implementer determines
    the primary checkout as the first entry of `git worktree list --porcelain`,
    runs `meridian worktree prepare <TASK-ID> --project <primary-checkout>
    --format json` for exactly the task ID in the trigger, and then runs
    `meridian worktree check` for the returned worktree.
- [ ] The manual mode is bounded by these rules, all stated in the template:
  any non-zero result from `prepare` (partial or mismatched state, an existing
  active writer, an unresolvable task ID) stops the work as `BLOCKED` with the
  command's message reported verbatim and nothing else changed; `prepare` is the
  only command run before `check` passes; the task ID is never inferred, only
  taken from the trigger; no `--worktree-root` is passed, so the resolved root
  applies; and after a successful `check` every later read, write, validation,
  status, and handoff operation runs with the prepared worktree as its working
  directory and never in the primary checkout.
- [ ] If the host cannot run commands or write in the prepared directory (for
  example a sandbox that does not cover the worktree root), the implementer
  stops as `BLOCKED`, names that exact directory, and tells the developer to
  restart the session there. It does not fall back to the primary checkout.
- [ ] `Review <TASK-ID>` and `Address review <TASK-ID>` are unchanged: they
  never run `prepare` and stop as `BLOCKED` when the registered worktree is
  missing. A test asserts that the review and remediation procedure files are
  byte-identical to their previous versions.
- [ ] `PROJECT_WORKFLOW.md` (`bounded-worktree-lifecycle`) says that the
  coordinator runs `prepare` for coordinator-launched work and that a manually
  typed `Proceed with` follows the rule in `docs/workflows/IMPLEMENTATION.md`;
  its capability version is bumped. The `Run lifecycle` coordinator text and the
  prohibition on host-created substitute checkouts stay.
- [ ] A migration, numbered after the newest existing migration, advances those
  two capabilities, lists `docs/workflows/IMPLEMENTATION.md` and
  `PROJECT_WORKFLOW.md` as managed paths, and has a `delta` and `verification`
  list in the style of migrations `051` and `055`. Capability marker baselines
  are updated through `python3 scripts/check_repository.py
  --write-marker-baselines` and the diff of that file is reviewed.
- [ ] Upgrade tests prove that a project at the previous capability versions
  reaches the new ones with `upgrade --apply` and keeps its consumer-owned text,
  and that a project with a customized `IMPLEMENTATION.md` gets a bounded
  conflict instead of a silent overwrite.
- [ ] Release bookkeeping follows the precedent of migration `055`: `VERSION`
  and `.claude-plugin/plugin.json` move to the next patch version after the
  current release (verified at task time), `releases/<version>.json` is added
  with `baselineChanged: true` and the migration id, and `CHANGELOG.md` gets a
  `## [<version>]` section starting with `Template-changing release` and a
  non-empty `### Upgrade notes` subsection. The notes name the affected
  capabilities and files, the action (`meridian upgrade --apply`), the likely
  conflict area (a locally edited `IMPLEMENTATION.md`), and that open agent
  sessions must be restarted to read the new rule.
- [ ] No change is made to the `meridian worktree` commands, the Lean Delivery
  templates, or the console.
- [ ] If implementing the rule needs a CLI change, a change to the integration
  gate, or a host-specific mechanism, the task stops and reports instead of
  deciding.
- [ ] `python3 scripts/check_repository.py` and
  `python3 -m unittest discover -s tests` pass.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md` | `task-worktree-boundary` capability text. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md` | `bounded-worktree-lifecycle` capability text. |
| `migrations/` | New migration; style reference `051-bounded-worktree-lifecycle.json`, `055-unified-worktree-root-and-setup.json`. |
| `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json` | Regenerated marker baselines. |
| `tests/test_meridian_cli.py` | Upgrade and template tests. |
| `docs/WORKTREE_LIFECYCLE.md` | Reference for `prepare` and `check` semantics; edit only if its wording contradicts the new rule. |
| `VERSION`, `.claude-plugin/plugin.json`, `releases/`, `CHANGELOG.md` | Release bookkeeping. |

## Technical Context

- **Observed**: palimpsest is at framework `1.1.49` and carries
  `task-worktree-boundary` v3 ("The coordinator runs `meridian worktree
  prepare` before starting this worker"). The current template carries v4 with
  the same coordinator wording, so the gap is in the template, not only in an
  old baseline, and an upgrade alone does not fix it.
- `meridian worktree prepare` creates the canonical branch and worktree or
  selects the exact existing pair and retains and blocks partial or mismatched
  state. `meridian worktree check` succeeds only from inside the exact prepared
  directory.
- The Lean Delivery template already says that for `Proceed with <TASK-ID>` the
  agent creates or selects the deterministic task branch and worktree.
- The Governed review and remediation procedures must keep requiring an existing
  registered worktree: the reviewer must not create the branch the implementer
  is supposed to have produced.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- Evidence tier: template text, capability versions, migration records, and
  upgrade results are structural and asserted by tests; no manual evidence is
  required. Whether a live agent follows the new text is not tested here and is
  recorded as unverified in the handoff.

## Out of scope

Making the console prepare worktrees or start the agent in the prepared
directory (Task 077's assumption that the directive prepares the worktree is now
true for manual and console launches alike once this ships), publishing the
release, changing the release command, and changing `Review` or `Address review`.

## Dependencies

- **Depends on**: 051, 055
- **Blocks**: none
