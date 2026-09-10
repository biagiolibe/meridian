# Task 009 — Bound the queue read

> **ID**: `009`
> **Category**: Feature (hook + template)
> **Priority**: 🟡 P2
> **Estimate**: ~4h
> **Assigned to**: unassigned

## 🎯 Objective

Make a session normally never open the full task queue. Roughly 7k tokens off the
fixed prefix in a project of Palimpsest's size.

## 📋 Acceptance Criteria

- [x] `hooks/queue-briefing.sh` emits the resolved active / queued / blocked rows for
      the governed-SDD queue, sufficient for a session to act without opening the file.
- [x] The governed-SDD queue template documents archiving terminal rows to
      `TASK_QUEUE_ARCHIVE.md`, mirroring the Lean Delivery branch's existing assumption.
- [x] `CONTEXT_BUDGET_POLICY.md` points at the briefing as the normal path and names
      the specific conditions that justify opening the file.
- [x] A migration record ships the template and policy changes.
- [x] The hook stays under its 5s timeout on a 200-row queue.
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

### Outcome

Migration `026-bound-the-queue-read` (VERSION `1.1.23`). The hardcoded
`tasks/QUEUE.md` constraint was handled by scanning only the annotated zone
immediately after `execution-assets`' `MERIDIAN:END` for a single,
unambiguous, non-archive `*queue*.md`-shaped path, falling back to the
default on no match or ambiguity rather than guessing — verified against
both the Palimpsest-shaped declaration and a deliberately ambiguous zone
(the archiving convention this same task documents mentions
`*QUEUE*ARCHIVE*.md`, which the resolver must not mistake for the live
queue). Dependency resolution treats `ANSWERED` as satisfying, per
`task-lifecycle` v2, and reads `QUEUE_ARCHIVE.md` too so an archived
`ACCEPTED` row still satisfies a dependent task. `templates/workflows/governed-sdd/tasks/QUEUE.md`
is not a managed/marker-protected file (bootstrap-time seed content only),
so its `managedPaths` entry in the migration record is documentary — an
already-adopted project's own queue file is unaffected by the upgrade.
Verified with a real `1.1.22` → `1.1.23` upgrade run and 8 new tests in
`tests/test_queue_briefing.py`, plus the full suite (89 tests) and
`check_repository.py`.

## 📁 Relevant Files

| File | Role |
|------|------|
| `hooks/queue-briefing.sh` | Row resolution. |
| `templates/workflows/governed-sdd/tasks/QUEUE.md` | Archiving convention. |
| `templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md` | Normal-path wording. |

## 🧩 Technical Context

`docs/AUDIT_TOKEN_EFFICIENCY.md` F9. Palimpsest's `docs/TASK_QUEUE.md` is 27 KB /
191 rows and is the specific object the incident post-mortem names.
`CONTEXT_BUDGET_POLICY.md` already says to read "non-terminal entries only" — prose,
applied after the file is open and already billed.

Two mechanical options; **the hook is strictly better** because it makes the correct
behavior the default rather than a discipline. Archiving is the weaker fallback and
still worth documenting.

## ⚠️ Constraints and Considerations

- The queue's canonical location is declared per project in `PROJECT_WORKFLOW.md`
  (`docs/TASK_QUEUE.md` in Palimpsest, `tasks/QUEUE.md` in the template). The hook
  currently hardcodes `tasks/QUEUE.md` — handle the declared location or the feature
  silently does nothing in the project that needs it most.
- If task 006 landed first, extend the same briefing rather than adding a second one.

## 🔗 Dependencies

- **Depends on**: none (coordinate with 006 if both are in flight)
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/009-bound-the-queue-read.md)"$'\n\nExecute this task in the current project.'
```
