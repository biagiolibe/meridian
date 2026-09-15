# Task 034 — Add `meridian adr show` and `meridian context authority`

> **ID**: `034`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~4h
> **Assigned to**: unassigned

## Objective

Give a session a way to read exactly the ADR/spec sections a task cites
instead of opening the whole log. `docs/PROPOSAL_CONTEXT_ENFORCEMENT.md` (M1)
measured this as the single largest avoidable read in a governed session
(~8k tokens to read ADR-0059..0063 in Palimpsest when only two of the five
were cited).

## Acceptance Criteria

- [ ] `meridian adr show <ADR-ID> --project <path>` prints exactly one ADR
      section (from `## ADR-NNNN` up to the next `## ADR-` heading or EOF)
      from the project's ADR log, resolved the same way `execution contract`
      resolves canonical paths (respecting a project's declared location,
      default `docs/ARCHITECTURE_DECISIONS.md`).
- [ ] Unknown ADR ID: non-zero exit, message names the ID and the file
      searched, no partial output.
- [ ] `meridian context authority <TASK-ID> --project <path>` parses the
      task file's `Authority` field, resolves each cited ADR ID through
      `adr show` and each cited spec section through the same heading-range
      logic against the project's declared spec file, and prints each
      excerpt labeled with its source path and heading (line numbers not
      required — headings are the addressable unit).
- [ ] A task `Authority` entry that is not an ADR ID or a resolvable spec
      heading is reported as unresolved (name it, do not silently skip it)
      rather than causing a non-zero exit for the whole command.
- [ ] `docs/CONTEXT_BUDGET_POLICY.md` gains one line in the "Task-first
      loading" list (mirroring the existing `queue-briefing v1` marker
      pattern) pointing sessions at `meridian context authority` as the
      normal path before opening an ADR log or spec file directly.
- [ ] `hooks/queue-briefing.sh`: when a task is `IN_PROGRESS`, append its
      resolved `Authority` list (source + heading, not the full excerpt) to
      the existing briefing output.
- [ ] Unit tests cover: heading splitting with adjacent ADRs, an ADR ID at
      EOF, a missing ADR ID, a task with no `Authority` field, and at least
      one project using a non-default ADR log path.

## Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | Add `adr` and `context` subcommands; reuse `detect_mode`/project-root resolution already used by `execution contract`. |
| `hooks/queue-briefing.sh` | Extend the `IN_PROGRESS` branch to call the new command and append its output. |
| `docs/CONTEXT_BUDGET_POLICY.md` | New capability marker, e.g. `capability=authority-excerpt v1`, in the Task-first loading list. |
| `docs/PROPOSAL_CONTEXT_ENFORCEMENT.md` | Source measurement and rationale (§3, M1). Do not duplicate its content elsewhere. |
| `tests/` | New test module for ADR/spec heading resolution. |

## Constraints

- Read-only command: never writes to the ADR log, spec files, or task files.
- Heading-range extraction must not depend on ADR numbering being
  contiguous or sorted in the file.
- Ship as a migration (new `MERIDIAN:BEGIN capability=authority-excerpt v1`
  marker in `CONTEXT_BUDGET_POLICY.md`) so adopting projects get the pointer
  on upgrade; the CLI/hook change itself runs from `$CLAUDE_PLUGIN_ROOT` and
  reaches every project immediately, same as migration 026.
- Does not touch `PROJECT_WORKFLOW.md`'s document-precedence rules or any
  review/lifecycle capability.

## Validation

- `python3 -m unittest discover -s tests`
- `python3 scripts/check_repository.py`
- Manual: run `meridian context authority M25-SPIKE-001 --project <palimpsest checkout>`
  and confirm it prints only ADR-0060 and ADR-0063, not the full log.

## Dependencies

- **Depends on**: none
- **Blocks**: none (independent of 035)

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/034-authority-excerpt-command.md)"$'\n\nExecute this task in the current project.'
```
