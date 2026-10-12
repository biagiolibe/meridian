# Task 204 — Record execution start and verified review delivery

> **ID**: `204`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: Explicit execution-boundary discussion, 2026-10-12
> **Origin**: friction

## Objective

Add `meridian execution start <TASK-ID>` as the worker's explicit start step:
prepare the assigned worktree, verify it, validate the execution contract,
then record execution start before substantive analysis or implementation.
Console-launched, manually triggered, and orchestrated workers follow the
same sequence. Advisor consultation is substantive task work, but Meridian
must not intercept, recognize, or gate advisor calls or other host tools.

Define the matching end boundary for Review-required Governed SDD tasks:
finish implementation and validation, commit the implementation, finalize
and commit the handoff, verify readiness, then publish and commit the
`READY_FOR_REVIEW` transition as the last delivery step. The implementer
stops writing after successful delivery. Review availability must not mean
that the implementer has merely begun preparing its completion report.

## Acceptance Criteria

- [x] `meridian execution start <TASK-ID> --project <task-worktree>` verifies
  that the caller is in the assigned canonical worktree and validates the
  current execution contract before changing task state. Reuse existing
  worktree, contract, and state readers and coded stops, not a new authority.
- [x] For a Governed SDD task in `QUEUED`, successful start records the legal
  `IN_PROGRESS` transition, current HEAD, and UTC timestamp through the
  existing command-owned transition mechanism and updates the task-record
  projection. Do not edit the primary queue, plan, review verdict, or another
  task's state.
- [x] Repeated start or Resume of an `IN_PROGRESS` task is idempotent:
  preserve transitions and the original start timestamp. Retain existing
  explicit Resume authorization and dirty-worktree rules; never silently
  tolerate unrelated changes or another writer. Remediation and review
  states follow their existing lifecycle, not an automatic reset caused by
  launching a session.
- [x] Wrong worktree, unresolved contract, invalid state, or ineligible
  lifecycle state stops before start writes. Failed preflight creates no
  start transition. Terminal tasks cannot be restarted.
- [x] Preserve Lean Delivery's existing state machine and worktree-derived
  in-progress behavior. Do not add `IN_PROGRESS` to the Lean machine as a
  side effect; document the command's compatible behavior for that workflow.
- [x] Managed worker instructions place start immediately after successful
  worktree verification and contract resolution, before substantive
  authority/source analysis, advisor consultation, or implementation.
  Minimal metadata and contract reconciliation needed to pass start remain
  allowed. Checkout creation or agent-pane launch alone never records start.
  Console directives, manual `Proceed with`, and orchestrator worker prompts
  use this same ordering. Read-only review/status requests never start work.
- [x] Add an explicit delivery operation, proposed as
  `meridian execution deliver <TASK-ID> --project <task-worktree>`, for
  Review-required Governed tasks. It checks the canonical worktree, legal
  state, completed validation evidence bound to the implementation commit,
  and final committed handoff through the existing readiness machinery
  before publishing `READY_FOR_REVIEW`. A dirty worktree, incomplete handoff,
  missing implementation commit, or stale evidence cannot publish review
  availability. `execution ready-check` remains read-only.
- [x] Delivery uses the existing transition authority and makes the final
  task-local delivery commit containing state and owned projections only;
  it neither commits implementation changes opportunistically nor pushes,
  merges, reviews, or accepts the task. Report the final committed HEAD and
  successful clean-worktree check. Respect the existing convention for
  self-referential handoff commits: do not require the handoff to name a
  commit that does not yet exist. No new evidence schema is needed merely
  to accommodate the delivery commit.
- [x] An ordinary `task transition ... READY_FOR_REVIEW` cannot bypass the
  same delivery-readiness prerequisites. If transition writes or its final
  commit fails, report the actual remaining state and recovery action, not
  successful delivery. Repeating delivery on the already clean, committed,
  valid delivery is idempotent and preserves timestamps and history.
- [x] The console reads machine state, not prose or agent-activity guesses.
  `IN_PROGRESS` remains visible from task-local uncommitted state immediately.
  Review is offered only for a valid committed `READY_FOR_REVIEW` delivery
  and a clean canonical worktree. An uncommitted ready transition or later
  dirty worktree is labeled as pending delivery/changes and cannot launch
  review; distinguish this availability condition from the authoritative
  lifecycle status rather than silently rewriting or downgrading it.
- [x] Managed instructions for manual, console-launched, and orchestrated
  implementations use the final delivery step only after code, validation,
  and handoff are complete; no later implementer writes are prescribed.
  The reviewer still performs its existing independent preflight. This
  boundary does not detect process exit or prevent an agent from ignoring
  instructions. Subsequent code changes must still invalidate stale evidence
  through the existing review/integration rules.
