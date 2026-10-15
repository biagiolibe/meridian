# Agent operations

Optional console, permission diagnostics, read-guard, and usage reference for
operators and maintainers. Start with the [adopter quick start](QUICKSTART.md).
These features keep the compatibility tiers in the [public surface](PUBLIC_SURFACE.md).

## Project console

The console, including its interactive keys and agent launch, is experimental;
it may change in minor releases.

From any project that contains Meridian's queue and task records, launch the
read-only interactive project console with:

```text
meridian console
```

It reads the current project's queue, open task details, dependencies, Git
summary, worktrees, and next permitted directives. Its heading and `--once`
snapshot identify the running Meridian version and framework root, so an
installed release is distinguishable from a repository checkout. The view
refreshes local state every two seconds and never writes project files. Use `--project
/path/to/project` to inspect another project and `--interval 5` to change the
refresh interval (between 0.2 and 60 seconds).

The console supports both `LEAN_DELIVERY` and `GOVERNED_SDD` projects, selected
from the mode lock in `PROJECT_WORKFLOW.md`. Because lifecycle edits are
committed on each task branch, it reads a task's queue row, record, handoff,
and review record from that branch with read-only Git commands and shows the
effective state with its source. Disagreements the lifecycle does not produce
appear as `MISMATCH` with no launch directive.

For active tasks, the detail pane and `--once` output also show wall-clock
cycle time from canonical worktree preparation, last activity, and the ordered
lifecycle gates still pending. Cycle time can include idle or waiting periods;
it is not active-agent time, an estimate, or an ETA. Legacy or unreadable
timing data is shown as unavailable without preventing use of the console.

A task stays listed after `meridian worktree integrate stage` marks its queue
row done (`[x]` in Lean Delivery, `ACCEPTED` in Governed SDD). Candidate
validation, finalize, and the `main` push still appear as `CLOSING`, a derived,
display-only state with lifecycle progress and the exact resume action.
Once only C10 cleanup remains, it counts as Done and leaves the Closing filter.
It remains accessible under All as Done, with a `Cleanup pending` hint and the
exact cleanup resume command in its detail pane and `--once` output. It is
excluded from the Open summary and offers no launch directive or active cycle
time. The console never performs cleanup; the row disappears when cleanup
removes the worktree, or C10 reports no resume action. Missing or unreadable
lifecycle state keeps the task Closing with progress shown as `unavailable`.
In Governed SDD a task waiting for approval shows its cycle time and a
`review pending` phase, and a reserved task worktree derives `IN_PROGRESS` or
`READY_FOR_REVIEW` from the task record because task branches do not edit the
queue.

For an eligible directive, `c` (or `[copy]`) keeps the copy-to-clipboard
fallback. On macOS with iTerm2, press `l` to open an isolated launch panel.
It shows the task, directive, project, agent choices, and safely discovered
configured model and effort defaults; press `1` for Claude Code or `2` for
Codex to revalidate and start that agent immediately, or `Esc` to cancel. The
shown defaults are informative and do not override agent configuration. The first launch may
cause macOS to ask permission for the terminal to automate iTerm2. Each launch
splits the console's current pane again, so repeated launches reduce the space
available to existing panes. Launching starts an agent that may modify the
project and counts as the developer's assignment of that task. The console does
not prepare worktrees: the permitted directive does so. If iTerm2, `osascript`,
the selected executable, or the console's iTerm2 session is unavailable,
the console reports the reason and `[copy]` remains available.

An ordinary `IN_PROGRESS` task offers **Resume** with the exact
`Proceed with <TASK-ID>` directive shown by `[copy]`. Resume is not a liveness
check: the console cannot tell whether another agent is still active, so it
requires an explicit warning confirmation before the agent choice. If the task
worktree has uncommitted changes, it requires a second, distinct confirmation.
The console reloads task state immediately before launch and refuses to proceed
if the directive or lifecycle changed. Closing tasks keep their lifecycle
resume command and never offer implementation Resume.

