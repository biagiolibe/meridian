# Audit — Token and Time Efficiency of Meridian's Implementation/Review Loop

Date: 2026-09-10. Scope: the `meridian` framework repository at commit `5dd218b`
plus three uncommitted edits. Evidence for the incident itself is the operator's
post-mortem of a task in Palimpsest, a downstream Rust/GPU project. Palimpsest's
governance surface was subsequently inspected (§1.5); findings specific to it are
marked **[project]** rather than **[framework]**.

**Revision 2026-09-10:** §1.5 and findings F1, F4, F9 were rewritten after the
operator supplied Palimpsest's actual `EXECUTION_EVIDENCE_PROFILE.md`. The first
draft assumed that file was unconfigured. It is not — it is configured, and
carefully. The corrected evidence makes the audit's thesis stronger, not weaker.

---

## 1. The cost model this audit uses

The instinct behind the request is "too many files, too big". That instinct
optimizes the wrong term.

In an agentic loop, billed input is not the size of the context — it is the sum
of the context across turns. With `P` the fixed prefix, `d` the payload appended
per iteration and `N` the iteration count, and writing the context before turn
`i` as `P + (i−1)·d`:

```
no cache hits      : total = N·P + d·N(N−1)/2
all prefix cached  : total = 0.1·[N·P + d·N(N−1)/2] + N·d
```

A real session sits between the two: the prefix is cached from turn 2, but cache
TTL expiry during long think/tool gaps pushes some turns back to full price. The
two bounds are given below so the ranking does not depend on which applies.

- `P` = governance documents, task, queue — read once at turn 1, then a stable
  cached prefix.
- `d` = a `cargo test` dump, a file re-read, a screenshot — appended, then
  re-sent on every subsequent turn.

`P` scales with `N`. The tail scales with `N²`. That changes the ranking of every
finding.

### Reconstruction of the incident

Figures measured in Palimpsest (F9), not assumed: `P` ≈ **32k** tokens — ~25k of
governance documents plus ~6.7k for `docs/TASK_QUEUE.md`. `d` ≈ 2k tokens per
tune-and-test cycle; `N` ≈ 20 cycles, consistent with the post-mortem's "molte
volte".

"Halve governance" below means 25k → 12.5k, i.e. P 32k → 19.5k — an aggressive
target, roughly what P4+P5+P7 together would achieve.

| Intervention | P | N | Uncached | Fully cached | Saving |
|---|---:|---:|---:|---:|---:|
| Baseline | 32k | 20 | 1,020k | 142k | — |
| Halve governance | 19.5k | 20 | 770k | 117k | **18–24%** |
| Cap iterations at 4 | 32k | 4 | 140k | 22k | **85–86%** |
| Both | 19.5k | 4 | 90k | 17k | 88–91% |

**Conclusion: shrinking documents is a real but second-order fix. The first-order
fix is capping the iteration count and the per-iteration payload.** An audit that
led with "the docs are too big" would deliver a satisfying refactor worth a few
percent.

---

## 2. Findings

### F1 — [framework, root cause] Numeric budgets held; prose budgets did not

Palimpsest's profile is configured, and configured well. The first draft of this
audit assumed otherwise and was wrong. The corrected finding is sharper, because
the file turns out to be a **natural experiment**: some of its budgets are
numbers, some are prose, and the post-mortem records the outcome for each.

Mapping the post-mortem's own two lists against the profile:

| Control in the profile | Form | Outcome in the incident |
|---|---|---|
| "at most **one** Computer Use initialization or discovery request" | **number** | respected |
| "**two** distinct captures by default; **three** is the absolute maximum" | **number** | respected |
| `RUST_BACKTRACE=full` prohibited until targeted diagnostics fail | **discrete gate** | respected |
| `Reasoning: medium` as an exact cap | **declared value** | respected |
| manual-verification preflight | **discrete gate** | respected |
| "Do not reread or reprint merely for completeness" | *prose* | **violated** — "una porzione enorme di `TASK_QUEUE.md`" |
| "Start every diff inspection with `git diff --stat`" (no frequency) | *prose* | **violated** — "ho verificato il diff solo dopo una bozza ampia" |
| no rule at all on iteration count | *absent* | **violated** — "molte volte… senza un limite di iterazioni né un criterio di stop" |
| no rule at all on test-as-search-instrument | *absent* | **violated** — "il test doveva essere un controllo di accettazione, non uno strumento di ricerca" |