- [x] Ship managed instructions through versioned capabilities, marker
  baselines, a migration, skill parity, and next-release metadata according
  to `CONTRIBUTING.md`. Upgrade notes explain start, Resume, final delivery,
  pending-delivery display, and session restart. Prepare the
  template-changing release; do not publish it.
- [x] Focused tests cover first/repeated start, Resume, worktree and contract
  failure without writes, terminal/ineligible states, Lean compatibility,
  console refresh from uncommitted task-local state, and instruction ordering
  across worker entry paths without relying on advisor implementation.
- [x] Delivery tests cover incomplete/uncommitted handoffs, dirty worktrees,
  stale validation, direct-transition bypass attempts, final commit failure,
  successful lifecycle-only commit, repeated delivery, and the console's
  pending-versus-reviewable distinction. Preserve SPIKE and review-not-required
  closure; do not route them through a fabricated review state.
- [x] Repository checks, full parallel tests, self-hosting CI audit, and
  `git diff --check` pass. Add one changelog fragment with upgrade notes.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py`, `scripts/task_state.py` | Start/delivery commands and existing worktree/readiness/transition authority. |
| `scripts/project_console.py`, `scripts/console_workflow.py` | Launch directives, authoritative refresh, and review availability. |
| `templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md`, `templates/workflows/governed-sdd/docs/LIFECYCLE_ORCHESTRATION.md` | Manual and coordinated worker start ordering. |
| `templates/workflows/lean-delivery/`, `skills/` | Compatible Lean behavior and Claude/Codex parity. |
| `docs/WORKTREE_LIFECYCLE.md`, corresponding templates and governed review procedure | Shared start/delivery ordering and independent reviewer preflight. |
| `migrations/`, marker baselines, release metadata | Versioned managed-text delivery. |
| `tests/test_meridian_cli.py`, `tests/test_task_worktree_isolation.py`, `tests/test_project_console.py`, focused execution-boundary tests | Behavioral and instruction-order evidence. |

## Technical Context

- Authority: `docs/ADR_MACHINE_TASK_STATE.md`, Decisions 1, 2, and 4;
  `PROJECT_WORKFLOW.md` worktree boundary and governance-file ownership;
  `CONTRIBUTING.md` release procedure.
- Observed on Palimpsest `F2-SCENE-001`: imported state remained `QUEUED`
  while the developer reported substantive work, including advisor
  consultation. The console correctly followed the state; the agent
  recorded `IN_PROGRESS` later. Instructions prescribe the transition but
  do not put it in a distinct early start operation.
- The same task entered `READY_FOR_REVIEW` at 21:02:57 Europe/Rome on
  2026-10-12, with transition HEAD still `d0a79fa`, immediately before the
  implementation commit `dde850b`. Handoff completion followed in `8dd6186`
  at 21:06:07. This establishes a premature delivery indication; it does
  not establish that production code continued changing after the transition.
- `task transition` currently validates state-machine legality, while
  `execution ready-check` is a separate operation. The console follows the
  ready state even while the implementer is still completing delivery.
- Developer decision: define a consistent start moment controlled by
  Meridian, without a host-specific advisor gate. Manual workers still need
  to follow the sequence; do not claim enforcement over all host activity.
- The first existing `IN_PROGRESS` transition is the durable start event.
  Preserve it rather than adding a competing timestamp or inferred history.

## Validation

- `python3 scripts/check_repository.py`
- `python3 scripts/run_tests.py --parallel`
- `python3 scripts/meridian.py --framework-root . audit --project . --mode lean-delivery --ci-profile meridian-self-hosting`
- `git diff --check`

## Out of scope

Advisor/tool-call gates, new host hooks, intercepting Claude internals,
automatic task selection, background activity detection, token telemetry,
completion estimates, pause-aware elapsed-time reporting, historical time
correction, changes to consumer projects, and release publication.
Do not add process-liveness monitoring, review automation, or a new
observability subsystem to solve the delivery boundary.

## Dependencies

- **Depends on**: 199, 202, 203 (completed).
- **Blocks**: none.

## Completion

Completed on 2026-10-12. Verified canonical execution start, source-bound validation and committed final delivery, pending-versus-reviewable console availability, and managed worker ordering. Lean, SPIKE, and review-not-required lifecycle behavior is preserved. Prepared version 1.2.14 and migration 067 without publishing a release. All required checks passed; see `tasks/handoffs/204.md` for evidence and the named environmental skip.
