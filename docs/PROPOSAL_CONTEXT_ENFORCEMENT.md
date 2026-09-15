# Proposal — Context Enforcement, Second Pass

Status: **M1/M2 shipped** (`tasks/done/034`, `tasks/done/035`, commit
`4ab174d`); M3/M4/M5/M6 not scheduled. See §8 for the closure report — read
that first if resuming this work. Author context: post-mortem of a
Palimpsest `M25-SPIKE-001` session, generalized so the interventions apply
to every Meridian project rather than to that one session.

Prior work this builds on: `docs/AUDIT_TOKEN_EFFICIENCY.md` (findings F1–F11,
proposals P1–P7) and `docs/PLAN_TOKEN_EFFICIENCY.md` (W0–W4). Read those only
if a cross-reference below needs its detail.

## 1. Evidence

One governed spike session in Palimpsest, 25 model responses, no subagents,
roughly 1.0M weighted tokens (cache read 0.1, cache write 2, output 5):

| Bucket | Weighted tokens | Share |
|---|---|---|
| Files read and edited | ~396k | 38% |
| Fixed per-turn preamble (~57k × 25) | ~394k | 38% |
| Reasoning and written output | ~173k | 17% |
| Command output (cargo/git/meridian) | ~73k | 7% |

Context peaked at ~213k tokens. Heaviest reads: the ADR log range
ADR-0059..0063 (~8k; only 0063 and 0060 were needed), `simulation.rs` in full
(~7k; ~60 lines needed), `PROJECT_WORKFLOW.md` (~5k),
`PULL_REQUEST_POLICY.md` and `EXECUTION_EVIDENCE_PROFILE.md` (~3–4k each),
the M24 verification report (~3k). Avoidable command output: a full probe
`{:#?}` dump (~2k raw) and `git branch -a` (~1.5k raw).

What worked: cargo output redirected to a file and read partially; parallel
independent reads; the probe succeeded without tune cycles.

## 2. Diagnosis

### D1 — The violated rules already exist

Four of the six observed inefficiencies are already prohibited in text:

- whole-file and unrelated-ADR reads: `CONTEXT_BUDGET_POLICY.md` §Task-first
  loading, items 2–3;
- unbounded probe output and reloading already-available instructions:
  capability `execution-evidence-profile v3`.

This re-confirms audit F1/F2: prose budgets do not bind. The only discipline
that held in the session is the one resolved mechanically — the
`queue-briefing` hook (migration 026). Adding more prose raises the fixed
cost and changes nothing. Durable fixes must be (a) mechanical enforcement,
(b) making the cheap path the default path, or (c) deleting text that is not
the operative rule.

### D2 — The fixed preamble is mostly harness, not docs

Instruction files loaded every turn total ~1.2k tokens (global `CLAUDE.md`
2.6KB, project `CLAUDE.md` 37 lines, `AGENTS.md` 1.4KB, memory index). The
remaining ~55k of the ~57k per-turn floor is most plausibly tool schemas,
MCP server definitions, and skill descriptions injected by the host (the
session ran in the Claude desktop app, which adds Browser, iOS Simulator,
visualize, Artifact, and session-management tools). No documentation change
reaches that 38%. **Measured** — see §5.

### D3 — Entry documents carry non-operative verbatim text

Palimpsest `PROJECT_WORKFLOW.md` lines 40–237 (~80% of the file) are
verbatim framework capability regions kept only so `meridian audit` matches
the release, each followed by a note saying the operative rule lives
elsewhere. Every read pays ~5k tokens for text that is explicitly not the
rule. The existing pointer mechanism (`is_agents_pointer`, migration 032)
covers only `CLAUDE.md` → `AGENTS.md`, not these regions. This is a concrete
instance of audit F3 (additive-only markers ratchet).

### D4 — The global instructions contradict governed projects

`~/.claude/CLAUDE.md` contains the Lean methodology (checkbox statuses,
`tasks/done/`, `PROJECT_PLAN.md`) and is loaded in every project. Governed
`PROJECT_WORKFLOW.md` (capability `workflow-mode-lock`) prohibits exactly
that fallback. Small token cost, but a standing contradiction on every turn.

## 3. Framework interventions (Meridian)

Ordered by expected yield. Each ships as a numbered migration where it
changes a managed path; hook/CLI changes run from `$CLAUDE_PLUGIN_ROOT` and
reach every project immediately (as in migration 026).

### M1 — Authority excerpt command (highest yield) — `tasks/034` ✅ shipped

- `meridian adr show <ADR-ID> [--project .]`: print exactly one ADR section
  from the project's ADR log, split by heading.
- `meridian context authority <TASK-ID> [--project .]`: parse the task's
  `Authority` field and print only the cited ADR sections and spec sections
  (heading-scoped), each with its source path and line range.
- `queue-briefing.sh`: when a task is `IN_PROGRESS`, append its resolved
  authority list with line ranges to the briefing.