**Every control expressed as a number was obeyed. Every control expressed as a
sentence was violated. Every gap was a place where no number existed.**

Two caveats, stated so a reader does not have to raise them. This is N=1, and
the source is the violating session's own retrospective rather than independent
observation. And there is a confound: the numeric controls all happen to govern
**discrete, rare, salient acts** (one discovery call, two captures), while the
prose controls govern **incremental accretion** (one more read, one more retry).
That may be the same insight rather than a competing one — §4 argues exactly
that quantity-shaped failures need counters — but the table alone does not
separate "numeric beats prose" from "discrete beats incremental". Either
reading points at the same fix.

The operator's own conclusion — "non è una necessità intrinseca del task, è stata
una cattiva strategia operativa" — is accurate but incomplete. The strategy was
bad in exactly the places the profile did not quantify, and good in exactly the
places it did. That is not a coincidence about one session; it is the shape of
the enforcement surface.

Confirmed by version archaeology: the three controls that would have covered the
gaps — a diagnostic-attempt budget, the test-and-tune prohibition, and the
"before the first code edit and after each material change" diff trigger — are
**absent from Palimpsest** (`grep` returns nothing in either
`docs/CONTEXT_BUDGET_POLICY.md` or `docs/EXECUTION_EVIDENCE_PROFILE.md`). They
exist only as the three uncommitted edits in the framework working tree. The
incident happened in a genuine gap, not through negligence.

But note what those three new edits are: **two of them are prose, and the third
is a `[policy]` placeholder.** Per this table, the two prose rules will be
violated the same way, and the placeholder will be filled with whatever the
operator writes — which is the only one of the three that can work, and only if
it is filled with a number.

### F1b — [framework] The 120-line rule cannot bind where the cost is

The profile says: "Expose at most the first 120 lines needed to identify the
failing crate, test, or file."

A model cannot comply with this in the way that matters. Output enters the
context at the moment the tool result returns — that is when the tokens are
billed, and from then on it is re-sent on every subsequent turn. All the model
can subsequently choose is whether to *re-print* it in its own message. The rule
governs the re-print and leaves `d`, the quadratic term, untouched.

The harness does impose a backstop, measured here: ~19 KB of command output
returned **in full**, while ~224 KB was diverted to a file with a 2 KB preview.
The cap therefore sits somewhere well above 20 KB. A `cargo test --workspace`
run on a project of Palimpsest's size produces roughly 5–50 KB — under the
backstop, so it lands whole. The harness protects against a runaway log; it does
not implement a 120-line rule, and nothing else does either.

The same applies to the "concise successful forms": `cargo test --workspace
--quiet` still emits a line per test. `--quiet` is a courtesy, not a bound.

The fix is one character class, not one paragraph — the bound has to be *in the
command string*, so the truncation happens before the output ever enters the
context:

```
cargo test --workspace --quiet 2>&1 | tail -40
cargo check --workspace --quiet 2>&1 | tail -20
```

This is P2, and against a Rust workspace it is likely the single largest
reduction in `d` available.

### F2 — [framework] Prose exhortation cannot enforce a counter

Every cost control in Meridian is a sentence addressed to the model's judgment:
"keep plans to three bullets or fewer", "use the profile's concise
success-output form", "choose the lowest reliable reasoning level". None is a
mechanism. A model 30 turns deep, with the governing sentence 25 turns behind it
in a 200k-token window, has that sentence at its lowest salience precisely at the
moment it matters most.

The three uncommitted edits in the working tree are the framework's reflex to
this incident — and all three add more prose:

```
AGENTS.md                     | 2 +-
docs/CONTEXT_BUDGET_POLICY.md | 6 ++++++
docs/EXECUTION_EVIDENCE_PROFILE.md | 5 ++++-
```

That reflex has negative expected value: it grows `P`, lowers the per-rule
salience of every existing rule, and does not change enforcement. Section 3
proposes mechanisms instead.

### F3 — [framework] Capability markers are additive-only, so governance grows monotonically

The `<!-- MERIDIAN:BEGIN capability=… -->` mechanism appends a block to 2–4
documents per upgrade. Verified: `scripts/meridian.py` has no removal,
compaction, or supersession path (`prune_stale_baselines` prunes *baseline
snapshots*, not marker blocks), and `migrations/CAPABILITY_MARKERS.md:157` only
notes that an agent may delete markers by accident. There is no operation that
merges two overlapping capabilities or retires one.

