# Task 224 — Rewrite the README around one host-neutral description

> **ID**: `224`
> **Category**: Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~3h
> **Assigned to**: unassigned
> **Session**: README review, 2026-10-15
> **Origin**: maintenance

## Objective

Meridian describes itself three different ways: the README subtitle ("Two
deliberate workflows for building software with AI coding agents: Lean
Delivery and Governed SDD."), the GitHub repository description, and the
`description` in `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`. The README is about 3,500 words and mixes
first-time visitors, adopters, and maintainers.

Adopt one description everywhere and restructure the README so a first-time
reader understands what Meridian does in under a minute. The description and
the README introduction must not name specific agent hosts: Meridian supports
Claude Code and Codex today, but the positioning must stay valid if hosts
change. Host names stay where they are factual (install instructions,
platform support).

The approved description is:

> Explicit tasks, isolated worktrees, verified integration. A delivery
> workflow for AI coding agents.

## Acceptance Criteria

- [ ] The README subtitle, `.claude-plugin/plugin.json`, and
  `.claude-plugin/marketplace.json` use the approved description verbatim.
  The handoff gives the developer the exact text for the GitHub repository
  description; the task does not change repository settings.
- [ ] The README header, introduction, and feature list name no specific
  agent host.
- [ ] The README opens with the logo header, the description, release, CI,
  and license badges, and a three-to-five sentence explanation of what
  Meridian is and what it is not (not an agent, no stack, no service).
- [ ] A "Meridian in 30 seconds" section shows a short task file excerpt and
  what `Proceed with <TASK-ID>` does: worktree, validation, integration, push,
  cleanup.
- [ ] A concise feature list covers explicit tasks, per-task worktrees,
  command-backed stops, denied destructive actions, migration-based project
  upgrades, the project console, and host hooks.
- [ ] Lean Delivery is presented first as the default mode; Governed SDD
  follows for higher-risk work.
- [ ] Install sections are short and link to `docs/QUICKSTART.md`; the
  version example is current or uses the `stable` ref.
- [ ] `docs/QUICKSTART.md` no longer names a superseded release: its clone
  command uses `--branch stable`, or the current release tag with a note that
  `stable` avoids editing it at each release. Today it clones `v1.2.15`.
- [ ] The update procedure covers the local framework checkout that provides
  the `meridian` CLI and the Codex skills, not only the Claude Code plugin pin
  and the project upgrade. `docs/HOW_TO_UPGRADE.md`, linked from the README,
  documents both variants:
  - a checkout that follows `stable`: `git -C "$MERIDIAN_ROOT" pull
    --ff-only`;
  - a checkout pinned to a tag: `git -C "$MERIDIAN_ROOT" fetch --tags` then
    `git -C "$MERIDIAN_ROOT" checkout v<version>`.

  Both end with the check that `upgrade_project.sh` relies on: `git -C
  "$MERIDIAN_ROOT" describe --tags --exact-match` prints `v<version>`, matching
  `VERSION`. The procedure says to restart running agent sessions so they use
  the new CLI.
- [ ] Detailed sections move to dedicated documents and leave a link:
  Updating Meridian, Framework upgrades, Codex command approvals, Governed
  execution evidence, and Language behavior. No content is lost; each moved
  section is findable from the README.
- [ ] The Documentation links are grouped by reader: adopters, agent
  operators, maintainers.
- [ ] The README is under 1,000 words (`wc -w README.md`).
- [ ] `tests/test_public_surface.py` and every README-dependent test pass;
  any assertion that depends on moved text is updated to the new location.
- [ ] A changelog fragment `changelog.d/224.md` records the documentation
  change.

## Relevant Files

| File | Role |
|------|------|
| `README.md` | Rewritten. |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Description. |
| `docs/QUICKSTART.md` | Install target for README links; stale `v1.2.15` clone command. |
| `docs/HOW_TO_UPGRADE.md`, `docs/AGENT_OPERATIONS.md` | Destinations for moved sections. |
| `docs/assets/` | Logo used in the header. |
| `tests/test_public_surface.py` | Reads the README. |

## Technical Context

- **Current behavior**: three different descriptions; long README with
  operational detail; no usage example; Governed SDD explained more than Lean
  Delivery.
- **Desired behavior**: one host-neutral description; a short README for
  first-time readers with links to detailed documents.

## Constraints and Considerations

- Repository text stays in English.
- Do not change `docs/PUBLIC_SURFACE.md` classifications or any stable
  surface while moving text.
- Keep `scripts/check_repository.py` Markdown link checks green.

## Dependencies

- **Depends on**: none
- **Blocks**: none

## Validation

```bash
python3 scripts/check_repository.py
python3 scripts/run_tests.py --parallel
wc -w README.md
```

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/224-readme-rewrite-and-unified-description.md)"$'\n\nExecute this task in the current project.'
```
