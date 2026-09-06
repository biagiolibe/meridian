# Quality and Compliance Roadmap

Status: proposal, not started. This is a backlog of candidate framework
changes, not an authorized work plan — pick items to implement individually
rather than treating this file as a queue to execute end to end.

## Why this exists

Meridian's process is enforced almost entirely through prose an agent is
expected to follow — task review policy, ancestry checks, reviewer
independence, audit conformance. Nothing in the repository mechanically
verifies that an agent actually did what the instructions said. The
capability-aware adoption CLI (`bin/meridian adopt --assisted`) proved a
better pattern for one slice of the framework: replace a coordination
convention that lives in an agent's memory with a deterministic state
machine, backed by durable state on disk, that a tool computes and a
coordinator merely reads (see [migrations/ASSISTED_ADOPTION.md](migrations/ASSISTED_ADOPTION.md)
and the `NEXT_ACTION` state machine in `scripts/meridian.py`). This roadmap
is that same pattern applied to the parts of Meridian that still rely on
prose-only enforcement.

Each item below cites the concrete gap it closes so a future session does not
need to re-derive the rationale.

## Tier 1 — low effort, closes a real gap now

- [ ] **Run the CLI test suite in CI.** `.github/workflows/validate.yml` only
  runs `scripts/check_repository.py`; `tests/test_meridian_cli.py` — the
  suite covering `bin/meridian` itself — never runs in CI, despite
  [CONTRIBUTING.md](CONTRIBUTING.md) requiring it for changes under `bin/`,
  `migrations/`, or `scripts/meridian.py`. Add
  `python3 -m unittest discover -s tests -v` as a CI step.
- [x] **`CHANGELOG.md`.** Done — see [CHANGELOG.md](CHANGELOG.md). Keep it
  updated alongside `migrations/*.json` and any framework-CLI change.
- [ ] **`meridian status` / `meridian doctor` command.** A read-only,
  deterministic introspection command for a generated project: installed
  version, pending migrations, missing capabilities (reusing
  `detect_capabilities`), and queue health (tasks `IN_PROGRESS` past some
  age, tasks missing a review record their status implies). Same
  control-plane philosophy as `adopt`/`upgrade`, applied to day-to-day
  operator visibility instead of one-time migration.

## Tier 2 — structural, meaningful compliance value

- [x] **Versioned capability markers and protected regions.** Done — full
  design and status in
  [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md)
  (phases 1-4 shipped; phase 5, process discipline and opportunistic
  retrofit onto migrations 003-005 and already-adopted projects, is
  ongoing). Fixes presence-only detection (a migration that *modifies* an
  existing capability is now visible) and phrase-based fragility (failed on
  a project whose wording predated the exact token, twice this session on
  real projects); `upgrade` now tells a cosmetic merge conflict (project
  already has the rule, worded its own way) from a real one instead of
  requiring `--owner-reconciled` on faith.
- [~] **Deterministic audit instead of a prose audit prompt.** Partially
  done: `meridian audit --project <path>` exists and mechanically verifies
  protected capability-marker integrity (phase 4 of
  `CAPABILITY_MARKERS.md`) — see
  [commands/meridian-audit.md](commands/meridian-audit.md). Still missing:
  the original motivating check, that every `ACCEPTED` task has a matching
  `APPROVE` verdict in its review record (`docs/AUDIT_PROMPT_READ_ONLY.md`
  item 12), which an *agent* still verifies by reading `git log` rather than
  a script parsing `tasks/QUEUE.md`/`tasks/reviews/*.md` mechanically. Add
  that check to the same `audit` command rather than a second one. Keep the
  remaining, genuinely judgment-based audit items (ADR consistency,
  architectural-boundary framing) as agent-performed.
- [ ] **Multi-level risk classification.** Review policy is binary
  (`REQUIRED`/`NOT_REQUIRED`). Introduce a risk tier (e.g.
  `LOW`/`MEDIUM`/`HIGH`/`CRITICAL`) that drives proportionate control —
  two-reviewer or mandatory-human-review for `CRITICAL`, single
  agent-reviewer for `LOW` — instead of one binary switch for every kind of
  change. Reuses the same "explicit override for an exception" shape already
  established by `finalize-adoption --owner-accepted`.
- [ ] **Explicit security gate.** Security currently appears only as one
  bullet among many review triggers in `docs/CODE_REVIEW_PROMPT.md`. Add a
  dedicated, separately-triggered check (secret scanning, dependency
  vulnerability check) that must pass before `ACCEPTED`, distinct from the
  general correctness review.
- [ ] **Lightweight requirement traceability.** A task cites its "authority"
  in prose today; nothing verifies the citation is real or current. Consider
  a checkable requirement ID convention (spec/ADR ID referenced by the task,
  verifiable by a script) so traceability survives beyond the honor system.

## Tier 3 — vision, for a genuinely regulated context (SOC 2 / ISO-style)

- [ ] **Structured, append-only audit log.** Today the only durable evidence
  of what happened is Git history plus prose in review records — readable by
  a human, hard to query or export for an external auditor. Consider
  `.meridian/audit-log.jsonl`: one event per state transition (task/adoption
  ID, actor role, verdict, commit SHA, timestamp).
- [ ] **Reviewer diversity for high-risk changes.** "A fresh session"
  guarantees context independence but not model independence — the same
  underlying model reviewing its own kind of mistake is a known blind spot.
  For `CRITICAL`-tier changes, consider requiring either a human reviewer or
  a different model/provider, not just a different session.
- [ ] **Dependency and license policy.** No documented gate for approving a
  new third-party dependency (license compatibility, known vulnerabilities).
- [ ] **Incident/rollback playbook.** No documented procedure for what
  happens when an `ACCEPTED` task later causes a production incident — no
  revert lifecycle state, no `docs/INCIDENT_RESPONSE.md`.
- [ ] **Optional data-handling/privacy overlay.** For projects that process
  personal data, no equivalent of the existing workflow overlays
  (`templates/workflows/*`) covering data classification or retention.

## Sequencing note

Tier 1 items are safe to do independently and in any order. Tier 2's audit
script and risk-tier item are easiest if done together, since the audit
script is the natural place to verify that a `CRITICAL` task actually got the
stronger review its tier requires. Tier 3 items are speculative until a real
compliance requirement (a specific customer, framework, or regulation) makes
one of them concrete — implementing them speculatively risks the same
over-engineering Meridian's own contribution guidance warns against.
