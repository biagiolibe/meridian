# Task 049 — Design the distribution and update channel for adopters

> **ID**: `049`
> **Category**: Architecture
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: 2026-09-23 release-management gap review

## 🎯 Objective

Adopters install Meridian today by cloning the repository and registering it
as a **local** Claude Code marketplace (`meridian-local`, `source: "./"`), or
by symlinking skills for Codex. Nothing defines how an adopter installs a
specific release, learns that a newer release exists, or updates their
checkout safely before running `meridian upgrade`. Produce a decision
document that fixes these choices, then split the implementation into
follow-up tasks. This is a design task: no CLI or packaging code changes.

## 📋 Acceptance Criteria

- [ ] `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` exists and decides, with
      rationale and rejected alternatives, each of:
      - **Distribution channel(s)**: for example a public Git-hosted Claude
        Code marketplace, Codex skill installation, a Python package, or a
        combination; for each channel, what exactly an adopter installs.
      - **Version pinning**: how an adopter installs and stays on a given
        release (for example the `v<version>` Git tags created by task 021).
      - **Update discovery**: how an adopter learns a newer release exists
        (for example a `meridian self-check`/`--check-latest` command reading
        GitHub Releases, or documentation only), including offline and
        no-network behavior.
      - **Update procedure**: the ordered adopter steps from "new release
        exists" to "project upgraded" (update checkout or plugin, then
        `meridian upgrade --check` / `--apply`), and how
        `frameworkVersion`, `workflowBaselineVersion`, and `protocolVersion`
        tell the adopter what kind of update it is.
      - **Adopter-facing release notes**: where upgrade notes live
        (`CHANGELOG.md` section, GitHub Release body, or both) and what a
        template-changing release must say beyond a CLI-only one.
      - **Support policy**: which older releases are still upgradable from,
        consistent with `release-baselines/` and `migrations/`.
- [ ] The document lists the follow-up implementation tasks it implies, each
      with an objective and dependencies, and those tasks are added to
      `tasks/QUEUE.md` and `PROJECT_PLAN.md` as `[ ]`.
- [ ] `python3 scripts/check_repository.py` passes (including
      `check_local_markdown_links()`).

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | New decision document. |
| `README.md` | Current installation and "Framework upgrades" sections (input). |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Current plugin distribution (input). |
| `releases/`, `release-baselines/`, `migrations/` | Version and ledger mechanics the design must reuse. |
| `tasks/QUEUE.md`, `PROJECT_PLAN.md` | Follow-up tasks. |

## 🧩 Technical Context

- **Current behavior**: distribution means "clone `main`"; there are no Git
  tags yet, no public marketplace, and no update notification. The upgrade
  CLI is correct only once the adopter already has the newer checkout.
- **Desired behavior**: a documented, versioned path from "a release is
  published" to "an adopter's project is on it", built on the version split
  (tasks 015-020) and the release ledger (task 019).

## 🔨 Suggested Implementation

1. Read `README.md` installation and upgrade sections, the release ledger
   design (task 019), and the host capability contract
   (`docs/HOST_CAPABILITY_CONTRACT.md`) for Claude Code and Codex constraints.
2. Check the current Claude Code plugin marketplace and Codex skill
   distribution capabilities from their official documentation; cite what
   the design relies on.
3. Write the decision document and the follow-up task list.

## ⚠️ Constraints and Considerations

- If the chosen design introduces a public API, a network dependency, or a
  new persistence format, flag it: `PROJECT_WORKFLOW.md` says such risk may
  warrant Governed SDD for the implementation tasks.
- Do not publish anything (marketplace listing, package upload) in this task.

## 🔗 Dependencies

- **Depends on**: 019
- **Blocks**: none (its follow-up tasks will depend on it)

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/049-design-distribution-and-update-channel.md)"$'\n\nExecute this task in the current project.'
```
