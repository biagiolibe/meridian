# Task 069 — Document Codex install from a tagged checkout

> **ID**: `069`
> **Category**: Documentation
> **Priority**: 🟢 P3
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Task 049 distribution and update design

## 🎯 Objective

Document and verify the Codex channel from Decision 1: tagged checkout, `MERIDIAN_ROOT`, and skills in the user skills directory.

## 📋 Acceptance Criteria

- [ ] README Codex section documents cloning at `v<version>`, setting `MERIDIAN_ROOT`, and linking both skills into the verified user skills directory.
- [ ] The skills directory and `MERIDIAN_ROOT` resolution are verified in a real Codex session and recorded in `docs/HOST_CAPABILITY_CONTRACT.md`; unverified points stay labelled unverified.
- [ ] The update step (fetch, check out the new tag, then `meridian upgrade`) is documented.
- [ ] `python3 scripts/check_repository.py` passes.

## 📁 Relevant Files

`README.md`, `docs/HOST_CAPABILITY_CONTRACT.md`

## 🧩 Technical Context

Authority: `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`. Do not publish tags, releases, or marketplace listings unless the developer authorizes it separately.

## 🔗 Dependencies

- **Depends on**: 049
- **Blocks**: none

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/069-document-codex-install-from-tagged-checkout.md)"$'\n\nExecute this task in the current project.'
```
