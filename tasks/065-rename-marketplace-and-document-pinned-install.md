# Task 065 — Rename the marketplace and document the pinned install

> **ID**: `065`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Task 049 distribution and update design

## 🎯 Objective

Rename the marketplace from `meridian-local` to `meridian`, rewrite the README installation and update sections around `/plugin marketplace add biagiolibe/meridian#v<version>`, and verify the claims empirically.

## 📋 Acceptance Criteria

- [ ] `.claude-plugin/marketplace.json` `name` is `meridian`; `claude plugin validate .` passes.
- [ ] README installation documents pinned add at `#v<version>`, plugin install as `meridian@meridian`, and the ordered update procedure from `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`.
- [ ] The one-time migration for `meridian@meridian-local` installs is documented in README and CHANGELOG.
- [ ] Pinned add, plugin update to a newer tag, and `${CLAUDE_PLUGIN_ROOT}/bin/meridian` resolution from an installed plugin are verified against a real tag and recorded in `docs/HOST_CAPABILITY_CONTRACT.md`; anything unverified stays labelled unverified.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## 📁 Relevant Files

`.claude-plugin/marketplace.json`, `README.md`, `CHANGELOG.md`, `docs/HOST_CAPABILITY_CONTRACT.md`

## 🧩 Technical Context

Authority: `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`. Do not publish tags, releases, or marketplace listings unless the developer authorizes it separately.

## 🔗 Dependencies

- **Depends on**: 049
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/065-rename-marketplace-and-document-pinned-install.md)"$'\n\nExecute this task in the current project.'
```