Consequence: `P` is a ratchet. `templates/workflows/governed-sdd/CLAUDE.md` is
now 12.0 KB, and most of its body sits inside capability marker blocks. Nothing
in the tooling can ever make it smaller.

### F4 — [framework] `AGENTS.md` and `CLAUDE.md` are 86% identical twins, and are already drifting

Measured (normalized, sentence-level, exact matches): 99 of CLAUDE.md's 115
sentences also appear verbatim in AGENTS.md.

Most call sites say "`AGENTS.md` **or** `CLAUDE.md`", so this is primarily a
maintenance cost, not a runtime one — **but the drift it predicts has already
happened, in this working tree.** The uncommitted edit adds "and the profile's
declared change-summary command" to step 1 of AGENTS.md, and does not add it to
the identical step 1 of CLAUDE.md. Claude Code sessions read CLAUDE.md; they
will not receive the fix being written right now.

Two call sites do make it a genuine 2× runtime cost:
`scripts/meridian.py:548` and `:607` instruct migration and review sessions to
read `PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md` — all three, ~33 KB of ~86%
redundant text.

A weaker paraphrase-level duplication also runs between `CLAUDE.md`
("Implementer-to-reviewer handoff", "Reviewer-integrator identity") and
`PROJECT_WORKFLOW.md` ("Git workflow"): the same rules, restated in different
words, both mandatory reads. Paraphrase duplication is worse than verbatim
duplication because no diff tool can detect the drift.

### F5 — [framework] Role-scoped reading is inoperative under Claude Code

`docs/CONTEXT_BUDGET_POLICY.md`'s `role-scoped-agent-rules` capability tells a
session to read only its role's headings from `AGENTS.md`/`CLAUDE.md`. Under Claude
Code's `CLAUDE.md` auto-injection, that file enters the session **in full** before
the rule is ever read; there is no partial-load option, so the rule saves nothing
for `CLAUDE.md`. It can still buy something for `AGENTS.md` in a harness that
loads it by explicit read — which is exactly the split P4 removes.

The rule also closes with its own escape hatch — "If a heading this rule names is
missing, renamed, or the mapping is otherwise unclear, read the whole file
instead" — which under any uncertainty degrades to the unoptimized behavior.
Net effect: ~1,400 bytes of policy text that, in the framework's primary
harness, buys zero reduction and adds to `P`.

### F6 — [framework] The measured governance prefix

For an implementer session, the documents the workflow declares mandatory:

| Bytes | File |
|---:|---|
| 11,975 | `CLAUDE.md` |
| 9,945 | `docs/CONTEXT_BUDGET_POLICY.md` |
| 9,403 | `PROJECT_WORKFLOW.md` |
| 5,193 | `docs/PULL_REQUEST_POLICY.md` |
| 4,187 | `docs/CODE_ORGANIZATION.md` |
| 1,958 | `docs/COMPLETION_REPORT_TEMPLATE.md` |
| 1,771 | `docs/EXECUTION_EVIDENCE_PROFILE.md` |
| 1,292 | `LANGUAGE_POLICY.md` |
| 1,038 | `tasks/QUEUE.md` (template; real queues are far larger) |
| **46,762** | **≈ 11.7k tokens before one line of code is read** |

Per §1 this is cached and second-order. It is worth fixing for drift and
salience reasons (F2, F4), not primarily for cost.

### F7 — [framework] The manual-verification preflight asks for a prediction, not a proof (superseded in part by F11)

`manual-verification-precondition` requires confirming *before* implementing that
the evidence can be produced. In the incident the preflight passed and the GPU
probe failed later — because "confirm you can produce it" is answerable
optimistically. A preflight that does not *execute* the capture path is a
self-report, and self-reports do not fail early.

**Partly superseded.** Palimpsest already replaced this with an executable probe
(F11), so the framework template is behind its own consumer here — see P6. The
residual framework defect is not the preflight's form but its interaction with
the deterministic-test escape hatch.

### F8 — [framework] There is no task class for search

