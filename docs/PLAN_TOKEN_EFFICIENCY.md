# Execution Plan — Economic Enforcement in Meridian

Companion to [AUDIT_TOKEN_EFFICIENCY.md](AUDIT_TOKEN_EFFICIENCY.md), which
carries the evidence. This file is the ordered work plan; it is a proposal until
the operator authorizes items individually.

## Where this sits

`QUALITY_COMPLIANCE_ROADMAP.md` already states this plan's governing thesis:

> "Meridian's process is enforced almost entirely through prose an agent is
> expected to follow… Nothing in the repository mechanically verifies that an
> agent actually did what the instructions said."

That roadmap applies the insight to **compliance** (review verdicts, ancestry,
audit conformance). This plan applies the same insight, and the same
control-plane pattern — durable state on disk that a tool computes and an agent
merely reads — to **economics** (context, iterations, output volume).

The two axes differ in one way that matters for design. A compliance failure is
a *discrete forbidden act*: one bad merge, one skipped review. Prose read at turn
1 is often enough to rule out a kind of act. An economic failure is *accretion*:
one more read, one more retry, each individually defensible, none of them
forbidden. Accretion is only ever bounded by a counter. This is why the plan
below contains almost no new prose.

**Nine items, W0–W4.** Each is independently shippable and independently
revertible. Effort estimates assume one agent session at `medium`.

---

## W0 — Framework-internal hygiene (no migration record needed)

Changes here touch only this repository's own files, not artifacts that adopted
projects hold copies of, so they ship without a `migrations/*.json` record and
without an upgrade path.

### W0.1 — Generate `CLAUDE.md` from `AGENTS.md`
*Audit: F4, F10 · ~3h · touches `scripts/meridian.py`, `tests/test_meridian_cli.py`, both templates*

`AGENTS.md` and `CLAUDE.md` are 86% identical in the template and are already
drifting — the uncommitted working-tree edit patches step 1 of `AGENTS.md` and
leaves the identical step 1 of `CLAUDE.md` stale.

**Direction is the whole design decision, and it is the counter-intuitive one.**
In a real project `AGENTS.md` is authoritative and carries project-specific
content with no home in `CLAUDE.md` (Palimpsest: `Truth layers`, `Events`,
`Determinism`, `Palimpsest manual-evidence extension`). Generating `AGENTS.md`
from `CLAUDE.md` would delete that. So:

- `AGENTS.md` is the source of truth.
- `CLAUDE.md` is **generated**: the pointer preamble, plus only what Claude Code
  specifically needs. The five duplicated capability blocks are removed, not
  regenerated — under Claude Code's auto-injection they are paid twice today.
- A `tests/test_meridian_cli.py` case asserts the committed `CLAUDE.md` matches
  the generator's output. That test alone catches the drift currently sitting
  uncommitted in this working tree.

**Does not do:** change any rule's content. Pure de-duplication.

### W0.2 — Stop instructing sessions to read both files
*Audit: F10 · ~20min · touches `scripts/meridian.py:548`, `:607`*

The assisted-adoption and assisted-reviewer prompts both say "Read the local
LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md" — all four. After
W0.1, `CLAUDE.md` is a generated pointer; these prompts should name `AGENTS.md`
only. Roughly 9 KB off every assisted migration and review session.

**Depends on:** W0.1.

---

## W1 — Ship today (template + migration record, one per item)

Each item changes a managed path, so each needs a `migrations/NNN-*.json` record
following the shape of `020-reasoning-budget-contract.json`. That record is the
delivery vehicle to adopted projects via `meridian upgrade`, and it is most of
the effort in each item — the doc edit itself is small.

### W1.1 — Output bounds belong in the command string
*Audit: F1b · ~2h · `docs/EXECUTION_EVIDENCE_PROFILE.md`, `docs/CONTEXT_BUDGET_POLICY.md`*

**This is the highest cost-reduction-per-hour item in the plan. Do it first.**

