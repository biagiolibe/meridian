# Design: Versioned Capability Markers and Protected Regions

Status: phases 1-4 shipped (markers on capabilities 001/002, version-aware
detection, cosmetic-vs-real conflict resolution in `upgrade`, and
`meridian audit`'s protected-region integrity check). Phase 5 (process
discipline) is documented in `CONTRIBUTING.md`/`migrations/README.md`.
Migration 007 additionally shipped markers for 004/005. An expanded retrofit
(migrations 008-011, plus a full Palimpsest retrofit) is in progress — see
"Addendum: expanded retrofit plan" near the end of this document for the
current, authoritative state; treat the original Phase 1-5 plan below as
historical design reasoning, not the up-to-date task list. This document
integrates two ideas
discussed while adopting Meridian onto a heavily customized project
(Palimpsest/ECHOES): capability detection that survives a project rewriting
Meridian's prose in its own voice, and a way to stop that same rewriting from
silently swallowing a framework-mandated rule. Both problems have the same
root cause and the same fix.

## The problem, precisely

`meridian upgrade` compares managed files byte-for-byte via a three-way merge.
That works while a project's wording stays close to the template. It breaks
permanently once a project restates the same rule in its own structure and
voice — not a bug, a mismatch between what the tool checks (exact text) and
what actually matters (behavior). Two concrete failures from this session:

1. **False negatives in detection.** `detect_mode()` and parts of
   `detect_capabilities()` look for literal tokens (`GOVERNED_SDD`, `Address
   review`, `Run lifecycle`). A project whose `PROJECT_WORKFLOW.md` predates
   the exact `GOVERNED_SDD` token — genuinely governed-SDD in substance —
   fails detection (`fusa`, then `palimpsest`, both this session).
2. **Permanent merge conflicts with no way to tell real gaps from cosmetic
   ones.** Palimpsest's `AGENTS.md`/`CLAUDE.md`/four docs files conflict on
   every upgrade because their wording diverged from the template long ago,
   even after every rule was correctly, manually incorporated in Palimpsest's
   own voice. `upgrade --check` cannot distinguish "this project doesn't have
   the rule" from "this project has the rule, phrased differently" — so the
   only tool-supported outcome was `--owner-reconciled`, an act of faith by
   the operator, not a verified fact.

There's also a related, unaddressed gap: **a migration that modifies an
existing capability** (not adds a new one) is invisible to a presence-only
check. If `detect_capabilities()` only asks "is `Address review` mentioned
anywhere," it can never tell v1 of that capability's rule from v2 — the
phrase can still be there while the actual rule text it governs is stale.

## The fix: a versioned marker that also protects its own content

A short, invisible marker pair wraps the framework-owned text for one
capability:

```markdown
<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->
Before running validation, classify the diff by surface: *documentation/policy
text* ... [exact canonical text] ...
<!-- MERIDIAN:END -->
```

Three rules, each independently checkable:

1. **Detection is version-aware, not boolean.** A migration that changes
   `validation-scoping` declares the version it requires
   (`capabilityVersion: 2`). Detection reads the marker's version and
   compares it to what's required — present-but-stale is a real, distinct
   state from absent, and both route to the same remediation loop
   (`IMPLEMENT_MIGRATION` distinguishes "add" from "update" only in its
   generated prompt text, not in the state machine).
2. **The bracketed content is not to be reworded.** Between `BEGIN` and
   `END` is the framework's exact canonical text for that capability version.
   A project extends by writing its own material *outside* the markers —
   referencing the protected rule, adding project-specific detail beneath it
   — never by rewriting what's inside.
3. **The marker is also an integrity anchor.** Because the protected content
   is supposed to be byte-identical to a known release of that capability
   version, a verifier can hash it and confirm it matches *some* released
   version of `validation-scoping` — not necessarily the latest, just a real
   one that was never hand-edited.

This does not make the region technically unmodifiable — nothing does, for
plain text an agent can write to. It makes an unauthorized edit **immediately
and mechanically detectable**, which is the practical equivalent as long as
detection is wired into a gate someone actually has to pass (see
Verification below). The same self-report problem that motivated migration
005 (CI-verified validation) applies here too: a bumped version number next
to unchanged (or wrongly changed) text is exactly as untrustworthy as a bare
"tests passed," so a reviewer verifying a capability-version bump must
re-derive that the protected text actually matches the claimed version — not
trust the marker any more than migration 005 trusts a self-reported pass.

## Migration record shape

```json
{
  "id": "006-validation-scoping-v2",
  "capability": "validation-scoping",
  "capabilityVersion": 2,
  "from": "1.1.2",
  "to": "1.1.3",
  "description": "Adds a third diff-surface category (configuration-only) between documentation and source.",
  "delta": "Insert one clause distinguishing configuration-only changes from documentation-only ones; the rest of the rule is unchanged from v1.",
  "managedPaths": ["docs/CONTEXT_BUDGET_POLICY.md"],
  "verification": ["..."]
}
```

