# Meridian Developer Machine Setup

This guide takes a macOS machine from zero to ready for developing Meridian
itself (`https://github.com/biagiolibe/meridian`) with Claude Code, Codex, or
by hand. It is written for two readers:

- **A human** following it step by step.
- **An agent** executing it on the human's behalf.

Each step has the same shape: **Check** (read-only), **Do** (the change),
**Verify** (proof that it worked). Skip a step's **Do** when its **Check**
already passes.

## Rules for agents executing this guide

1. Run every **Check** before its **Do**. Never run a **Do** whose **Check**
   already passes.
2. Steps marked **[HUMAN]** need the human: interactive sign-in, a Claude Code
   slash command, or explicit consent. Print the exact command, stop, and wait.
3. Steps marked **[CONSENT]** change global or user-level configuration
   (`~/.gitconfig`, `~/.zshrc`, `~/.codex/config.toml`, Claude Code settings).
   Show the planned change and get an explicit yes first.
4. Never push, force push, create or move tags, rewrite history, or delete
   folders while following this guide.
5. If a **Verify** fails, stop and report the command and its output. Do not
   improvise a workaround.
6. Never print tokens, passwords, or keychain contents.

## Variables used below

Adjust these once; every later command uses them.

```bash
export MERIDIAN_DEV_PARENT="$HOME/dev"                  # parent folder for the clone
export MERIDIAN_DEV_DIR="$MERIDIAN_DEV_PARENT/meridian" # the development clone
export MERIDIAN_RELEASE_DIR="$HOME/.local/share/meridian" # the released CLI (step 4)
```

These exports last only for the current shell. Step 4 persists the release
checkout as `MERIDIAN_ROOT` in `~/.zshrc`; commands you repeat later, such as
the update after each release, use `$MERIDIAN_ROOT`. An unset variable in
`git -C "$VAR"` is not an error: Git runs in the current directory.

The machine holds two Meridian checkouts with different jobs:

| Checkout | Follows | Used for |
|---|---|---|
| `$MERIDIAN_DEV_DIR` | `main` | Developing Meridian: edits, tests, task worktrees. |
| `$MERIDIAN_RELEASE_DIR` | `stable` (the latest release tag) | The `meridian` CLI on `PATH`, the Codex skills, and upgrades of every project that uses Meridian, including Meridian's own task lifecycle. |

---

## 1. Base tools

**Requirements**

| Tool | Minimum | Why |
|---|---|---|
| macOS Command Line Tools | any current | `git`, `bash`, `osacompile` |
| Homebrew | any current | installs the rest |
| Git | any current release | linked task worktrees |
| Python | **3.12 or later** | Meridian CLI, scripts, and tests (stdlib only, no `pip install`) |
| GitHub CLI `gh` | any current | CI evidence and release verification |
| Claude Code | current | primary agent host (plugin + hooks) |
| Codex CLI | current | second agent host (skills + hooks) |
| `jq` | optional | convenient for reading JSON output |

**Check**

```bash
xcode-select -p
brew --version
git --version
python3 --version
gh --version
claude --version
codex --version
```

**Do**

```bash
xcode-select --install          # [HUMAN] opens a system dialog
```

Install Homebrew from <https://brew.sh> **[HUMAN]**, then:

```bash
brew install git python@3.12 gh jq
```

Make Homebrew's Python the `python3` of every shell, including the one Codex
and Claude Code start **[CONSENT]** (append to `~/.zshrc`):

```bash
export PATH="$(brew --prefix python@3.12)/libexec/bin:$PATH"
```

Install Claude Code and Codex CLI following their official instructions
**[HUMAN]**, then sign in to each one **[HUMAN]**.

**Verify**

```bash
command -v python3                       # should point to Homebrew's python@3.12 (or newer)
python3 -c 'import sys; assert sys.version_info >= (3, 12), sys.version'
python3 -c 'import ssl, urllib.request; urllib.request.urlopen("https://api.github.com", timeout=10); print("TLS ok")'
```