Today the profile collects `[commands]` and separately asks for a "concise
success-output form", and the failure section says "expose at most the first 120
lines". Measured (audit F1b): ~19 KB of command output enters context in full;
the harness backstop sits well above 20 KB. A `cargo test --workspace` run is
5–50 KB, so it lands whole. The tokens are billed when the tool result returns,
and re-sent every turn thereafter. "Expose at most 120 lines" can only govern
whether the model *re-prints* them — a rounding error against the quadratic term.

Change the profile's contract so the recorded value is the **complete literal
command string, including its output bound**, and say why:

The template records the *shape*, and stays stack-agnostic — its own opening
sentence declares it the application of a "stack-agnostic" discipline, and today
the only stack name anywhere under `templates/` is a fill-in hint in
`TECH_DESIGN.md`:

```bash
set -o pipefail
<project validation command> 2>&1 | tail -<project-chosen bound>
```

The project fills that in (`cargo test --workspace --quiet 2>&1 | tail -40` in
Palimpsest's case). Per-stack worked examples belong in `WORKFLOW_GUIDE.md`, which
is repo documentation and is not copied into projects.

**`set -o pipefail` is not optional, and every example must lead with it.** A bare
`cargo test … | tail -40` returns *`tail`'s* exit status, which is always 0. That
silently defeats two controls the framework depends on: the profile's own
"Preserve each command and its exit status", and `CODE_REVIEW_PROMPT.md`'s rule
against accepting a validation claim "without a command/exit-status … behind it".
A reviewer who implements this item verbatim without `pipefail` ships a
regression that makes every future failing validation look green. Where a shell
without `pipefail` is in play, capture `${PIPESTATUS[0]}` explicitly instead.

Amend `CONTEXT_BUDGET_POLICY.md`'s "use the profile's concise success-output
form" to "run the profile's literal declared command string; do not run the bare
command and summarize afterwards."

`set -o pipefail` and `| tail -N` are *shell* mechanics and belong in the
template; `cargo`, `npm` and `pytest` do not. A bootstrapping project gets its
correct default from `WORKFLOW_GUIDE.md`, not from the copied file.

**Does not do:** reduce validation coverage. Exit status is unchanged and still
reported; only the volume that enters context changes.

### W1.2 — Ship default numbers, not empty brackets
*Audit: F1 · ~2h · `docs/EXECUTION_EVIDENCE_PROFILE.md`, `tasks/TASK_BLUEPRINT.md`*

The audit's central evidence: in the incident project, **every budget expressed
as a number was respected and every budget expressed as a sentence was
violated**. The controls that would have covered the gaps did not exist there at
all.

The framework's current answer is a placeholder — `Diagnostic-attempt budget…:
[policy]`. A placeholder inherits nothing: a project that never fills it has no
bound, which is exactly the incident's condition. Ship defaults instead:

```
Diagnostic attempts: 3     # hypothesis-changing retries before BLOCKED is mandatory
Evidence captures: 2       # already numeric in practice; make it a named field
Context expansions: 2      # reads beyond Authority + Expected code surface
```

A project may raise a default, but must record a rationale — the same shape
`Reasoning` already uses, which is the framework's own precedent for "a declared
field is an exact permitted runtime value, not a suggestion". Add matching
optional per-task override fields to `TASK_BLUEPRINT.md`.

**Does not do:** enforce anything yet. W1.2 makes the number exist and gives it a
home; W2.1 makes it binding. Shipping W1.2 alone is still worth it — F1's table
says a number in front of a model performs very differently from a sentence — but
do not mistake it for enforcement.

### W1.3 — Close the probe / escape-hatch composition
*Audit: F7, F11 · ~2h · `manual-verification-precondition` → v2*

The clearest single framework defect the incident exposed. Two capabilities, each
defensible alone, compose into a hole:

- Palimpsest's local extension requires a manual-evidence probe that *actually
  succeeds*, and mandates `BLOCKED` if it cannot.
- The framework's `manual-verification-precondition` says a deterministic test
  may serve as primary evidence, making visual confirmation "a secondary check,
  not the only gate" — and its literal example is "a geometry or layout
  assertion", which is precisely the incident's task.

So the GPU probe's failure was demoted from a `BLOCKED` trigger to a failed
secondary check, and nothing then bounded the environment exploration that
followed.

Two changes, both in the capability text:

1. **Promote the stronger form upward.** Replace the template's "confirm you can
   produce that evidence" with Palimpsest's executable-probe requirement. The
   consumer project is ahead of the framework here; adopt its wording.
2. **Separate the two things the escape hatch conflates.** A deterministic test
   may remove the *requirement to capture*. It must never suspend the *stop on a
   probe that has already been attempted and failed*:

   > A probe that has been attempted and failed is positive evidence about the
   > environment. Report it and request the evidence channel from the developer
   > before continuing, whatever the evidence tier. Never respond to a failed
   > probe by exploring the local environment for an alternative.

---

## W2 — The counter (the systemic fix)

### W2.1 — Budget state, CLI, and hook echo
*Audit: F1, F2 · ~1–2 days · `scripts/meridian.py`, `hooks/`, `tests/`*

This is the item the audit exists to argue for, and it reuses the control-plane
pattern `bin/meridian adopt --assisted` already established: durable state on
disk, computed by a tool, read by an agent that cannot quietly disagree with it.

**State.** `.meridian/budget.json`, keyed by task ID:

```json
{ "TASK-041": { "diagnostic": 2, "captures": 1, "expansions": 0 } }
```

**Keying — settle this before implementing.** Keyed by task rather than session,
so a budget cannot be reset by opening a new chat. But a plain task key breaks
the remediation cycle: `Address review <TASK-ID>` is legitimate new work with its
own diagnostics, and a task may go through several review attempts. Under a plain
task key, attempt 3 inherits an exhausted counter and must return `BLOCKED`
immediately — the mechanism firing on a task that is proceeding correctly. That
false positive is how a control gets disabled after its first week.

Key by `<TASK-ID>:<attempt>`, where attempt increments on each
`READY_FOR_REVIEW → IN_PROGRESS` transition. The reviewer already writes that
transition as part of the review-handoff commit, so there is a natural place to
hook it and no new bookkeeping.

**CLI.** `meridian budget show <TASK-ID>` and `meridian budget spend <TASK-ID>
<kind>`. `spend` returns non-zero once the declared cap is reached, and its
message names `BLOCKED` as the required next move. Recording a spend is itself
durable, auditable evidence — it belongs in the completion report.

**Echo.** Extend `hooks/queue-briefing.sh`, which already fires on every
`UserPromptSubmit`:

```
[Meridian Governed Queue]
  🔴 In progress: TASK-041
  ⏱  Diagnostics 2/3 · Captures 1/2 · Expansions 0/2
  ⛔ On exhaustion: return BLOCKED. Do not raise a cap.
```

The mechanism is entirely about **position**: ~40 tokens re-injected at the end
of the context every single turn, at maximum salience, versus a rule read once at
turn 1 and buried 25 turns deep by the time it matters. That asymmetry is the
whole point.

**Known limitation, stated up front.** In this stage the model calls `spend`, so
the count is still a self-report — the win is salience, not enforcement. Stage
two closes it: increment from a `PostToolUse` hook keyed on the validation
command pattern, so the count becomes a side effect of *running the test* rather
than an act of reporting it. Ship stage one first; it is most of the benefit and
none of the pattern-matching brittleness.

**Depends on:** W1.2 (the numbers must exist first).

---

## W3 — Structural: stop the ratchet

### W3.1 — A retirement path for capabilities
*Audit: F3 · ~1 day · `scripts/meridian.py`, `migrations/CAPABILITY_MARKERS.md`*

Verified: no removal, compaction, or supersession path exists. `migrations/*.json`
has `capabilities`, `managedPaths`, `verification` — all additive.
`prune_stale_baselines` prunes baseline snapshots, not marker blocks. Every
upgrade appends to 2–4 documents and nothing ever merges or retires one.

Without this, **every reduction W0–W2 achieves is undone by the next four
upgrades.** It buys no tokens itself; it is what makes the other items durable.

Add a `removes` / `supersededBy` field to the migration record schema and the
`meridian upgrade` path that honors it: delete a retired marker block, and merge
two overlapping capabilities into one canonical home with a cross-reference at
the other sites. Extend `meridian audit` to flag a rule appearing under more than
one heading — the paraphrase duplication between `CLAUDE.md` and
`PROJECT_WORKFLOW.md` is invisible to any diff tool and is how the current
triplication happened.

### W3.2 — Retire `role-scoped-agent-rules`
*Audit: F5 · ~1h · migration record*

Under Claude Code's `CLAUDE.md` auto-injection the file enters the session in
full before the rule is ever read, so it saves nothing for `CLAUDE.md`. It is not
target-less — `AGENTS.md` survives W0.1 as the source of truth and is 29 KB in
Palimpsest, so a harness that loads it by explicit read could in principle use
the rule. The case for retiring it is reliability, not absence of a target: its
own closing clause ("if the mapping is otherwise unclear, read the whole file
instead") means it degrades to the unoptimized behavior under exactly the
conditions where a session is least sure what it is reading. A conditional saving
that vanishes under uncertainty, costing ~1.4 KB of always-loaded policy text,
is a bad trade. Retire it and put the same effort into W3.3, which bounds a read
mechanically.

**Depends on:** W3.1 — this is the first real customer for the removal path, and
a good test of it.

### W3.3 — Bound the queue read
*Audit: F9 · ~4h · template + `hooks/queue-briefing.sh`*

Palimpsest's `docs/TASK_QUEUE.md` is 27 KB / 191 rows and is the specific object
the post-mortem names. `CONTEXT_BUDGET_POLICY.md` says to read "non-terminal
entries only" — prose, applied after the file is already open and billed.

Two mechanical options; the second is strictly better because it makes the
correct behavior the default rather than a discipline:

- Archive terminal rows to `TASK_QUEUE_ARCHIVE.md` — a pattern the Lean Delivery
  branch of `queue-briefing.sh` already assumes exists — keeping the live queue
  bounded.
- Have the hook emit the resolved active / queued / blocked rows directly, so a
  session normally never opens the file at all.

Roughly 7 k tokens off `P` in a project of Palimpsest's size.

---

## W4 — The cause

### W4.1 — A `SPIKE` task class
*Audit: F8 · ~1–2 days, mostly design · `PROJECT_WORKFLOW.md`, `TASK_BLUEPRINT.md`, `AGENTS.md`, migration record*

Everything above is a brake. This is the item that removes the reason to brake.

The incident's real shape: a layout/geometry problem — a question whose answer
was *not known* — was handed to an implementation session. Meridian's lifecycle
has exactly one working shape, and its contract assumes the answer is known and
only needs writing down: `Expected code surface`, `Acceptance criteria` and
`Out of scope` are all pre-committed at task-authoring time. When the answer is
not known, the only legal move is `BLOCKED` — which reads as failure. **So the
framework made the expensive path the only path that looked like progress.**

A second lifecycle shape:

```
Class: SPIKE
Question:    [the thing that is not known]
Budget:      [max iterations / max wall time]
Deliverable: an ADR or a documented reference value — NOT production code
Branch:      throwaway, never merged
Review:      NOT_REQUIRED
Lifecycle:   QUEUED → IN_PROGRESS → ANSWERED | INCONCLUSIVE
```

Plus the routing rule that gives it teeth: an implementation task whose
acceptance criteria cannot be evaluated without first discovering an unknown must
return `BLOCKED` **naming the spike it needs**. That is a legal, cheap,
non-failure-flavored move available at exactly the moment a session currently
chooses the expensive one.

The second benefit is as large as the first: research context is isolated in a
session that is **thrown away**, instead of being carried forward into the
implementation and then again into the review.

**Design questions to settle before implementing** — these are why this is
`high` reasoning and not `medium`:
- Does an `INCONCLUSIVE` spike satisfy a dependency, or block it?
- Can a spike's throwaway branch contain code at all (a probe binary), given
  `Deliverable: not production code`?
- Does a spike need its own review gate to prevent it becoming an unbounded
  side-channel for work that should have been a task?
- **`Review: NOT_REQUIRED` above conflicts with existing policy, and resolving it
  is in scope.** `PROJECT_WORKFLOW.md` restricts `NOT_REQUIRED` to "low-risk
  documentation, mechanical configuration, simple scaffolding, or focused tests"
  and explicitly prohibits it for "unresolved design questions" — which is the
  definition of a spike. Either the spike class carries a review gate of its own
  (cheaper than a full review: does the ADR answer the stated `Question` within
  budget?), or `review-policy` is amended to name spikes as a third case. Do not
  ship the class without picking one.

---

## Recommended order

Ordered by return, not by effort. The queue in `tasks/QUEUE.md` mirrors this.

| # | Item | Task | Effort | Why here |
|---|---|---|---|---|
| 1 | **W1.1** output bounds in the command string | 001 | 2h | Highest reduction per hour; the only phase-1 item that moves real tokens |
| 2 | **W1.2** default numeric budgets | 002 | 2h | Buys ~no tokens alone; W2.1 needs it |
| 3 | **W2.1** budget CLI + hook echo | 006 | 1–2d | The systemic fix — the only item that reduces `N` rather than `d` |
| 4 | **W1.3** probe / escape-hatch fix | 003 | 2h | Largest saving in the specific incident, but situational; real value is governance |
| 5 | **W0.1 + W0.2** generate `CLAUDE.md` | 004, 005 | 3h | Correctness, not cost: stops a fixed rule silently not reaching Claude Code |
| 6 | **W4.1** `SPIKE` class | 010 | 1–2d | Removes the reason the loop starts; design-heavy |
| 7 | **W3.1 → W3.2 → W3.3** ratchet control | 007–009 | ~2d | Makes 1–6 durable rather than temporary |

Items 1–3 are the cost-reduction path and are worth completing before 4–5 are
scheduled. Items 4 and 5 block nothing and can slip without cost; the only hard
dependency in the whole plan is 002 → 006.

**Why this is not effort-ordered.** Phase 1 attacks `d`, the size of each
iteration. Only W2.1 attacks `N`, the number of them — and `N` is the quadratic
multiplier. Modelled against the incident (P 32k, d 2k, N 20): items 1–2 and the
dedup take it from ~142k to ~107k tokens (−25%), while adding item 3 takes it to
~17k (−88%). The first three items are worth roughly a quarter; the counter is
worth the rest.

**Two standing cautions.**

**Revised.** An earlier draft said not to commit the three pre-queue working-tree
edits as they stand. That was too blunt. The concern was never that those
sentences are wrong — it was that prose alone was the *whole* response to the
incident. Once W1.2 and W2.1 supply the numbers, the prose becomes the principle
those numbers implement, which is the correct division of labour. Commit them.
What matters is that W1.2 *fills* the `[policy]` field rather than replacing it,
and that the `AGENTS.md`/`CLAUDE.md` asymmetry is left intact as W0.1's proof
case rather than hand-patched.

And the plan's own failure mode is the one it diagnoses: every item here is a
candidate for being "improved" by adding a paragraph explaining it. Resist that.
If an item cannot be expressed as a number, a generated file, or a hook, it
probably does not belong in this plan.

---

## Next: Palimpsest

Delivery splits in two, and the split matters for planning:

- **Applies cleanly.** W1.3 and W3.3 edit capability marker blocks, which is
  exactly what the marker mechanism exists to update. `meridian upgrade` handles
  these.
- **Needs an operator reconciliation pass.** W1.1 and W1.2 change
  `EXECUTION_EVIDENCE_PROFILE.md` — a *project-owned* file that Palimpsest has
  legitimately filled in with substantial custom content (its Rust command forms,
  its capture policy, its `screencapture` path). An upgrade against a managed
  path the project has rewritten on purpose is the merge-conflict case
  `CAPABILITY_MARKERS.md` was built for; expect reconciliation, not a clean
  apply. Budget for that rather than planning a one-command rollout.
What will remain project-specific — its already-strong local profile, the
`AGENTS.md`/`CLAUDE.md` divergence at 29 KB vs 9.3 KB, the 191-row queue, and
whether the incident's task should retroactively have been a spike — is a
separate pass, to be planned after these items are chosen.
