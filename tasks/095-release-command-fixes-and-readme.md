# Task 095 — Fix the release command's usage and dry run, and update the README

> **ID**: `095`
> **Category**: Release tooling / Documentation
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Developer first run of `scripts/release.py` after Tasks 093 and 094

## Objective

Close two defects found when the maintainer first ran `scripts/release.py`, and
bring `README.md` in line with what Meridian now ships. The README must describe
the real commands and flags, not the ones planned in earlier tasks.

## Acceptance Criteria

### Release command

- [ ] `python3 scripts/release.py prepare --bump patch` (the form documented in
  `CONTRIBUTING.md` and Task 093) is accepted and behaves exactly like the
  current `python3 scripts/release.py --bump patch`, which keeps working.
  `python3 scripts/release.py publish …` is unchanged. `release.py --help`
  lists `prepare` and `publish` and states which one publishes.
- [ ] `--dry-run` prints, in this order: the derived release kind, the version,
  the files it would write, and only the new `## [<version>]` changelog section.
  It no longer prints the whole `CHANGELOG.md`. It still writes nothing, and a
  test asserts that the output is bounded (the section only) for a changelog
  with many older sections.
- [ ] Existing release tests keep passing, and new tests cover the `prepare`
  word, the unchanged no-word form, and the bounded dry-run output.

### README

- [ ] The "Repository layout" block lists every top-level directory that exists
  (`capabilities/`, `docs/`, `release-baselines/`, `releases/`, `schemas/`,
  `scripts/`, `tests/`, `tasks/`, and `.github/workflows/` if tracked) with one
  accurate line each, checked against the tree at task time.
- [ ] The Codex section mentions `meridian codex doctor` as the read-only check
  of the permission profile, the skill links, and `MERIDIAN_ROOT`, using the
  checks that the command actually prints.
- [ ] "Development and contributions" adds a short release subsection that names
  `python3 scripts/release.py prepare` and `publish`, states that `publish`
  pushes `main` and the tag only after `--confirm v<version>`, that the
  maintainer writes the changelog entries and any migration first, and links to
  the full procedure in `CONTRIBUTING.md`.
- [ ] The Roadmap paragraph no longer lists as a future goal something that
  already ships (the tagged install, update discovery, and the release command).
  It may state only goals that appear in `tasks/QUEUE.md`; it adds none that do
  not.
- [ ] Every command and flag shown in `README.md` exists in the current
  `--help` output of the corresponding command, verified at task time, and every
  relative link resolves. Examples keep `v<version>` placeholders, not a fixed
  version.
- [ ] No tracked file contains a machine-specific absolute path.
- [ ] `CHANGELOG.md` records both changes under `[Unreleased]`, in a section
  that matches the nature of the change (a fix for the command, documentation
  for the README).
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/release.py` | `main` dispatch and the dry-run printing. |
| `tests/test_release.py` | Existing and new tests. |
| `CONTRIBUTING.md` | Release procedure; already uses `release.py prepare`. |
| `README.md` | Layout block, Codex section, development and roadmap sections. |
| `CHANGELOG.md` | `[Unreleased]` entries. |

## Technical Context

- **Observed behavior**: `release.py prepare --bump patch --dry-run` fails with
  `unrecognized arguments: prepare`; `main` only special-cases `publish`
  (`values[0] == "publish"`) and sends everything else to the prepare parser.
- **Observed behavior**: `release.py --bump patch --dry-run` printed the whole
  new `CHANGELOG.md` (860 lines on 2026-10-01), so the useful part scrolled away.
- The README already documents the console split pane, the pinned install, the
  `meridian-local` migration, `meridian setup`, and `--check-latest`; this task
  does not rewrite those sections and only fixes statements that the
  verification above shows to be wrong.
- Lean Delivery applies: no new public `meridian` CLI surface is added, and
  `release.py` is maintainer tooling.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `python3 -m unittest discover -s tests -p 'test_release.py'`
- The README command and flag check is run by hand against each `--help` and
  recorded in the handoff; the layout check compares the block with `ls`.
- Evidence tier: command parsing and output size are program-computed and
  asserted; no manual evidence is required.

## Out of scope

Changing release semantics (kind derivation, protocol gate, push order),
publishing a release, rewriting README sections that are already accurate, and
any change to `prepare_release.py` or the workflow.

## Dependencies

- **Depends on**: 093, 094
- **Blocks**: none