> **TLS pitfall.** A Python installed from the python.org `.pkg` has no
> CA certificates until you run its `Install Certificates.command`. Without it,
> `meridian self-check --check-latest` reports
> `CERTIFICATE_VERIFY_FAILED`. Either run that command
> (`/Applications/Python 3.x/Install Certificates.command`) or put Homebrew's
> Python first on `PATH`.

---

## 2. Git identity and GitHub access

Commits need an explicit author identity. Use the GitHub account you
contribute with and its noreply address
(`<id>+<username>@users.noreply.github.com`, shown in GitHub's email settings).
Every commit email becomes public history, and removing one later means
rewriting the whole history (see `docs/history/HISTORY_REWRITE_2026-10-14.md`
on `main`). Never commit with a work or personal address.

**Check**

```bash
git config --global --get user.name
git config --global --get user.email
git config --global --get user.useConfigOnly
```

**Do** **[CONSENT]** (only for missing values)

```bash
git config --global user.name "<your name>"
git config --global user.email "<your commit email>"
git config --global user.useConfigOnly true
```

`user.useConfigOnly` makes Git refuse a commit that has no configured
identity instead of guessing one from the machine name.

On GitHub, under **Settings → Emails**, enable **Keep my email addresses
private** and **Block command line pushes that expose my email** **[HUMAN]**.
GitHub then rejects a push that carries your private address, so a wrong
identity on one machine cannot reach the repository.

Pushes over HTTPS prompt once for a username and a **personal access token**
**[HUMAN]**; the macOS keychain (`osxkeychain`) stores it. For SSH, add your key
to the GitHub account and clone with the `git@github.com:` URL instead.

**Verify** (after step 3 has created the clone)

```bash
git -C "$MERIDIAN_DEV_DIR" config --show-origin user.email   # the noreply address
```

### GitHub CLI account

`gh` keeps its own sign-in, separate from Git. Meridian's `ci_evidence.py` and
`release.py` call `gh`, so it must be signed in to an account that can read the
repository (publishing a release needs push rights).

**Check**

```bash
gh auth status
```

**Do** **[HUMAN]** (only if no suitable account is listed)

```bash
gh auth login --hostname github.com --git-protocol https
```

With several accounts, select the right one before CI-evidence or release work:

```bash
gh auth switch --hostname github.com --user <username>
```

Do **not** run `gh auth setup-git` unless you want `gh` to become the Git
credential helper for every repository on the machine.

---

## 3. Development clone

**Check**

```bash
test -d "$MERIDIAN_DEV_DIR/.git" && git -C "$MERIDIAN_DEV_DIR" remote get-url origin
```

**Do**

```bash
mkdir -p "$MERIDIAN_DEV_PARENT"
git clone https://github.com/biagiolibe/meridian.git "$MERIDIAN_DEV_DIR"
```

**Verify**

```bash
git -C "$MERIDIAN_DEV_DIR" status --short --branch                 # ## main...origin/main, clean
```

---

## 4. Released CLI and shell environment

The `meridian` command on `PATH`, `MERIDIAN_ROOT`, and the Codex skills point
at a **release checkout** that follows the `stable` branch. Each release's
`publish` fast-forwards `stable` to the commit of its tag, so this checkout is
always exactly on the latest release tag. That is what
`scripts/upgrade_project.sh` requires: it refuses a framework whose `HEAD` is
not the tag of its `VERSION`. A `MERIDIAN_ROOT` that points at the
development clone fails there as soon as `main` moves past a tag.

Meridian's own tasks use the released CLI too, exactly as an adopter would. A
broken `main` cannot block the task lifecycle, and Claude Code already runs the
released plugin (step 7). To run code that exists only on `main`, call it from
the development clone explicitly: `./bin/meridian` or
`python3 scripts/meridian.py --framework-root .`. `bin/meridian` resolves the
framework from its own location, so it needs no `MERIDIAN_ROOT`.

**Check**

```bash
git -C "$MERIDIAN_RELEASE_DIR" status --short --branch   # ## stable...origin/stable
grep -n 'MERIDIAN_ROOT' ~/.zshrc ~/.zprofile 2>/dev/null
```

**Do**

```bash
mkdir -p "$(dirname "$MERIDIAN_RELEASE_DIR")"
git clone --branch stable https://github.com/biagiolibe/meridian.git "$MERIDIAN_RELEASE_DIR"
```

**[CONSENT]** (append to `~/.zshrc`, or replace an existing `MERIDIAN_ROOT` line)

```bash
export MERIDIAN_ROOT="$HOME/.local/share/meridian"   # the value of MERIDIAN_RELEASE_DIR
export PATH="$MERIDIAN_ROOT/bin:$PATH"
```

Open a new terminal afterwards. Step 6 links the Codex skills to
`$MERIDIAN_ROOT/skills`.

**Verify**

```bash
command -v meridian                               # -> $MERIDIAN_ROOT/bin/meridian
meridian --version                                # -> same value as the next line
cat "$MERIDIAN_ROOT/VERSION"
git -C "$MERIDIAN_ROOT" describe --tags --exact-match   # -> v<that version>
```

**After each release**, move the release checkout forward, verify it, and
restart Codex and any open agent session so they use the new CLI. Use
`$MERIDIAN_ROOT`, which `~/.zshrc` sets in every shell:

```bash
test -n "$MERIDIAN_ROOT" && git -C "$MERIDIAN_ROOT" pull --ff-only origin stable
git -C "$MERIDIAN_ROOT" describe --tags --exact-match   # -> v<new version>
cat "$MERIDIAN_ROOT/VERSION"                            # -> <new version>
```

Then upgrade each project that uses Meridian (`meridian upgrade --check`, then
`--apply` on a dedicated branch), and refresh the Claude Code plugin with
`/plugin marketplace update meridian` if its marketplace follows `stable`.

---

## 5. Baseline validation

Run the same checks as CI (`.github/workflows/validate.yml`) from the clone.
These commands use the development clone's own code, not the released CLI.

```bash
cd "$MERIDIAN_DEV_DIR"
python3 scripts/check_repository.py
python3 scripts/meridian.py --framework-root . profile doctor meridian-self-hosting --project .
python3 scripts/meridian.py --framework-root . audit --project . --mode lean-delivery --ci-profile meridian-self-hosting
python3 scripts/run_tests.py --parallel
```

**Verify**

- `check_repository.py` prints `Meridian repository checks passed.`
- `profile doctor` ends with `SUMMARY ... FAIL=0`.
- `audit` ends with `CI_GATE ... failures=0`. `ADVISORY` and `UNVERIFIED`
  lines are expected and do not fail the gate.
- `run_tests.py --parallel` exits `0` and prints the `total` and `digest` lines.
  With about 1,000 tests it takes several minutes; run it in the background
  when an agent's command timeout is short.

If the parallel run cannot start its workers, use the sequential release gate:
`python3 -m unittest discover -s tests`. Changes under `bin/`, `migrations/`,
or `scripts/meridian.py` also need `python3 -m unittest discover -s tests -v`.

---

## 6. Meridian machine setup (worktrees, Codex profile, Claude allowlist)

Meridian runs every task in its own linked worktree under one machine-level
root (default `~/.meridian/worktrees`, overridable with
`MERIDIAN_WORKTREE_ROOT`). `meridian setup` prepares that root, the Codex
permission profile, the Codex skill links, and the project-local Claude Code
allowlist.

**Check** (read-only)

```bash
cd "$MERIDIAN_DEV_DIR"
meridian codex doctor
meridian setup --check
```

Read the `changes:` list that `setup --check` prints. On a fresh machine it
typically plans to:

- create `~/.meridian/worktrees` (owner-only permissions);
- add a `MERIDIAN:BEGIN worktree-permissions` block to `~/.codex/config.toml`
  that grants Codex write access to the worktree root;
- link `~/.agents/skills/meridian-lean-delivery` and
  `~/.agents/skills/meridian-governed-sdd` to `$MERIDIAN_ROOT/skills/...`;
- write an allowlist and `permissions.deny` rules into the ignored
  `$MERIDIAN_DEV_DIR/.claude/settings.local.json`;
- possibly write `.meridian/project.json` (a project declaration). That file
  is tracked; leave it out of this setup unless a task asks for it.

**Do** **[CONSENT]**

```bash
meridian setup --apply
```

Then restart Codex and Claude Code.

**Verify**

```bash
meridian codex doctor        # every line "ready"
meridian setup --check       # no remaining changes except ones you chose to skip
ls -la ~/.agents/skills
git -C "$MERIDIAN_DEV_DIR" status --short   # still clean (settings.local.json is ignored)
```

`.claude/settings.local.json` is ignored by Git, so a fresh clone never has it.
Run `meridian setup --apply` again after every re-clone.

---

## 7. Claude Code plugin

Claude Code loads Meridian as a plugin from the `meridian` marketplace. The
plugin provides the `/meridian-*` skills and the hooks (`read-guard`,
`queue-briefing`, `stop-audit`). It runs the **released** version, not the
development clone.

**Check**

```bash
python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); print(d['plugins'].get('meridian@meridian'))"
python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude/settings.json'))); print(d.get('extraKnownMarketplaces',{}).get('meridian'))"
```

**Do** **[HUMAN]** (slash commands inside Claude Code)

Pick one pin:

- `stable`: follows each published release; refresh with
  `/plugin marketplace update meridian`.
- `v<version>`: an exact tag; move it by hand.

```text
/plugin marketplace remove meridian
/plugin marketplace add biagiolibe/meridian#stable
/plugin install meridian@meridian
```

If `~/.claude/settings.json` declares `extraKnownMarketplaces.meridian` with a
different `ref`, `add` fails with `its source doesn't match its
extraKnownMarketplaces entry`. Change that `ref` to the one you add, or remove
the entry, first **[CONSENT]**. Removing the marketplace also uninstalls the
plugin, so always reinstall afterwards. Restart Claude Code.

**Verify**

```bash
meridian self-check --check-latest   # Installed / Latest / Status / Plugin ref lines
```

In Claude Code, `/plugin` shows `meridian@meridian` enabled with the expected
version. Old folders under `~/.claude/plugins/cache/meridian/` are not proof of
the active version; `installed_plugins.json` is.

---

## 8. Codex

**Check**

```bash
ls -la ~/.agents/skills                 # links created in step 6
ls ~/.codex/skills 2>/dev/null          # an old copy here shadows the links; remove it yourself
grep -n -A1 "projects.\"$MERIDIAN_DEV_DIR\"" ~/.codex/config.toml
```

**Do** **[HUMAN]**

1. Start Codex in `$MERIDIAN_DEV_DIR` and trust the project when asked. The
   project's `.codex/` layer (rules and `hooks.json`) is read only for a
   trusted project.
2. Accept the project hooks when Codex asks to trust them.
3. Restart Codex after any change to skills, profile, or `PATH`.

**Verify**

- `meridian codex doctor` reports `project-trust: ready` and
  `skill-links: ready`.
- In Codex, `$meridian-lean-delivery` is available.
- In a Codex shell, `python3 --version` reports 3.12 or later.

### Command approval rules

Codex prompts for every command that leaves its sandbox unless an execpolicy
rule allows it. The project rules in `.codex/rules/` apply only inside a
trusted project, and only to that project. The user-level file
`~/.codex/rules/default.rules` applies everywhere, including the task
worktrees under `~/.meridian/worktrees`. Rules match leading tokens only, and
when several rules match, the most restrictive decision wins.

**Check**

```bash
grep -n 'meridian\|"gh"\|"push"' ~/.codex/rules/default.rules
```

Look for broad rules that a "don't ask again" click may have created, such as
`["git", "push"]` or `["meridian"]` with no further token. They allow force
pushes and `--apply` commands without a prompt.

**Do** **[CONSENT]**

Back up the file, remove the broad rules found above, then append:

```text
# Plain pushes to origin only. A flag placed after the refspec
# (`git push origin main --force`) is not caught by prefix rules; the GitHub
# ruleset on main and stable is the real guard against that form.
prefix_rule(pattern=["git", "push", "origin"], decision="allow")
prefix_rule(pattern=["git", "push", ["--force", "-f", "--force-with-lease", "--delete", "-d", "--mirror"]], decision="forbidden")
prefix_rule(pattern=["git", "push", "origin", ["--force", "-f", "--force-with-lease", "--delete", "-d", "--mirror"]], decision="forbidden")

# Meridian read-only and task-lifecycle commands. Commands that change machine
# or project configuration (setup/codex configure --apply, upgrade --apply,
# adopt, finalize-adoption, lock, generate-*) keep prompting.
prefix_rule(pattern=["meridian", ["--version", "self-check", "console", "audit", "profile", "locations", "project", "context", "adr", "budget", "report", "usage", "validation", "execution", "task", "review"]], decision="allow")
prefix_rule(pattern=["meridian", "worktree"], decision="allow")
prefix_rule(pattern=["meridian", "codex", ["doctor", "worktree-path"]], decision="allow")
prefix_rule(pattern=["meridian", ["upgrade", "setup"], "--check"], decision="allow")
prefix_rule(pattern=["meridian", "codex", "configure", "--check"], decision="allow")

# Read-only GitHub CLI. `gh api` stays unlisted: it can send writing requests.
prefix_rule(pattern=["gh", "release", ["list", "view"]], decision="allow")
prefix_rule(pattern=["gh", "run", ["list", "view", "watch"]], decision="allow")
prefix_rule(pattern=["gh", "pr", ["list", "view", "checks", "diff"]], decision="allow")
prefix_rule(pattern=["gh", "issue", ["list", "view"]], decision="allow")
prefix_rule(pattern=["gh", "repo", "view"], decision="allow")
prefix_rule(pattern=["gh", "auth", "status"], decision="allow")

# Git and system commands that do not discard work.
prefix_rule(pattern=["git", "write-tree"], decision="allow")
prefix_rule(pattern=["git", "fetch"], decision="allow")
prefix_rule(pattern=["git", "restore", "--staged"], decision="allow")
prefix_rule(pattern=["git", "rm"], decision="allow")
prefix_rule(pattern=["git", "rm", ["-f", "--force"]], decision="prompt")
prefix_rule(pattern=["ps"], decision="allow")
```

Restart Codex; rules load when a session starts.

**Verify**

Each command must print the decision shown. Pass the command as separate
tokens after `--`, not as one quoted string.

```bash
R=~/.codex/rules/default.rules
codex execpolicy check --rules "$R" -- git push origin main          # allow
codex execpolicy check --rules "$R" -- git push --force origin main  # forbidden
codex execpolicy check --rules "$R" -- meridian worktree advance 1   # allow
codex execpolicy check --rules "$R" -- meridian upgrade --apply      # no decision: prompts
codex execpolicy check --rules "$R" -- gh release list               # allow
codex execpolicy check --rules "$R" -- gh api repos/x                # no decision: prompts
codex execpolicy check --rules "$R" -- git rm -f x                   # prompt
```

### GitHub branch protection

The repository ruleset **Protect main and stable** blocks force pushes
(`non_fast_forward`) and deletion of `main` and `stable`, with no bypass
actors. Task branches are not covered. A deliberate force push, such as a
history rewrite, needs the ruleset disabled first and re-enabled right after
**[HUMAN]**:

```bash
RULESET_ID=$(gh api repos/biagiolibe/meridian/rulesets --jq '.[] | select(.name == "Protect main and stable") | .id')
gh api -X PUT "repos/biagiolibe/meridian/rulesets/$RULESET_ID" -f enforcement=disabled
gh api -X PUT "repos/biagiolibe/meridian/rulesets/$RULESET_ID" -f enforcement=active
```

**Verify**

```bash
gh api repos/biagiolibe/meridian/rules/branches/main --jq '.[].type'   # non_fast_forward, deletion
```

---

## 9. Final checklist

Run from a **new** terminal. An agent reports each line's result.

```bash
cd "$MERIDIAN_DEV_DIR"
python3 -c 'import sys; assert sys.version_info >= (3, 12)' && echo "python ok"
test -n "$(git config user.email)" && echo "identity ok: $(git config user.email)"
git status --short --branch
test "$(meridian --version)" = "$(cat "$MERIDIAN_ROOT/VERSION")" && echo "cli ok"
git -C "$MERIDIAN_ROOT" describe --tags --exact-match && git -C "$MERIDIAN_ROOT" status --short --branch
meridian codex doctor
python3 scripts/check_repository.py
python3 scripts/run_tests.py --parallel
gh auth status
```

The machine is ready when every line succeeds, `codex doctor` is all `ready`,
and the plugin check in step 7 passes.

---

## 10. Working on Meridian

Read these in the clone before the first task:

- `CLAUDE.md` / `AGENTS.md`: agent rules for this repository.
- `PROJECT_WORKFLOW.md`: the Lean Delivery lifecycle (locked mode).
- `LANGUAGE_POLICY.md`: the conversation language; all repository text is
  English.
- `CONTRIBUTING.md`: validation, managed copies, changelog fragments, releases.
- `docs/WORKTREE_LIFECYCLE.md`: single-step lifecycle commands for recovery.

Day-to-day directives for an agent:

- `Proceed with <TASK-ID>`: implement one queued task end to end in its own
  worktree (`meridian worktree prepare` → implement → validate →
  `meridian worktree advance` → integrate → push `main` → cleanup).
- `Review <TASK-ID>`: read-only review.
- Small, reversible additions may be quick tasks directly on `main`.

The lifecycle commands (`meridian worktree ...`, `meridian task ...`) come
from the released CLI on `PATH` (step 4). A command that is new on `main` is
available to tasks only after it is released, unless you run it with
`./bin/meridian` from the clone.

Never part of a normal task: tags, releases, force pushes, history rewrites,
deleting unmerged branches. Releases go through
`python3 scripts/release.py` as described in `CONTRIBUTING.md`, run by the
maintainer.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `CERTIFICATE_VERIFY_FAILED` from `self-check` | python.org Python without CA bundle | Run `Install Certificates.command` or use Homebrew Python first on `PATH` |
| Commit refused: `no email was given and auto-detection is disabled` | No `user.email` configured | Set it (step 2); check with `git config --show-origin user.email` |
| Push authenticates as the wrong GitHub account | Keychain returns another account's token | Delete the wrong keychain entry for `github.com` and push again **[HUMAN]** |
| `Cannot add marketplace "meridian"` | `extraKnownMarketplaces` ref differs | Align or remove that entry (step 7) |
| `codex doctor` shows `blocked` | Codex profile diverges from Meridian's block | Reconcile `~/.codex/config.toml` by hand; `meridian codex configure --check` explains |
| `BLOCKED WRONG_WORKTREE` | Agent started outside the task worktree | Start in the path printed by `meridian worktree prepare` |
| `STOP: framework HEAD is not tag v<version>` from `upgrade_project.sh` | `MERIDIAN_ROOT` points at the development clone, which is past the tag | Point `MERIDIAN_ROOT` at the release checkout on `stable` (step 4) |
| Push rejected: `GH007: Your push would publish a private email address` | A commit carries your private email | Set the noreply address (step 2) and recreate the unpushed commits with it |
| `would clobber existing tag` on fetch, or `git pull` merges two unrelated histories | Clone made before the history rewrite of 2026-10-14 | Do not pull. Move the clone aside, clone again, and copy back ignored files such as `.claude/settings.local.json` |
| Codex prompts for a routine command | No execpolicy rule allows it, or the project rules are not loaded in this directory | Check it with `codex execpolicy check` (step 8); add a narrow rule only if the command cannot write or execute arbitrary code |
| Push rejected: `Cannot force-push to this branch` or `Cannot delete this branch` | The ruleset on `main` and `stable` | Intended. For a deliberate rewrite, disable the ruleset and re-enable it afterwards (step 8) |
| Tests fail only for AppleScript/iTerm2 | Sandbox cannot resolve the iTerm2 dictionary | Recorded as a named skip; run the full suite outside the sandbox before a release |
