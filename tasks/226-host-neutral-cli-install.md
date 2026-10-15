# Task 226 — Install the Meridian CLI once, at one path, for every host

> **ID**: `226`
> **Category**: Documentation (plus a Python version guard in `bin/meridian`)
> **Priority**: 🟡 P2
> **Estimate**: ~2h
> **Assigned to**: unassigned
> **Session**: Installation review, 2026-10-15
> **Origin**: friction

## Objective

The install documentation never presents the `meridian` CLI as its own step.
The release checkout is cloned only under the Codex instructions
(`README.md` "Install", `docs/QUICKSTART.md` "Install for Codex"), into
`~/meridian`. The Claude Code path offers no reliable terminal CLI:

- `docs/QUICKSTART.md` says to use the installed plugin's absolute
  `bin/meridian` path or to add it to `PATH`;
- that path holds the version
  (`~/.claude/plugins/cache/meridian/meridian/<version>/bin`), so every plugin
  update breaks it;
- the same quick start then runs `meridian setup --check` and `--apply` from
  a shell for every reader.

A developer who uses both hosts ends up with two framework copies, the plugin
cache and the checkout, possibly at different versions. The maintainer guide
already uses `~/.local/share/meridian`, but the public documentation uses
`~/meridian`.

Make installation two host-neutral steps: first install the framework and its
CLI at the single canonical path `~/.local/share/meridian`, for every reader,
then connect the host.

## Acceptance Criteria

- [ ] `docs/QUICKSTART.md` starts installation with one step for every reader,
  before any host-specific step:

  ```bash
  git clone --branch stable https://github.com/biagiolibe/meridian ~/.local/share/meridian
  export MERIDIAN_ROOT="$HOME/.local/share/meridian"
  export PATH="$MERIDIAN_ROOT/bin:$PATH"
  ```

  It tells the reader to persist both exports in the shell startup file that
  their terminal and agent host load. Then it verifies with
  `command -v meridian`, `meridian --version`, `cat "$MERIDIAN_ROOT/VERSION"`,
  and `git -C "$MERIDIAN_ROOT" describe --tags --exact-match`.
- [ ] The persistence instruction names a file that non-interactive shells
  also read, because an agent host or script can start `zsh -lc` or
  `zsh -c`, which do not read `~/.zshrc`. For zsh it recommends `~/.zshenv`;
  for bash it names the equivalent pair (`~/.profile` or `~/.bash_profile`,
  plus `~/.bashrc`). It adds a check that works without an interactive shell:
  `zsh -lc 'command -v meridian'` (or `bash -lc` for bash) prints the
  checkout's `bin/meridian`.
- [ ] The prerequisites tell the reader to check `python3 --version` in the
  same non-interactive form, because on macOS a `PATH` without Homebrew
  resolves `python3` to the system Python 3.9.
- [ ] `bin/meridian` stops with a clear message and a non-zero exit when the
  interpreter is older than Python 3.12, before importing the CLI. The message
  names the required version, the version found, and the interpreter path
  (`sys.executable`), and points to the quick start prerequisites. Today the
  CLI fails with `ModuleNotFoundError: No module named 'tomllib'`. The guard
  itself must parse and run on Python 3.9, so it uses no newer syntax. A test
  runs the wrapper under a simulated old version and checks the message and
  exit code; the existing CLI tests keep passing.
- [ ] The host steps follow the CLI step:
  - **Claude Code**: the marketplace plugin on `#stable`, with a note that the
    plugin and the checkout must stay at the same release, and that the
    terminal uses the checkout CLI, not the plugin cache path;
  - **Codex**: `meridian setup --check` and `--apply` for skill links and
    the permission profile, with no separate clone.
- [ ] `~/.local/share/meridian` is the only install path in user-facing
  documentation. No instruction tells an adopter to clone to `~/meridian` or to
  add the plugin cache directory to `PATH`. A pinned tag keeps the same path:
  `--branch v<version>` instead of `--branch stable`.
- [ ] `README.md` "Install" shows the same two steps in short form and links
  to the quick start. The README stays under 1,000 words (`wc -w README.md`).
- [ ] `docs/HOW_TO_UPGRADE.md` "Update the framework first" names the canonical
  checkout and explains that a Claude Code user updates both the checkout and
  the plugin. It keeps the rule that a checkout must be exactly at a release
  tag. Any section that task 225 added for `meridian self-update` stays intact.
- [ ] The "framework root" examples in `docs/HOW_TO_UPGRADE.md` use
  `$MERIDIAN_ROOT` or `~/.local/share/meridian` first; the plugin cache path
  remains only as a documented alternative for `--meridian-root`.
- [ ] Historical evidence is not rewritten. `docs/CLEAN_INSTALL_VERIFICATION.md`
  records what a past release tested with `$HOME/meridian`; it gains at most one
  note that the current canonical path is `~/.local/share/meridian`.
- [ ] Tests that read the quick start, README, or upgrade guide pass. Any
  assertion on the old clone path or section heading moves to the new text.
  If no test checks that the quick start installs at the canonical path, add
  one.
- [ ] A changelog fragment `changelog.d/226.md` records the documentation
  change under `Changed` and the Python version message under `Fixed`.
- [ ] `python3 scripts/check_repository.py`, `python3 scripts/run_tests.py
  --parallel`, and `git diff --check` pass.

## Relevant Files

| File | Role |
|------|------|
| `docs/QUICKSTART.md` | Install steps, currently split by host. |
| `README.md` | Short install section. |
| `docs/HOW_TO_UPGRADE.md` | Framework update and framework root examples. |
| `docs/CLEAN_INSTALL_VERIFICATION.md` | Historical install evidence; note only. |
| `bin/meridian` | CLI wrapper; gains the Python version guard. |
| `tests/` | Public documentation tests. |

## Technical Context

- The maintainer guide on the `maintainer-docs` branch
  (`MERIDIAN_DEVELOPER_SETUP.md`, step 4) already installs the release checkout
  at `~/.local/share/meridian` on `stable` and persists `MERIDIAN_ROOT` and
  `PATH` in `~/.zshrc`. The public quick start should match it.
- `scripts/upgrade_project.sh` refuses a framework whose `HEAD` is not exactly
  the tag of its `VERSION`. A checkout on `stable` satisfies this after each
  release's `publish`.
- Evidence of 2026-10-15, from a clean isolated home: with the exports only
  in `~/.zshrc`, `zsh -c` and `zsh -lc` do not find `meridian`, while
  `zsh -ic` and `zsh -ilc` do. With `PATH=/usr/bin:/bin` on macOS,
  `meridian --version` fails on the system Python 3.9 with
  `ModuleNotFoundError: No module named 'tomllib'`.
- Task 225 adds `meridian self-update`, which updates the checkout that the CLI
  runs from; it relies on every reader having that checkout.

## Constraints and Considerations

- Repository text stays in English.
- Do not change `docs/PUBLIC_SURFACE.md` classifications.
- Keep `scripts/check_repository.py` Markdown link checks green; the README
  links `docs/QUICKSTART.md#install-for-codex` today, so update anchors that
  change.

## Dependencies

- **Depends on**: 225 (in progress; both edit `README.md` and
  `docs/HOW_TO_UPGRADE.md`). Start after 225 is integrated.
- **Blocks**: none

## Validation

```bash
python3 scripts/check_repository.py
python3 scripts/run_tests.py --parallel
wc -w README.md
git diff --check
```

## How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/226-host-neutral-cli-install.md)"$'\n\nExecute this task in the current project.'
```