- Policy text: one marker line in `CONTEXT_BUDGET_POLICY.md` pointing sessions
  at the command as the normal path (mirroring `queue-briefing v1`).

Acceptance: on Palimpsest, `meridian context authority M25-SPIKE-001` emits
only ADR-0060 and ADR-0063 sections; unit tests cover heading splitting,
missing IDs (non-zero exit, clear message), and spec-section anchors.

### M2 — `PreToolUse` read guard — `tasks/035` ✅ shipped

A plugin hook on `Read`: if the target exceeds a threshold (default 400
lines, overridable in `EXECUTION_EVIDENCE_PROFILE.md`) and neither `offset`
nor `limit` is set, deny with a message naming the cheap path
(`grep -n` → ranged `Read`, or `meridian adr show`). Exempt the assigned task
file, the entry router, and `LANGUAGE_POLICY.md`. Only active in projects
carrying a Meridian workflow file.

Risk: friction on legitimately small-but-long files; mitigated by the
per-project threshold and an allowlist. Acceptance: hook tests for
over/under threshold, ranged reads, exemptions, and non-Meridian projects.

### M3 — Move compatibility baselines out of entry documents

A migration adding a `baseline-relocation` capability: marker regions that a
project keeps only for framework compatibility (i.e. followed by a declared
"operative version elsewhere" note) move to `.meridian/baseline/<file>.md`.
The entry document keeps a one-line pointer per region. `meridian audit`
verifies the relocated copy byte-for-byte; `upgrade` updates it there.

Acceptance: Palimpsest `PROJECT_WORKFLOW.md` drops from ~236 to ~40 lines
with `meridian audit` still passing; regions without an operative-elsewhere
note are never moved.

### M4 — Make the global instructions a pointer

Replace the Lean methodology body in `~/.claude/CLAUDE.md` (and whatever
Meridian installer/skill writes it) with a ≤5-line pointer: "in a project
with `PROJECT_WORKFLOW.md`, follow it; lean rules live in the
`meridian-lean-delivery` skill". Removes the D4 contradiction everywhere.

### M5 — Context checkpoint hook

A `UserPromptSubmit` (or `Stop`) hook estimates context size from the
transcript at `transcript_path`. Above a threshold (default ~120k estimated
tokens) it emits an advisory: write the durable handoff and continue in a
fresh session. In `TASK_BLUEPRINT.md`'s spike shape, split "investigate" and
"draft deliverable (ADR)" into two phases separated by a handoff note.

Advisory only — the estimate is approximate and must never block.

### M6 — Bounded probes for spikes

Extend the spike shape so a probe command is declared like a validation
command, output bound included, and run via `meridian execution evidence`.
Probe code prints summary lines only (e.g. `PROBE key=value`); full dumps go
to a file under the evidence directory and are read by range. Complements
audit P2 / plan W1.1, which bound validation commands but not probes.

## 4. Project interventions (Palimpsest) — lower yield

- **P1** — Declare bounded Git commands in `EXECUTION_EVIDENCE_PROFILE.md` as
  literal command strings (`git branch --list '<task>*'`,
  `git log --oneline -n 10`), not as new paragraphs.
- **P2** — Optional, only after M1: split `docs/ARCHITECTURE_DECISIONS.md`
  (4032 lines, 65 ADRs) into one file per ADR plus an index. It breaks
  existing citations; M1 captures most of the gain without it.
- **P3** — ~~Add a project `.claude/settings.json` disabling unused MCP
  servers.~~ Downgraded to negligible by §5: MCP tools already cost 0 tokens
  in the CLI. Pruning unused skill plugins remains a ≤2k option.

Rejected: a separate "spike excerpt" document (~40 lines) of operational
rules. Adding a document to a system whose problem is document proliferation
raises the floor; M3 delivers the same saving by shrinking the existing file.

## 5. Fixed-preamble measurement (resolved)

Measured with `/context` in a fresh interactive `claude` CLI session inside
the Palimpsest checkout, before any prompt (model `claude-sonnet-5`, 1M
window). The preamble is session-independent, so a fresh session is a valid
measurement of the evidence session's floor.

| Category | Tokens | Notes |
|---|---|---|
| System prompt | 9.3k | |
| System tools | 28.7k | largest item; effectively irreducible |
| Memory files | 1.8k | 3 files: global `CLAUDE.md`, project `CLAUDE.md`, `MEMORY.md` |
| Skills | 2.9k | 19 skills |
| MCP tools | 0 | 2 tools, loaded on demand |
| Messages | 8 | |
| **Total** | **42.7k** | |

Findings:

1. **Host choice is the main fixed-preamble lever.** CLI floor 42.7k versus
   ~57k per response inferred for the desktop-app evidence session: ~14k per
   response (~25% of the floor) is desktop-specific tool schemas. This
   confirms D2 in order of magnitude. Caveat: the evidence session's model
   may differ from Sonnet 5; tool schemas are broadly model-independent.
   Mostly served from cache (weight 0.1), so the weighted saving is smaller
   than the raw ~350k over 25 responses, but it applies to every turn.