`capability` and `capabilityVersion` are new, optional fields — a migration
that only touches the mechanical upgrade CLI (like today's 004/005 wrapper
logic) or that isn't naturally expressible as one marked region can omit
them and fall back to today's file-hash-only tracking. `delta` replaces the
implicit assumption in today's `assisted_implementer_prompt` that "missing
capability" always means "write it from scratch" — for a version bump, the
implementer's job is the delta only, the same atomic-task discipline Meridian
already asks of every other kind of work.

## Detection and remediation, unified

`detect_capabilities()` changes from "does this phrase appear anywhere" to:
for each migration with a `capability` field, find its marker in the
project, compare `capabilityVersion`; `MISSING` covers both "no marker" and
"marker below the required version," each reported with which case it is.

The genuinely new payoff is for `upgrade`, not just `adopt --assisted`: when
the three-way merge reports `CONFLICT` on a file that also carries a
capability marker, check the marker before asking the operator for
`--owner-reconciled`. Marker at the required version — the conflict is
cosmetic (the project already has the rule, worded its own way); register
the baseline with no agent involved, no act of faith. Marker missing or
stale — the conflict is real; dispatch the same implementer/reviewer loop
already built for adoption, scoped to `delta`, not a full rewrite.

## Verification: the part that makes protection more than a comment

Detection alone doesn't stop drift, it just measures it after the fact. Add
one deterministic check — inside the `meridian audit` command from
`QUALITY_COMPLIANCE_ROADMAP.md`'s Tier 2, not a new top-level command — that,
for every marker found in a project, hashes the bracketed content and
confirms it matches the exact text of *some* released version of that
capability (checked against every historical version shipped in Meridian's
own migration records, not only the latest). No match: report drift with the
capability id, claimed version, and the fact that its content doesn't match
any released text for it. This turns an edited protected region into an
audit finding a reviewer has to address, not a fact nobody notices until the
next upgrade conflicts for a reason nobody can explain.

## What this does not solve

- It doesn't stop an agent from deleting the markers entirely, or editing
  inside them, in the moment. Nothing can, for a plain file with write
  access. It stops that edit from going unnoticed past the next audit or
  review.
- It doesn't retroactively fix Palimpsest's existing prose — the framework
  rules there are still interleaved with project-specific text in the same
  sentences in places. Introducing markers there is a one-time, manual
  separation job, the same kind of work already done by hand this session,
  done once so future drift becomes visible instead of accumulating again.
- It doesn't apply to Lean Delivery, which has no capability-tracked rules
  today; scope this to governed-SDD's managed docs only unless a concrete
  need for Lean Delivery capability tracking shows up later.

## Implementation plan

Sequenced so each phase is independently useful and testable; do not start a
phase before the previous one has tests passing.

