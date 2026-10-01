# Task 075 — Distribute the project console through the Meridian CLI

> **ID**: `075`
> **Category**: Developer tooling
> **Priority**: 🟡 P2
> **Assigned to**: Codex
> **Session**: Developer request for project-wide console distribution

## Objective

Expose the read-only project console through the distributed `meridian` command
and document how adopters launch it from any project containing Meridian files.

## Acceptance Criteria

- [ ] `meridian console` launches the existing interactive console for the
  current project.
- [ ] `--project PATH` and the console refresh interval remain available.
- [ ] The command resolves the console from the installed Meridian framework
  root and does not copy or modify project files.
- [ ] README documents installation, invocation, refresh behavior, and the
  supported Claude Code and Codex distribution paths.
- [ ] The distribution design records the command as part of the tagged tree,
  with no separate package or network dependency.
- [ ] Repository checks, CLI tests, console tests, and an interactive smoke
  check pass.

## Relevant Files and Context

- `bin/meridian` launches `scripts/meridian.py` from the installed framework.
- `scripts/project_console.py` owns the existing curses console.
- `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` defines tagged-tree distribution.
- Task 074 integrated terminal-default background handling.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_project_console.py'`
- CLI help and interactive PTY smoke checks.

## Dependencies

- **Depends on**: 074, 065
- **Blocks**: none
