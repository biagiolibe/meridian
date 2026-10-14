# Task 214 — Add security policy, code of conduct, and issue and PR templates

> **ID**: `214`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Public adoption readiness, 2026-10-14
> **Origin**: release

## Objective

The repository has no `SECURITY.md`, code of conduct, or issue or PR
templates. Meridian installs hooks, runs Git operations, and pushes on an
agent's behalf, so a public project needs a private channel to report
vulnerabilities and a predictable shape for reports.

## Acceptance Criteria

- [ ] `SECURITY.md` names the supported versions by reference to the support
  policy, the private reporting channel (GitHub private vulnerability
  reporting), what to include in a report, and the expected response. It does
  not publish a personal email address.
- [ ] `CODE_OF_CONDUCT.md` adopts the Contributor Covenant 2.1 with its
  attribution and names the same private reporting channel for enforcement.
- [ ] `.github/ISSUE_TEMPLATE/` has a bug report template and a feature
  request template, plus a `config.yml` that routes security reports to
  `SECURITY.md`. The bug template asks for the Meridian version (`meridian
  --version`), workflow mode, host, OS, and the exact `BLOCKED` line when
  there is one.
- [ ] `.github/pull_request_template.md` asks for the task ID, validation
  commands and results, and a changelog fragment when the change is
  user-visible, as `CONTRIBUTING.md` requires.
- [ ] `README.md` and `CONTRIBUTING.md` link `SECURITY.md` and
  `CODE_OF_CONDUCT.md`.
- [ ] `python3 scripts/check_repository.py` and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `SECURITY.md` | New security policy. |
| `CODE_OF_CONDUCT.md` | New code of conduct. |
| `.github/ISSUE_TEMPLATE/` | New issue templates. |
| `.github/pull_request_template.md` | New PR template. |
| `README.md`, `CONTRIBUTING.md` | Links. |

## Technical Context

- Private vulnerability reporting was enabled on 2026-10-14.
- Documentation-only change: the test suite may be skipped, recorded per
  `docs/CONTEXT_BUDGET_POLICY.md`.

## Validation

- `python3 scripts/check_repository.py`
- `git diff --check`

## Out of scope

GitHub repository settings, topics, and homepage, which are developer
actions.

## Dependencies

- **Depends on**: —
- **Blocks**: none
