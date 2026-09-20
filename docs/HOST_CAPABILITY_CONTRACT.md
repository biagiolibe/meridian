# Host Capability Contract

Status: Design baseline. This document records host-specific evidence and
release expectations; it does not itself create a task, change a template, or
claim that an unimplemented control is enforced.

## Purpose

Meridian has one workflow policy, but Claude Code and Codex reach that policy
through different instruction files, plugin/skill distribution paths, tools,
approval systems, and trust models. A workflow rule is not an effective
constraint merely because its prose exists in both host-facing assets.

Every claim about a host-dependent capability therefore identifies a concrete
host profile and one of these states:

| State | Meaning |
|---|---|
| `enforced` | The host invokes a verified adapter that prevents the prohibited action. |
| `advisory` | The host receives guidance or a reminder, but can still bypass it. |
| `unsupported` | Meridian intentionally provides no adapter for this host profile. |
| `unverified` | An adapter, claim, or runtime path exists but lacks the required evidence. |

An installed file is not evidence that a capability is active. For a
host-managed adapter, distinguish `installed`, `configured`, `trusted`, and
`effective`; only the last state supports an `enforced` claim.

## Host profiles

The contract applies to a versioned profile, not an umbrella product name.
At minimum, release evidence names the host, host version, invocation mode,
and relevant configuration layer.

| Profile | Distribution path | Notes |
|---|---|---|
| Claude Code plugin session | Claude plugin, `CLAUDE.md`, slash commands, plugin hooks | Plugin lifecycle and the native `Read` tool are distinct from Codex shell execution. |
| Codex project session | `AGENTS.md`, optional Codex skill, project `.codex/` files | Project hooks and rules require the project's Codex configuration layer to be trusted. |
| Codex plugin session | Codex plugin hook/configuration plus `AGENTS.md` | Plugin hooks also require trust; `PLUGIN_ROOT` is available and `CLAUDE_PLUGIN_ROOT` remains a compatibility variable. |
| Host-neutral CLI | `bin/meridian` and managed project files | The CLI may be common, but PATH, current directory, sandbox, and approval behavior remain host-specific. |

## Capability matrix

| Capability | Claude Code profile | Codex project profile | Required evidence before an enforcement claim |
|---|---|---|---|
| Workflow router and language policy | `CLAUDE.md` supplies the route and policy. | `AGENTS.md` supplies the route and policy; a skill is an optional reusable layer. | Fresh-session evidence of the auto-loaded entry point, route selection, and policy salience. Byte equality alone is insufficient. |
| Managed entry-point integrity | Template/generator tests preserve expected `CLAUDE.md` content. | Template/generator tests preserve expected `AGENTS.md` content. | Static generator and audit tests plus one host-session route fixture per release that changes routing. |
| Queue and language briefing | `UserPromptSubmit` hook is an advisory salience aid. | No equivalent adapter is distributed. | Claude: plugin-hook invocation fixture. Codex: retain `unsupported` unless a trusted adapter and probe are shipped. |
| Authority excerpts and execution budgets | Available through the Meridian CLI when the plugin root resolves it. | Available through the Meridian CLI when `MERIDIAN_ROOT`/PATH and cwd resolve it. | Per-profile bootstrap/doctor check proving the exact command can be found and executed from a project subdirectory. |
| Large-file read guard | Existing plugin hook targets the native `Read` tool; unit tests cover its policy semantics. | The governed-SDD `.codex/hooks.json` adapter intercepts recognised Bash reads after project-hook trust. | Native payload fixture and real hook invocation for Claude; recorded Codex payload, parser table, denial fixture, trust proof, and no false-deny regression for Codex. |
| Command approval policy | No Meridian-managed, project-scoped equivalent is currently shipped. | `templates/workflows/governed-sdd/.codex/rules/meridian.rules` is distributed on upgrade, but it is effective only after project-layer trust. | A decision table evaluated by the host plus a real trusted-project chain test. Approval evidence does not prove sandbox access. |
| Trust activation | Must be observed for the installed plugin/hook definition. | Local rules/hooks are inactive until the project layer and current hook definition are trusted. | An activation check that distinguishes missing, untrusted, trusted, and effective states. |
| Shell and chained commands | Host-specific behavior must not be inferred from rule text. | Codex CLI 0.155.1 trusted-project probe: an all-allowed `&&` chain ran without a prompt; a force-push chain was refused; an unmatched later `git rebase` segment still ran. Governed sessions must issue one command per call. | A fixture for simple command, chain, pipe, redirection, and unsupported syntax, with the expected allow/deny behavior recorded per host. |
| Sandbox and Git operations | Permission and filesystem outcomes depend on the runtime environment. | Approval rules cannot override filesystem sandboxing, network restrictions, or Git worktree restrictions. | A host-specific preflight that reports whether the intended Git/filesystem operation is executable, needs approval, or is unavailable. |
| Review isolation | Task-tool or a fresh independent session may provide isolation. | A separate thread/subagent may provide isolation when available; otherwise use a fresh chat. | The skill must state the current adapter and fallback without assuming a host limitation that has not been verified for the current version. |
| Upgrade and adoption entry point | Claude commands use `CLAUDE_PLUGIN_ROOT`. | Codex guidance uses `MERIDIAN_ROOT`/CLI discovery. | One clean project upgrade/adoption check from each host profile that the release claims to support. |

## Verified Claude Code read-guard probe

On 2026-09-20, a temporary Meridian-shaped repository with a 401-line target
file was used with Claude Code `2.1.278`, model `claude-sonnet-5`, and the
Meridian plugin loaded directly through `--plugin-dir`.

