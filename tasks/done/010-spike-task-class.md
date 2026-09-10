# Task 010 — A `SPIKE` task class

> **ID**: `010`
> **Category**: Architecture (lifecycle)
> **Priority**: 🟡 P2
> **Estimate**: ~1–2 days, mostly design
> **Assigned to**: unassigned

## 🎯 Objective

Give a session a legal, cheap, non-failure-flavored move for work whose answer is not
yet known. Every other task in this queue is a brake; this is the one that removes the
reason to brake.

## 📋 Acceptance Criteria

- [x] `PROJECT_WORKFLOW.md` defines the `SPIKE` class and its lifecycle.
- [x] `TASK_BLUEPRINT.md` defines the spike task shape.
- [x] `AGENTS.md` defines the routing rule: an implementation task whose acceptance
      criteria cannot be evaluated without first discovering an unknown must return
      `BLOCKED` **naming the spike it needs**.
- [x] The four design questions below are answered in the shipped text, not left open.
- [x] A migration record ships it.
- [x] `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py` pass.

## 🧩 Technical Context

`docs/AUDIT_TOKEN_EFFICIENCY.md` F8. The incident's real shape: a layout/geometry
problem — a question whose answer was *not known* — was handed to an implementation
session. Meridian's lifecycle has exactly one working shape, whose contract assumes
the answer is known and only needs writing down: `Expected code surface`,
`Acceptance criteria` and `Out of scope` are all pre-committed at authoring time.
When the answer is not known, the only legal move is `BLOCKED`, which reads as
failure. **So the framework made the expensive path the only path that looked like
progress.**

Proposed shape:

```
Class: SPIKE
Question:    [the thing that is not known]
Budget:      [max iterations / max wall time]
Deliverable: an ADR or a documented reference value — NOT production code
Branch:      throwaway, never merged
Lifecycle:   QUEUED → IN_PROGRESS → ANSWERED | INCONCLUSIVE
```

The second benefit is as large as the first: research context is isolated in a session
that is **thrown away**, instead of being carried forward into the implementation and
then again into the review.

## ⚠️ Constraints and Considerations

Four design questions to settle **before** writing the templates. These are why this
task is design-heavy and should run at `high` reasoning:

1. Does an `INCONCLUSIVE` spike satisfy a dependency, or block it?
2. Can a spike's throwaway branch contain code at all (a probe binary), given
   `Deliverable: not production code`?
3. Does a spike need its own review gate to prevent it becoming an unbounded
   side-channel for work that should have been a task?
4. **`Review: NOT_REQUIRED` conflicts with existing policy, and resolving that is in
   scope.** `PROJECT_WORKFLOW.md` restricts `NOT_REQUIRED` to "low-risk documentation,
   mechanical configuration, simple scaffolding, or focused tests" and explicitly
   prohibits it for "unresolved design questions" — which is the definition of a
   spike. Either the spike class carries a cheaper review gate of its own (does the
   ADR answer the stated `Question` within budget?), or `review-policy` is amended to
   name spikes as a third case. Do not ship the class without picking one.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/010-spike-task-class.md)"$'\n\nExecute this task in the current project.'
```
