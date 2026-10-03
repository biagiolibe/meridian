# Task 132 — Document the settings-pinned marketplace refusal and how to check the installed version

> **ID**: `132`
> **Category**: Documentation
> **Priority**: 🟢 P3
> **Estimate**: ~1h
> **Assigned to**: unassigned
> **Session**: Update of the Claude Code plugin to 1.2.6, 2026-10-03

## Objective

The README's update procedure says that re-adding a marketplace at a different
ref is refused and tells the reader to remove, add, and reinstall. It does not
cover a second, different refusal that a developer meets when the marketplace was
added through `extraKnownMarketplaces` in `~/.claude/settings.json` (or managed
settings): `/plugin marketplace add biagiolibe/meridian#v<new-version>` fails with
`Cannot add marketplace "meridian": its source doesn't match its
extraKnownMarketplaces entry in user or managed settings`, because that entry
pins the old ref (observed with `"ref": "v1.2.0"` while updating to 1.2.6). Add a
short note with the cause and the fix, and document how to confirm which Meridian
version Claude Code actually has installed.

## Acceptance Criteria

- [ ] `README.md`, in the plugin update procedure next to the existing "Move the
  pin" step, states the `extraKnownMarketplaces` refusal: the exact message, the
  cause (the settings entry lists a different source or ref), and the fix
  (change the entry's `ref` to the new tag, or remove the entry, then run
  `/plugin marketplace update meridian` or the remove, add, install sequence).
- [ ] The note says the entry may live in user settings or in managed settings,
  and that a managed entry cannot be changed by the developer and must be changed
  by whoever owns it.
- [ ] The README documents how to confirm the installed version from Claude Code,
  from most to least direct: the plugin list in `/plugin`; the installed-plugin
  record `~/.claude/plugins/installed_plugins.json` (field `version` of
  `meridian@meridian`); and `meridian self-check --check-latest`, whose
  `Installed`, `Latest`, and `Status` lines compare against the newest release.
  Each method is stated with what it proves, and the note says the plugin cache
  can keep older version folders that are not the active install.
- [ ] Every command and file path named in the new text was run or read on a
  real installation before being written, and the handoff records which were
  verified. Anything not verified is labelled as such in the README rather than
  asserted.
- [ ] `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` gets a one-line cross reference
  to the README note where it describes the marketplace pin, and no other
  design text changes.
- [ ] No script, template, migration, or behavior changes. The change is
  documentation only, so no version bump or migration is required, and one
  changelog fragment (`Documentation`) is added per `CONTRIBUTING.md`.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `README.md` | Plugin update procedure and the version-check note. |
| `docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` | One-line cross reference near the marketplace pin. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Recorded Claude Code behaviors for marketplace pinning, for consistency. |

## Technical Context

- Observed on 2026-10-03: `~/.claude/settings.json` held
  `extraKnownMarketplaces.meridian` with source `github`, repo
  `biagiolibe/meridian`, `ref: v1.2.0`, and `~/.claude/plugins/known_marketplaces.json`
  recorded the same ref. After the entry was moved to the new tag, the install
  record showed version `1.2.6` and commit `c7ac5e0`.
- The existing README text already covers the generic different-ref refusal, so
  the new note must not repeat it; it adds only the settings-entry case.
- The plugin cache can hold several version directories (for example `1.2.0` and
  `1.2.6`); the active one is the one named by the install record.

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Editing any user's or managed Claude Code settings, changing how Claude Code
resolves marketplaces, and Codex installation (not affected by this refusal).

## Dependencies

- **Depends on**: —
- **Blocks**: none
