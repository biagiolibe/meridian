# Task 011 — Warn about the head/SIGPIPE/pipefail trap in the template

> **ID**: `011`
> **Category**: Bugfix (template + migration)
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Ship with**: the next release that already changes a governed-SDD template — do not release alone.

## 🎯 Objective

`docs/EXECUTION_EVIDENCE_PROFILE.md` mandates `set -o pipefail` and an output
bound inside the command string, but does not warn that the obvious first-lines
idiom turns that `pipefail` into a false-failure generator. The template creates
the trap; the template should name it.

## 📋 Acceptance Criteria

- [ ] The profile's validation-output section states that a first-lines bound
      must consume the whole stream — `awk 'NR<=N'` or `sed -n '1,Np'` — and
      that `head -n N` and `sed 'Nq'` must not be used.
- [ ] It gives the mechanism in one sentence: the early-exiting stage closes the
      pipe, `SIGPIPE` kills the producer with status 141, and `pipefail` reports
      a failed pipeline for a command that succeeded.
- [ ] It states that the fault is intermittent — it fires only when output
      exceeds the bound — so it passes on a small project and starts failing as
      the suite grows.
- [ ] The text stays **stack-agnostic**: shell mechanics only, no language,
      build tool, or test runner. Per-stack examples stay in `WORKFLOW_GUIDE.md`.
- [ ] A migration record ships it, bundled per the constraint below.
- [ ] `python3 scripts/check_repository.py` and the CLI test suite pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md` | Where the warning goes. |
| `WORKFLOW_GUIDE.md` | Already carries the full explanation and measurements (commit `c138d4e`); do not duplicate it, reference the mechanism briefly. |
| `migrations/NNN-*.json` | Bundled migration record. |

## 🧩 Technical Context

Surfaced while reconciling Palimpsest onto 1.1.18. Measured there, 40-line bound
against a passing suite emitting 111 lines:

| Pipeline | Exit |
|---|---|
| `… \| head -n 40` | **101** — suite passing |
| `… \| awk 'NR<=40'` | 0 |
| `… \| tail -n 40` | 0 |

The distinction is which stage exits early, not `head` versus `awk`. Neither
safe idiom masks a real failure: a failing command still exits non-zero through
`awk` or `tail` under `pipefail`.

## ⚠️ Constraints and Considerations

- **Do not release this as a standalone version bump.** Reconciliation cost is
  per *upgrade run* per file, not per migration record — `scripts/meridian.py`'s
  `merge_clean` does one three-way merge from the stored baseline to the current
  template (`plan_from_baseline`), not a replay of each migration. So what
  spares an adopting project is not bundling records but **not making it upgrade
  twice**. Ship this in the same release as the next template change (009, 010,
  or whichever lands first).
- Keep it short. This is a warning inside an already-large always-loaded file;
  the full treatment lives in `WORKFLOW_GUIDE.md`.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/011-sigpipe-trap-in-template.md)"$'\n\nExecute this task in the current project.'
```