The incident's real shape: a layout/geometry problem was handed to an
implementation session, which then ran research inside an execution contract.
Meridian's lifecycle has exactly one working shape — `QUEUED → IN_PROGRESS →
READY_FOR_REVIEW → ACCEPTED` — whose contract assumes the answer is known and
only needs writing down (`Expected code surface`, `Acceptance criteria`,
`Out of scope` are all pre-committed). When the answer is *not* known, the
contract has no legal move except `BLOCKED`, and `BLOCKED` feels like failure —
so the model keeps searching inside the implementation frame. **The framework
made the expensive path the only path that looked like progress.**

### F9 — [project] Measured governance surface in Palimpsest

The template figures in F6 badly understate the real case. Measured in
Palimpsest:

| Bytes | File |
|---:|---|
| 28,977 | `AGENTS.md` |
| 26,883 | `docs/TASK_QUEUE.md` (191 table rows) |
| 16,486 | `PROJECT_WORKFLOW.md` |
| 13,368 | `docs/PULL_REQUEST_POLICY.md` |
| 11,584 | `docs/CODE_ORGANIZATION.md` |
| 10,527 | `docs/CONTEXT_BUDGET_POLICY.md` |
| 9,318 | `CLAUDE.md` |
| 5,126 | `docs/EXECUTION_EVIDENCE_PROFILE.md` |
| 2,590 | `LANGUAGE_POLICY.md` |
| 1,807 | `docs/COMPLETION_REPORT_TEMPLATE.md` |
| **126,666** | **≈ 32k tokens** |

So `P` ≈ 32k rather than the 27k assumed in §1 — the reconstruction was
conservative in the right direction. `AGENTS.md` alone has grown to 2.4× the
framework template it derives from.

`docs/TASK_QUEUE.md` at 191 rows is the specific object the post-mortem names.
Nothing in the queue's own design bounds its growth or offers a filtered read;
`docs/CONTEXT_BUDGET_POLICY.md`'s minimal-status rule ("query the canonical
queue for non-terminal entries only") is again prose, and again describes a
discipline the model must apply *after* the file is open.

### F10 — [project, runtime 2×] `CLAUDE.md` and `AGENTS.md` are both loaded, and 59% overlaps

Palimpsest's `CLAUDE.md` opens by declaring itself "a thin pointer to
`AGENTS.md`, which is authoritative" — and then carries a "Meridian generic
baseline (framework compatibility)" section reproducing five capability blocks
that appear verbatim in `AGENTS.md`:

```
DUP    819  ## Command triggers
DUP   1886  ### Autonomous lifecycle orchestration
DUP   1072  ### Review-mode boundary
DUP   1022  ### Review-remediation workflow
DUP    775  ## Owner-acceptance workflow
            5,574 of 9,300 bytes = 59% of CLAUDE.md
```

Under Claude Code, `CLAUDE.md` is auto-injected *and* instructs the session to
read `AGENTS.md`. Both are in context. This is not a maintenance abstraction —
it is ~5.6 KB paid twice, every session, and it is the F4 prediction realized in
the actual incident.

It is also a **correctness** exposure, not only a cost one. The two files have
diverged 3:1 in size; a reader that trusted `CLAUDE.md`'s self-description as a
"thin pointer" would be reading five stale copies rather than a pointer.

### F11 — [project] The escape hatch disarmed the one executable preflight

Palimpsest already implements what §3's P6 proposes, and implements it well —
`## Palimpsest manual-evidence extension` requires an **end-to-end probe that
actually succeeds** before implementation, and states: "If no allowed probe can
succeed before code changes, return `BLOCKED`; do not implement in the hope that
the channel will become available later."

The post-mortem reports both that the preflight was respected *and* that the GPU
probe failed, after which the session continued exploring the local environment
instead of asking the operator for screenshots. Both can be true because the
framework's `manual-verification-precondition` capability carries an escape
hatch:

> "When a deterministic test can serve as the change's primary acceptance
> evidence (for example, a geometry or layout assertion), treat manual or visual
> confirmation as a secondary check, not the only gate."

A geometry/layout task is the *literal example* in that sentence. So the probe's
failure was demoted from a `BLOCKED` trigger to a failed secondary check — and at
that point nothing bounded what the session did next. The exploration that
followed was not covered by any rule.

**Two capabilities, each defensible alone, composed into a hole.** The escape
hatch should suspend the *requirement* for the capture, not the *stop* on a
probe that has already failed: a failed probe is positive evidence about the
environment and should always route to the operator, whatever the evidence tier.
This is the closest thing in the incident to a framework defect with a name.

---

## 3. Proposal — mechanism over prose

Ranked by expected saving. Each replaces model discretion with something outside it.

### P1 — Numeric budgets in the task file, echoed by the existing hook (highest yield)

Add to `tasks/TASK_BLUEPRINT.md`:

```
Diagnostic attempts: 3        # hypothesis-changing retries before BLOCKED is mandatory
Evidence captures: 2          # distinct screenshots/views permitted
Context expansions: 2         # reads beyond Authority + code surface
```

These are hard caps, in the same style as the existing `Reasoning` cap — which
already establishes the precedent that a task field is an exact permitted
runtime value, not a suggestion.

Then extend `hooks/queue-briefing.sh` — which already exists and already fires on
every `UserPromptSubmit` — to print the active task's budgets and a
session-local counter:

```
[Meridian Governed Queue]
  🔴 In progress: TASK-041
  ⏱  Diagnostic attempts: 2/3 · Captures: 1/2 · Expansions: 0/2
  ⛔ On exhaustion: return BLOCKED. Do not raise a cap.
```

This is the decisive property: **the counter is re-injected at the end of the
context on every single turn**, at maximum salience, at a cost of ~40 tokens per
turn. A rule buried 25 turns back cannot compete with that. The counter file
lives in the project's scratch/ignore path; the model increments it as part of
the diagnostic loop, and the hook echoes it back unmodifiable.

**Known limitation, and the closing move.** In this first stage the model
increments the counter, so the count is still a self-report — the win is
salience, not enforcement. Stage two removes the discretion: increment from a
`PostToolUse` hook keyed on the validation-command pattern, so the count is a
side effect of *running the test* rather than an act of reporting it. Same hook
file, same infrastructure. Ship stage one first; it is most of the benefit and
none of the pattern-matching risk.

Expected effect on the reconstructed incident: N from ~20 to ≤4, i.e. the ~80%
saving in §1.

### P2 — Wrapped commands, not "be concise"

Replace the profile's `[commands]` placeholder semantics: the profile must
declare the **literal command string including its output discipline**, not the
bare command plus an instruction to be brief.

```
cargo test -q --lib 2>&1 | tail -30
cargo clippy -q --message-format=short 2>&1 | tail -30
```

Per F1b this is not a style preference: it is the only place the bound can
actually bind, because the tool result is where the tokens are billed. Enforce
with a `PreToolUse` hook that rejects an unwrapped `cargo test`/`cargo check`,
turning `d` from a variable the model controls into a constant. Attacks the
quadratic term directly and compounds with P1.

### P3 — A `Spike` task class (structural fix for F8)

Introduce a second lifecycle shape:

```
Class: SPIKE
Question: [the thing that is not known]
Budget: [max iterations / max wall time]
Deliverable: an ADR or a documented reference value — NOT production code
Branch: throwaway, never merged
Review: NOT_REQUIRED
```

Rule: an implementation task whose acceptance criteria cannot be evaluated
without discovering an unknown must return `BLOCKED` **naming the spike it
needs**. This gives the model a legal, cheap, non-failure-flavored move at
exactly the moment it currently chooses the expensive one — and it isolates the
research context in a session that is thrown away instead of carried into the
implementation and review contexts.

This is the change I would make first if only one were possible, because F8 is
the cause and F1 is the missing brake.

### P4 — Generate `AGENTS.md`, stop maintaining a twin

**Direction matters, and it is the opposite of what it first looks like.** In
Palimpsest, `AGENTS.md` is authoritative and carries substantial project-specific
content with no home in `CLAUDE.md` (`Truth layers`, `Events`, `Determinism`,
`Palimpsest manual-evidence extension`). Generating `AGENTS.md` from `CLAUDE.md`
would destroy it.

So: **`AGENTS.md` is the source; the thin `CLAUDE.md` pointer is generated from
it** — which is what Palimpsest already half-does by hand, and does wrongly, by
also pasting in five stale duplicate blocks (F10). The generated `CLAUDE.md`
should be *only* the pointer plus whatever Claude Code specifically needs, with
the duplicated capability blocks removed outright.

In the framework template the two really are near-twins, so the same generator
applies there with no content loss. Add a `tests/test_meridian_cli.py` assertion
that the generated file matches the committed one — that alone catches the drift
currently sitting uncommitted in this working tree. Also fix
`scripts/meridian.py:548` and `:607`, which tell migration and review sessions to
read `PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md` — all three.

### P5 — A compaction operation for capability markers

Add a `meridian compact` step to the migration tooling: merge overlapping
capability blocks, delete superseded ones, and move a rule that appears in more
than one document to a single canonical home with a one-line cross-reference.
Without this, F3 guarantees that any reduction achieved today is undone by the
next four upgrades.

