# Task 088 — Define how a completion handoff names commits that cannot contain their own SHA

> **ID**: `088`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: implementer
> **Session**: Developer report on the F1-FIGURE-001 review preflight in the palimpsest project

## Objective

Make the Governed SDD completion handoff state how to record a commit that
cannot name itself. A handoff committed inside the implementation commit
cannot contain that commit's SHA, and a later lifecycle-only correction
cannot contain its own SHA either. Today the `task-worktree-handoff` block asks
for a `<commit SHA>` in every commit field and gives no rule for this case.

In the palimpsest project an implementer wrote the validated base `main`
commit into `Current task commit`. The reviewer preflight correctly returned
`BLOCKED`. The implementer then concluded that correcting the record was
impossible without amend or force-push, because the correction commit would
immediately make the field stale again, and asked for a workflow amendment.
In fact the existing contract already permits a lifecycle-only correction
commit, and accepted palimpsest handoffs already use a descriptive form
("same as the implementation commit"). The template does not say either
thing, so agents rediscover or misread it.

## Acceptance Criteria

- [x] The `task-worktree-handoff` capability block in
  `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` moves
  to a new capability version and states:
  - when the handoff is committed in the implementation commit, the
    implementation, validated task, and current task commit fields may use a
    descriptive form that identifies the commit by subject and branch (for
    example `the task commit <subject> (created after this report; see
    git log -1 <task-branch>)` and `same as the implementation commit`);
  - when the handoff is corrected or extended in a later lifecycle-only
    commit, every earlier commit is named by full SHA and only the new commit
    is described;
  - the current task commit field never names the validated base `main`
    commit or any commit other than the task branch `HEAD`;
  - a wrong commit field is corrected by a new lifecycle-only commit that
    changes only the handoff record, followed by one push of the task branch
    before the next review attempt; amend and force-push stay prohibited.
- [x] The reviewer preflight text (`task-worktree-review-procedure` in
  `docs/workflows/REVIEW.md`, and any other managed block that compares the
  handoff's current task commit with the worktree `HEAD`) states how a
  descriptive value is resolved: the reviewer resolves it to the registered
  task branch `HEAD` and confirms the subject matches, and a value that names
  a different commit is still `BLOCKED`. If no such change is needed, the
  task records why.
- [x] A migration file records the capability version changes, their
  managed paths, and the delta, following the pattern of
  `migrations/054-machine-independent-worktree-handoff.json`. Existing
  consumer handoffs are not rewritten.
- [x] Marker baselines and every test that pins the block text are updated.
- [x] An upgrade from the previous capability version installs the new block
  while preserving consumer-owned text.
- [x] `meridian worktree check` and `meridian execution handoff-check`
  behaviour is unchanged. They resolve commits from Git, not from the
  handoff's commit-field text; the task confirms this with a test or a cited
  code path instead of assuming it.

## Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` | Owns the `task-worktree-handoff` block (currently v3). |
| `templates/workflows/governed-sdd/docs/workflows/REVIEW.md` | Owns the reviewer preflight block that compares the current task commit with `HEAD`. |
| `migrations/` | New migration for the capability version changes. |
| `migrations/marker-baselines/CAPABILITY_MARKER_BASELINES.json` | Marker baselines for the changed blocks. |
| `tests/test_meridian_cli.py`, `tests/test_task_worktree_isolation.py` | Tests that pin block text or exercise current-task-commit checks. |
| `scripts/meridian.py` | Reference only: `current_task_commit` handling around lines 874 and 1694–1730. |

## Technical Context

- **Current behavior**: every commit field in the handoff template is
  `<commit SHA>`. Nothing explains self-reference, and nothing says a
  lifecycle-only correction commit is the intended repair, although the
  `Current task commit` placeholder already requires only that the validated
  task commit be an ancestor and the intervening diff contain only permitted
  lifecycle records.
- **Evidence from an adopter (palimpsest, capability v2)**: accepted
  handoffs for `M36-GATE-001`, `F0-ATLAS-001`, and `F0-VERIFY` used the
  descriptive form and passed the reviewer preflight. `F1-FIGURE-001` wrote
  the base `main` SHA into `Current task commit`; it was repaired by a
  lifecycle-only commit that changed only `tasks/handoffs/F1-FIGURE-001.md`,
  which `meridian execution handoff-check` accepted, and the task was then
  reviewed and integrated.
- **Desired behavior**: the template and the reviewer preflight make both
  forms and the correction procedure explicit, so neither implementer nor
  reviewer needs to infer them.

## Validation

```bash
python3 scripts/check_repository.py
```

```bash
python3 -m unittest discover -s tests -v
```

## Completion evidence

- Handoff block moved to `task-worktree-handoff` v4 and reviewer preflight to
  `task-worktree-review-procedure` v7; migration
  `057-self-referential-handoff-commits` (1.1.54 -> 1.1.55) records both, and
  the release ledger, `VERSION`, plugin manifest, and `CHANGELOG.md` carry
  release 1.2.3 as required by `check_repository.py` (precedent: migration 056).
- Upgrade test `test_upgrade_installs_self_referential_handoff_rules_and_preserves_consumer_text`
  covers the v3 -> v4 / v6 -> v7 upgrade with consumer text preserved.
- CLI behavior unchanged, by code path: `scripts/meridian.py` handoff
  consistency (around lines 718-731) reads only the `Branch`, `Worktree`, and
  `Base \`main\` commit` fields from the handoff, and never the
  `Current task commit` text; integration validation (around line 1848)
  compares commits supplied from Git. No CLI code changed.
- Lean Delivery handoff: no self-reference gap was examined or changed; no
  follow-up recorded.
- Validation: `python3 scripts/check_repository.py` passed;
  `python3 -m unittest discover -s tests` ran 446 tests, OK.

## Out of scope

- Changing how the CLI resolves or validates commits.
- Rewriting existing consumer handoffs.
- Changing the Lean Delivery handoff, unless the same self-reference gap is
  found there; if so, record it as a follow-up instead of widening this task.

## Dependencies

- **Depends on**: none.
- **Blocks**: none.