Repeating `Proceed with` is safe for an interrupted task: worktree preparation
selects the existing canonical branch and worktree, preserves its original
`started_at`, and does not create a second worktree. Resume still runs from the
primary checkout so the normal preparation and worktree checks remain in force.

The command is part of the tagged Meridian tree. Claude Code adopters receive
it through `${CLAUDE_PLUGIN_ROOT}/bin/meridian`; Codex adopters run the
`bin/meridian` launcher from their tagged checkout with `MERIDIAN_ROOT` pointing
at that checkout. No project-local copy, Python package, network service, or
background process is required.

## Codex command approvals in Governed SDD

After upgrading a Governed-SDD project, Meridian manages
`.codex/rules/meridian.rules`. It allows the workflow's routine Git commands
and narrow Meridian read-only or validation commands, forbids force-push
forms, and leaves all other commands to Codex's normal approval flow. Lean
Delivery projects do not receive this file.

Codex reads the project-local rules only after its `.codex` layer is trusted
in the user-level `~/.codex/config.toml`; Meridian cannot grant that trust, and
an untrusted project silently ignores the file. Inspect the file itself with:

```bash
codex execpolicy check --rules .codex/rules/meridian.rules -- git status
```

Then prove activation manually in a trusted Governed-SDD session: an allowed
command that previously prompted must run without an approval prompt. Project
rules combine with `~/.codex/rules/default.rules`, with the most restrictive
matching decision winning. `git -C <path> ...` cannot be covered by a prefix
rule, so use the execution tool's working-directory parameter instead.

Issue one command per execution call. In a trusted-project probe with Codex CLI
0.155.1, `git status && git diff --check` ran without a prompt and a chain
containing `git push --force` was refused, but `git status && git rebase main`
also ran without a prompt. Do not rely on later chain segments being evaluated.
The offline checker evaluates argument vectors rather than shell syntax.

## Codex large-file read guard in Governed SDD

Governed-SDD upgrades also manage `.codex/hooks.json`. After reviewing the
hook with `/hooks`, Codex invokes `meridian hook read-guard --host codex`
before Bash commands. It blocks recognised `cat`, `sed -n`, bounded
`head`/`tail`, and `nl | sed` reads when their combined effective output from
large files exceeds `Read-guard threshold` (400 lines by default). It does not
parse arbitrary shell, scripts, substitutions, heredocs, `awk`, or `python
-c`; those forms are allowed rather than falsely blocked.

Confirm activation in a trusted project by attempting `cat` on a file over the
threshold: Codex must deny it before execution. Use `rg -n` then ranged
`sed -n`, or `meridian context authority <TASK-ID>` / `meridian adr show
<ADR-ID>` for bounded source material. `meridian adr list [--status <value>]
[--format text|json]` prints one line per ADR (ID, title, status) to find the
governing ADR without opening the log. Declare a necessary file in task
Authority or raise `Read-guard threshold` only when the larger read is needed.

## Local session token usage

`meridian usage` and `meridian usage report` are experimental and may change
in minor releases.

`meridian usage report --format text` summarizes local Codex and Claude Code
session counters without reading or exposing message content. Filter a host,
project name, or date with `--host`, `--project`, and `--since`; add
`--breakdown` to identify the call where input grew most. The command is
read-only and local: it prints only timestamps, project directory names, model
metadata when recorded, and aggregate counters—not prompts, tool arguments,
file contents, or full paths. For both hosts `input` is the total input of a
call including cached input (Claude Code: `input_tokens` plus cache-read and
cache-creation tokens); `cached` is the cache-read part and `cache_ratio` is
`cached / input`. In JSON, `first_call_input`, `mean_call_input`,
`peak_call_input`, and `cumulative_input` use that total. A Claude Code call
with no usage counters is excluded and counted in `unavailable_calls`. Private host log formats can change; an absent or
unrecognized format reports `unsupported` clearly.