Candidates today: the reviewer-integrator identity block (3 copies:
`CLAUDE.md`, `AGENTS.md`, `PROJECT_WORKFLOW.md`, plus a fourth restatement in
`docs/CODE_REVIEW_PROMPT.md`); the implementer-to-reviewer handoff (same
spread); `role-scoped-agent-rules` (delete outright per F5).

### P6 — Close the probe/escape-hatch composition (replaces the original P6)

The first draft proposed making the manual-verification preflight executable.
Palimpsest already did that, and did it better than the framework template —
`## Palimpsest manual-evidence extension` requires a probe that actually
succeeds. That extension should be promoted **upward into the framework
template**, replacing the template's weaker "confirm you can produce that
evidence".

The remaining defect is F11's composition. Amend
`manual-verification-precondition` so the deterministic-test escape hatch
suspends the *requirement to capture*, never the *stop on a probe that has
already failed*:

> A probe that has been attempted and failed is positive evidence about the
> environment. Report it and request the evidence channel from the developer
> before continuing, regardless of whether a deterministic test is the primary
> acceptance evidence. Never respond to a failed probe by exploring the local
> environment for an alternative.

Cheap, and it closes the specific hole this incident fell through.

### P7 — Bound the queue read

`docs/TASK_QUEUE.md` is 27 KB / 191 rows and growing monotonically. Prose telling
the model to read "non-terminal entries only" is applied after the file is open.
Two mechanical options, either sufficient:

- Archive terminal rows to `TASK_QUEUE_ARCHIVE.md` — the pattern the Lean
  Delivery branch of `hooks/queue-briefing.sh` already assumes exists — leaving
  the live queue at a bounded size.
- Have the existing hook emit the resolved active/queued/blocked rows directly,
  so a session normally never opens the file at all.

The second is strictly better: it makes the correct behavior the default one
rather than a discipline.

---

## 4. On questioning Meridian's formalisms

The request explicitly invited this, so, directly:

**Worth keeping.** The mode lock, document precedence, one-writer-per-worktree,
the review-record-as-durable-handoff, and the reviewer-integrator session
separation are all cheap to state and buy real correctness. The `Reasoning` cap
is the framework's best existing idea and the model for P1.

**Worth cutting.**
- `role-scoped-agent-rules` — inoperative in the primary harness (F5).
- The `AGENTS.md`/`CLAUDE.md` twin — generate it (P4).
- Paraphrased restatements of the Git workflow across three documents — one home
  plus cross-references.
- `docs/OPERATOR_PROMPTS.md` (11.7 KB) is explicitly non-normative and
  duplicates the command triggers; it belongs in the framework repo as
  documentation, not copied into every consumer project's context surface.

**Worth reframing.** Meridian currently treats *governance* and *economics* as
the same discipline, enforced the same way: by writing another paragraph. They
are not. Governance is well served by prose, because its failure mode is an
agent doing a forbidden *kind* of thing, and a rule read once at turn 1 is enough
to rule out a kind. Economics fails by *quantity* — one more retry, one more
read, each individually defensible — and quantity is only ever controlled by a
counter. Every marginal paragraph Meridian adds to the economic side makes the
governance side slightly worse, by diluting it.

The framework should own numbers and hooks, and let prose do the job prose is
good at.

---

## 5. Recommended order

The first draft's step 1 — "fill the profile" — is already done, and done well.
Revised:

1. **P2** — wrapped validation commands in Palimpsest's profile. One line of
   change, attacks the quadratic term, and per F1b it is the only form of the
   output bound that can actually bind. Do this today.
2. **P1** — numeric budgets + hook echo. F1's table is the argument: in this
   project, numbers were obeyed and sentences were not. The missing number is
   the iteration cap.
3. **P3** — the `Spike` class. Fixes the cause rather than the symptom.
4. **P6** — the probe/escape-hatch fix (F11). Small, specific, and it is a real
   framework defect.
5. **P7** — bound the queue read. ~7k tokens off `P` in this project.
6. **P4/P5** — drift and ratchet control. F10 shows the drift is already
   material and already costing double.

Before any of this: do **not** commit the three uncommitted framework edits as
they stand. Two are prose and, per F1, will be violated the same way the
existing prose was. The third is the `[policy]` placeholder — that one is the
right shape, and it should ship with a default number in the template rather
than an empty bracket, so a project that never fills it still inherits a bound.

Steps 1–6 are changes to two repositories and should be run through Meridian's
own governed lifecycle as separate atomic tasks, not applied as a single sweep.