**Phase 1 — Marker syntax and backfill (migration 006). Shipped.**
Define the exact marker grammar (regex Meridian's own tooling will parse),
retrofit `<!-- MERIDIAN:BEGIN capability=... v1 --> ... <!-- MERIDIAN:END -->`
around the existing capability text for `review-remediation-record` (001)
and `lifecycle-orchestration` (002) in `templates/workflows/governed-sdd/`.
This is itself a migration (touches managed files) — version bump, migration
record, tests, exactly like 004/005. Does not yet change any detection or
verification code; it only makes the markers exist so the next phases have
something to read.

**Phase 2 — Version-aware `detect_capabilities()`. Shipped.**
Added the `capability`/`capabilityVersion` fields to the migration record
schema (backfilled onto 001/002); `detect_capabilities()` parses markers with
a version comparison. A legacy fallback (`LEGACY_CAPABILITY_EVIDENCE`) was
added beyond the original plan: without it, every project adopted before
migration 006 has no marker at all and would have regressed to fully
`MISSING` under marker-only detection — caught by testing against two real
projects (fusa, palimpsest) before shipping, not by the unit tests alone.
The fallback proves only v1, never a later version. `assisted_implementer_prompt`
surfaces a migration's `delta` field when present.

**Phase 3 — Cosmetic-vs-real conflict resolution in `upgrade`. Shipped.**
When `plan_from_baseline` reports a merge conflict for a file, and that
file's *own* content already carries a satisfied marker for every capability
it manages, the conflict downgrades to a new `VERIFIED` plan action (file
left untouched, does not block the upgrade) instead of a blocking
`CONFLICT`. The check had to be scoped to the file's own text, not
project-wide capability presence — an earlier version checked project-wide
and produced a false positive (a conflict on an unrelated file was wrongly
downgraded because a different file's marker happened to satisfy the
capability), caught by the existing conflict regression tests.
`--owner-reconciled` remains the fallback for a conflict with no marker at
all (unmarked legacy content, or a file no migration tracks as a capability).

**Phase 4 — Integrity verification in `meridian audit`. Shipped, narrower
than originally scoped.**
`meridian audit --project <path>` compares each marker's bracketed content
against the framework's *current* template for that same file and capability
version — not "every released version ever," since Meridian keeps no
separate historical archive of past capability text outside the current
templates. A marker naming a version the current template no longer carries
reports `SKIP` (a staleness question for `upgrade`) rather than a false
`FAIL`. Extending this to genuinely check against every historical version
would need a durable per-version text archive that does not exist yet — left
for a future revision if it turns out to matter in practice.

**Phase 5 — Process discipline. Documentation shipped; retrofit ongoing.**
`CONTRIBUTING.md` and `migrations/README.md` now require: a migration that
modifies existing framework-mandated prose (not just adds a new file) must
declare `capability`/`capabilityVersion` and wrap the affected text in
markers if it doesn't already have them, with a `delta` scoped to the actual
change. Migrations 003, 004, and 005 do not carry markers yet, and neither
`fusa` nor `palimpsest` (both real, already-adopted projects) have adopted
any marker — both are intentionally deferred to each one's next real change
rather than a dedicated migration or session with no other purpose.

Each phase after Phase 1 is optional to do immediately — the design holds
together even if only markers + version-aware detection ship and the
integrity audit lands later once `meridian audit` itself exists.

## Addendum: expanded retrofit plan

Decided while bringing Palimpsest to full compliance: Palimpsest's own
directory conventions (`docs/TASK_QUEUE.md`, `docs/tasks/<milestone>/`,
`docs/tasks/reviews/`) are hardcoded inline inside 001/002's canonical text,
so wrapping Palimpsest's actual wording in a marker would be a false claim
(it isn't the canonical text) and would fail `meridian audit`. Bringing
Palimpsest to genuine compliance without changing its real file layout
requires the canonical text itself to stop hardcoding paths — a framework
change, not a Palimpsest-only one. Separately: `PROJECT_WORKFLOW.md` — the
single most important managed file, since it carries the `GOVERNED_SDD`
mode lock itself — has no capability tracking at all today, the same gap
001/002 had before migration 006, just not yet hit by a real incident.

**Migration 007 (shipped).** Markers + capability fields for
`validation-scoping` and `ci-verified-validation`, matching what 006 did for
001/002. Required relaxing `extract_marker_block`'s grammar to accept an
inline, mid-sentence marker (not just a marker on its own line), since
`validation-scoping`'s text in `AGENTS.md`/`CLAUDE.md` is one clause inside a
larger numbered step, not a standalone section.

**Migration 008 (planned).** `review-remediation-record` and
`lifecycle-orchestration` bump to `capabilityVersion: 2`: the canonical text
stops hardcoding `tasks/reviews/<TASK-ID>.md` / `tasks/QUEUE.md` inline and
instead references a project's declared "canonical locations" (a section
`PROJECT_WORKFLOW.md` already has conceptually). `delta` describes only this
reference change — no behavioral change for a vanilla project, since its
declared locations already match the defaults.

**Migrations 009-011 (planned): baseline capabilities for everything else
that's binding but untracked.** One capability per genuinely independent
rule, not one per file — a composite file keeps the same precision Phase 3
relies on. Two files are deliberately excluded: `docs/ARCHITECTURE_DECISIONS.md`
is a scaffold the project is meant to fill in, and `docs/OPERATOR_PROMPTS.md`
is an explicitly non-normative cookbook (`check_repository.py` already
enforces that it stays one) — protecting either would fight its purpose.

- **009 — `PROJECT_WORKFLOW.md`**, one capability per `##` section:
  `workflow-mode-lock`, `document-precedence`, `task-lifecycle`,
  `execution-assets`, `roles`, `review-policy`, `git-workflow` (folding in
  its `Reviewer-integrator identity` subsection), `execution-discipline`.
- **010 — whole-file capabilities** for single-purpose files:
  `language-policy` (`LANGUAGE_POLICY.md`), `task-blueprint`
  (`tasks/TASK_BLUEPRINT.md`), `code-organization`
  (`docs/CODE_ORGANIZATION.md`), `audit-prompt`
  (`docs/AUDIT_PROMPT_READ_ONLY.md`).
- **011 — `AGENTS.md`/`CLAUDE.md` residual sections**: `command-triggers`
  (the trigger-phrase list itself), `review-mode-boundary`,
  `owner-acceptance-workflow`, `implementer-reviewer-handoff`,
  `reviewer-integrator-identity`. `### Implementation workflow`'s steps 1-4
  and 6-8 stay untracked: the marker grammar has no nesting, and step 5
  already carries `validation-scoping`'s marker inside that same numbered
  section — wrapping the whole section would nest markers, which the parser
  does not support. Extending the grammar to support nesting is possible but
  deferred; it would mean revising a grammar already shipped in 006.

**Palimpsest retrofit (planned, after 007-011 land).** Every managed file
except the two excluded ones gets the protected-region + extension pattern:
canonical text byte-identical to the (parameterized, where applicable)
framework version, Palimpsest's own material — explicit `cargo` commands,
the `palimpsest-domain` Bevy-free boundary, ECHOES terminology, milestone
`*-VERIFY` PR gating, the reviewer-identity override — moved to clearly
labeled extension text immediately outside the marker, never inside it.
Verification: `meridian audit` all `PASS`, `meridian upgrade --check` zero
conflicts across all previously-conflicting files, and a manual line-by-line
diff confirming no existing Palimpsest rule was dropped, only relocated.