2. **P3 is downgraded to negligible.** MCP tools already cost 0 tokens in the
   CLI (on-demand loading); disabling servers in `.claude/settings.json`
   saves nothing there.
3. **M4 is downgraded to a clarity fix.** All memory files together are 1.8k;
   its value is removing the D4 contradiction, not tokens.
4. **Skills are a minor lever.** Disabling plugins a project never uses
   (e.g. docx/pptx/xlsx/pdf) would save an estimated 1–2k per response.
5. System prompt plus system tools (~38k) is the irreducible floor.

Operational recommendation: run governed worker sessions (implementation,
review, spikes) from the CLI rather than the desktop app. Everything else on
the fixed preamble is worth low single-digit thousands of tokens.

## 6. Expected impact (estimates)

- M1 + M2: target the 38% file bucket; plausibly remove most of the
  ~120–160k avoidable weighted tokens per comparable session, with compounding
  savings because context stays smaller on every later turn. Still the
  largest lever overall.
- Running workers from the CLI: ~14k raw tokens off every response.
- M3: ~5k per read of `PROJECT_WORKFLOW.md`, constant per session.
- M4, P3, skill pruning: ≤2k per response combined; M4 kept for clarity.

## 7. Suggested next steps

1. Adopt the CLI-for-workers recommendation immediately (no code change);
   consider stating it in `OPERATOR_PROMPTS.md`.
2. ~~M1 and M2 are queued as `tasks/034` and `tasks/035`~~ — done, see §8.
   M3 (migration), M5, M6, and M4 (low-priority clarity fix) remain to be
   turned into task files, in that priority order (§8).
3. Palimpsest P1 as a governed task once M1 lands; P2 only if still justified
   afterwards; P3 dropped unless a future host loads MCP schemas eagerly.

## 8. Closure report — M1/M2 (2026-09-16)

`tasks/034` and `tasks/035` are both `[x]`, implemented (not just marked
done) in commit `4ab174d`: `meridian adr show`/`meridian context authority`
plus the `queue-briefing.sh` extension, migration `039`; `hooks/read-guard.sh`
registered on `PreToolUse`, migration `040`. Both `tests/test_authority_excerpt.py`
and `tests/test_read_guard.py` were added. Verified after landing:
`python3 -m unittest discover -s tests` → 146 tests, OK (the `FAIL:`-prefixed
lines printed mid-run are captured stdout from tests that deliberately inject
drift to check detection — expected, not suite failures); `python3
scripts/check_repository.py` → passed standalone.

**Does this close the evidenced problem?** Mostly yes, for the dominant
cause. Weighed against the original session's four buckets:

| Bucket | Share of ~1.0M weighted tokens | Addressed by M1+M2? |
|---|---|---|
| Files read out of scope | 38% (~396k) | Yes, almost all of it — this is exactly what M1 (targeted ADR/spec excerpts) and M2 (mechanical block on unranged large reads) attack. |
| Fixed per-turn preamble | 38% (~394k) | No — §5 found the floor is mostly host/system-tool schemas (~28.7k of 42.7k on the CLI), not reducible by any Mx here. The applicable lever was "run workers from the CLI, not the desktop app," already independent of M1–M6. |
| Reasoning and written output | 17% | Not addressed by any Mx. |
| Command output | 7% | Partially — M6 (not yet built) would close the remainder. |

D1's causal claim — that the file-read bucket was the largest and the
easiest to prevent, since its rules already existed in prose and were simply
unenforced — is what M1/M2 turn from prose into a mechanical default. That
is the substantive part of the diagnosis, and it is now shipped.

**What M3–M6 would still add, and why they were left out this round:**

- **M3** (move compatibility baselines out of entry documents): small,
  constant saving (~5k per read of `PROJECT_WORKFLOW.md`), better cost/yield
  ratio than M4–M6 — the next one worth doing if this is resumed.
- **M4** (global `CLAUDE.md` as a pointer): ~1.8k total across all memory
  files: negligible in tokens, valuable only for removing the D4 workflow
  contradiction.
- **M5** (context checkpoint hook): does not reduce tokens already spent;
  it is a preventive measure against a session growing past ~120k like the
  evidence session did (213k peak), not a remediation of the measured spend.
- **M6** (bounded probe output): closes the remaining slice of the smallest
  bucket (7% command output).

None of M3–M6 changes the answer to "was the evidenced problem addressed":
the largest and most fixable cause (file reads) is closed; the second-largest
(fixed preamble) turned out to be mostly non-addressable by documentation or
task work at all, and its one actionable lever (CLI over desktop) was already
adopted as a standing recommendation rather than a task. M3–M6 are
diminishing-returns refinements, worth doing eventually, not required to
consider this round resolved.
