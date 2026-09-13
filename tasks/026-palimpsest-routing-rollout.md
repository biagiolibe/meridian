# Task 026 — Roll out routing to Palimpsest and measure initial context

> **ID**: `026`
> **Category**: Integration
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned

## Objective

Upgrade Palimpsest to the compact-routing release and verify that Claude Code
and Codex begin status, tech-design, implementation, and review work without
loading a universal monolith.

## Acceptance Criteria

- [ ] Palimpsest upgrades from a clean checkout with no lost customized rule
      and a passing `meridian audit`.
- [ ] Its `CLAUDE.md` uses the explicit pointer marker and routes silently,
      mentioning precedence only for a real conflict or blocker.
- [ ] Before/after byte measurements for both entry points are recorded.
- [ ] One status/question, `Proceed`, and `Review` session demonstrate the
      expected routed reads and preserve all required safeguards.

## Constraints

- Do not overwrite consumer-project changes or use `adopt`.
- Stop on an upgrade conflict and record it for an explicit resolution.

## Validation

- `meridian upgrade --project <palimpsest> --check`
- `meridian audit --project <palimpsest> --mode governed-sdd`
- `git diff --check`

## Dependencies

- **Depends on**: 025
- **Blocks**: none