| Question | Result |
|---|---|
| Does the Meridian plugin load? | Yes. Claude reported the Meridian plugin and its hooks in the session metadata. |
| Does `PreToolUse:Read` fire for a native Read? | Yes. |
| Is an unranged over-threshold Read prevented? | Yes. The hook exited `2`, returned its structured deny output, and the tool result was classified as a non-execution permission rule. |
| Does the model receive an actionable reason? | Yes. It reported that the 401-line read was blocked by the 400-line threshold. |

This verifies the existing Claude read guard for this direct-plugin CLI profile.
It does not by itself prove that a marketplace-installed plugin, another Claude
runtime, or a different tool path loads the same hook definition.

## Verified Codex hook probe

On 2026-09-20, a scratch Git repository was used with Codex CLI 0.155.1 and a
trusted project-local `.codex/hooks.json` logging hook.

| Question | Result |
|---|---|
| Does `PreToolUse` fire for the shell path? | Yes. |
| What tool name is exposed? | `Bash`. |
| Where is the command? | `tool_input.command`. |
| Are multiline input and `&&` preserved? | Yes; both arrive in the one command string. |
| Can a hook block the entire invocation? | Yes. A hook emitting a reason on stderr and exiting `2` blocked both sides of an `&&` chain before either ran. |
| Is JSON alone sufficient with exit `2`? | No in this probe: Codex reported that no blocking reason had been written to stderr and the chain ran. |
| Does trust matter after a hook change? | Yes. Changing the hook definition required a new manual trust review before it ran. |

This established task 041's probe classification A for this profile. The
subsequent implementation added the parser, exemptions, managed distribution,
and redacted fixtures; other Codex runtimes remain unverified.

Task 041 subsequently recorded redacted individual `sed`, chain, `cat`, and
`rg` payload fixtures. The trusted definition is stored in
`~/.codex/config.toml` under `hooks.state`, keyed as
`<project>/.codex/hooks.json:pre_tool_use:0:0`; changing it requires another
manual `/hooks` review. The hook process had the project cwd, `MERIDIAN_ROOT`,
and a PATH containing `MERIDIAN_ROOT/bin` (but no `PLUGIN_ROOT`). Its deny
probe confirmed that stderr plus exit `2` blocks the whole chain and conveys
the reason; structured JSON is supplementary.

On 2026-09-20, a trusted Palimpsest project session denied both a 2,520-line
project file and `cat /private/tmp/meridian-read-guard-probe.txt > /dev/null`
for an external 401-line file before execution. Together with task 042's
external-path regression fixture, this is enforcement evidence for the named
trusted Codex project-session profile, not for a Codex plugin session or every
future Codex runtime.

## Required host-impact gate

Before a task changes a workflow rule, hook, command, generated instruction,
skill, permission policy, or CLI bootstrap path, its task record must state:

1. **Policy outcome** — the host-independent behavior being protected.
2. **Affected profiles** — each host/runtime/version/invocation mode affected,
   plus profiles explicitly out of scope.
3. **Adapter state** — `enforced`, `advisory`, `unsupported`, or `unverified`
   before and after the change.
4. **Activation preconditions** — installation, trust, PATH, cwd, sandbox,
   permissions, and any user action required.
5. **Evidence plan** — static fixture, host execution fixture, and required
   manual observation. A host claim without a matching evidence item remains
   `unverified`.
6. **Fallback** — the safe behavior and user-visible message if the adapter
   cannot run or cannot determine the host payload.

The implementation and review report must repeat the profiles actually
verified. A repository test may prove parser or template semantics, but cannot
by itself promote a host integration to `enforced`.

## Decision rules

- Prefer a common policy with narrow host adapters over a common parser that
  assumes identical tools or payloads.
- Prefer a false allow to a false deny for advisory shell parsing unless the
  protected operation is independently unsafe; false denials stall legitimate
  work and invite workarounds.
- Treat approval, trust, sandbox access, and execution success as separate
  facts. No one fact implies another.
- Do not add host-specific prose to generic workflow policy when an adapter,
  a profile row, or a fallback statement expresses the requirement more
  precisely.
- Do not describe a capability as cross-host parity until its expected outcome
  has been demonstrated in every profile named by the claim.

## Open evidence

| Item | Current state | Needed evidence |
|---|---|---|
| Claude plugin read-guard activation | `enforced` for the tested direct-plugin Claude Code 2.1.278 profile. | Marketplace-installed plugin activation and any other Claude runtime remain unverified. |
| Codex command approval policy | `enforced` for the Codex CLI 0.155.1 trusted project profile. | Other Codex versions and plugin sessions remain unverified; governed sessions issue one command per invocation. |
| Codex read guard | `enforced` for the trusted Palimpsest Codex project-session profile, including the recorded external absolute-path read. | Other Codex versions and plugin sessions remain unverified. |
| Router auto-load parity | `unverified` as a release-wide claim. | Fresh-session evidence for the actual entry point and route-specific initial reads on both profiles. |
| Codex review-isolation adapter | `unverified`; existing skill language may be stale. | Versioned check of available subagent/thread capability and a documented fresh-chat fallback. |
| Host-neutral CLI bootstrap | `unverified` across profiles. | Subdirectory PATH/cwd checks for authority, upgrade, adoption, and hook entry points. |

## Non-goals

This contract does not introduce a new task lifecycle, make Codex and Claude
mechanically identical, distribute rules or hooks, change the current template
set, or replace a task-specific acceptance criterion. It is the design record
used to scope those changes safely.
