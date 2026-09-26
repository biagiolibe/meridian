# Task 053 — Remove machine-specific absolute paths from tracked records

> **ID**: `053`
> **Category**: Architecture
> **Priority**: 🟡 P2
> **Estimate**: ~2-3h
> **Assigned to**: unassigned
> **Session**: 2026-09-26 consumer entry-router drift investigation

## 🎯 Objective

The developer works on the same repositories from more than one machine,
where checkouts live under different directories. Tracked files must not
contain absolute paths that depend on one machine. Today such paths appear
in Meridian's own records, and the workflow introduced by task 051
(migration 045) *requires* new ones: every task handoff records the
"absolute worktree path", in Meridian and in every consumer that upgraded
to 1.1.42. Replace that rule with a machine-independent one, clean up the
existing occurrences, and add a repository guard.

## 📋 Acceptance Criteria

- [ ] Meridian's `PROJECT_WORKFLOW.md` and both workflow templates record the
      task worktree by a machine-independent value instead of an absolute
      path: the deterministic sibling name `<primary-checkout-name>-task-<n>`
      (or a path relative to the primary checkout, such as
      `../<name>-task-<n>`). The runtime mapping check resolves it against
      `git worktree list --porcelain`, so verification strength is unchanged.
- [ ] Every template passage that asks for an absolute worktree path is
      updated: `governed-sdd/PROJECT_WORKFLOW.md` (git-workflow),
      `governed-sdd/docs/PULL_REQUEST_POLICY.md`,
      `governed-sdd/docs/COMPLETION_REPORT_TEMPLATE.md` (task-worktree-handoff),
      `governed-sdd/docs/workflows/REVIEW.md`, and
      `lean-delivery/PROJECT_WORKFLOW.md`. Each changed protected region gets
      a capability version bump and a new migration record, with marker
      baselines rewritten deliberately.
- [ ] The "absolute common Git directory" used for
      `meridian-integration.lock` is left as is: it is computed at runtime and
      never written to a tracked file. The text says so explicitly.
- [ ] Existing occurrences in live documents are replaced by
      machine-independent wording (for example `<palimpsest-checkout>` or
      `--project ../palimpsest`): `docs/PALIMPSEST_ROUTING_EVOLUTION_EVIDENCE.md`
      and `tasks/handoffs/051.md`. The task decides and records whether
      archived records in `tasks/done/` are rewritten or listed as a
      documented, frozen exception.
- [ ] A new `check_no_machine_paths()` in `scripts/check_repository.py`
      fails on `/Users/<name>/` and `/home/<name>/` (and a Windows
      `C:\Users\<name>\` form) in tracked text files, honoring only the
      exceptions recorded above; it is called from `main()`.
- [ ] Fixtures in `tests/test_check_repository.py`: a clean tree passes; a
      tracked file with each forbidden form fails and names the file and
      line; an allowed exception passes.
- [ ] `python3 scripts/check_repository.py` and
      `python3 -m unittest discover -s tests -v` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `PROJECT_WORKFLOW.md` | Local task-worktree boundary (handoff record). |
| `templates/workflows/lean-delivery/PROJECT_WORKFLOW.md` | Same rule, distributed to consumers. |
| `templates/workflows/governed-sdd/PROJECT_WORKFLOW.md`, `docs/PULL_REQUEST_POLICY.md`, `docs/COMPLETION_REPORT_TEMPLATE.md`, `docs/workflows/REVIEW.md` | Governed handoff and review rules. |
| `migrations/`, `migrations/marker-baselines/` | New migration and baselines for the bumped capabilities. |
| `docs/PALIMPSEST_ROUTING_EVOLUTION_EVIDENCE.md`, `tasks/handoffs/051.md`, `tasks/done/` | Existing occurrences. |
| `scripts/check_repository.py`, `tests/test_check_repository.py` | New guard and fixtures. |

## 🧩 Technical Context

- **Current behavior**: task 051's rule says the handoff records the
  "absolute worktree path"; `tasks/handoffs/051.md` therefore contains one,
  as will every later handoff here and in consumers. Several evidence
  documents and archived tasks also cite commands with a checkout path from
  one machine.
- **Desired behavior**: tracked files identify checkouts and worktrees by
  names or relative paths that resolve on any machine; absolute paths exist
  only at runtime.

## 🔨 Suggested Implementation

1. Rewrite the rule text, bump the affected capabilities, add the migration,
   and regenerate marker baselines with
   `python3 scripts/check_repository.py --write-marker-baselines`.
2. Update any CLI code or test that builds or verifies the handoff worktree
   value so it accepts the new form.
3. Replace existing occurrences, then add the guard and its fixtures.

## ⚠️ Constraints and Considerations

- This is a protected-template change that reaches consumers through a
  migration; treat it as risk-bearing and request a review.
- It bumps `VERSION` and adds a migration, as tasks 015/017 also do; integrate
  in queue order and re-check `check_migrations()` after each merge.
- Consumer handoffs already written with absolute paths are not rewritten by
  the migration; document this in the migration description.

## 🔗 Dependencies

- **Depends on**: 054
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/053-remove-machine-specific-absolute-paths.md)"$'\n\nExecute this task in the current project.'
```
