# Task 042 — Deny over-budget absolute reads outside the project root

> **ID**: `042`
> **Category**: Bugfix (quick task)
> **Priority**: 🟡 P2
> **Assigned to**: Codex

## Objective

Keep the Codex read guard effective for recognised absolute paths outside a
Meridian project's root.

## Acceptance evidence

- The denial message uses a project-relative path when possible and an
  absolute path otherwise.
- A 500-line external temporary file addressed by `cat <absolute-path>` is
  denied with the file path and effective line count in the reason.
- `python3 -m unittest discover -s tests -v`,
  `python3 scripts/check_repository.py`, and `git diff --check` pass.

## Completion notes

The prior adapter counted an external absolute file, then raised `ValueError`
while rendering it with `path.relative_to(project)`. Its advisory-safe error
handling consequently allowed the command. `display_path()` now renders an
absolute path outside the project root without entering that allow path.

Validation passed on 2026-09-20: the targeted read-guard suite (8 tests), the
full test suite (165 tests), repository checks, and whitespace check.
