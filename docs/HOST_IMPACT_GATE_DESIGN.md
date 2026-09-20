# Host-Impact Task Contract and Completion Gate

Status: Proposed design for Task 043. This document authorizes neither a
template change nor a lifecycle implementation.

## Problem and policy outcome

A workflow policy can be correct in a repository and still be ineffective in
a host session. Claude Code and Codex differ in tool names, configuration
layers, trust prompts, plugin roots, shell delivery, PATH, sandboxing, and
approval behavior. A task that changes any of those surfaces must therefore
state what behavior it protects and the exact host profiles for which that
behavior has evidence.

The policy outcome is not host parity. It is accurate claims: an adapter is
called `enforced` only for a versioned profile where its activation and
prohibited outcome were observed.

## Task-record declaration

Every normal governed-SDD task will carry one compact `Host impact` section.
It has two mutually exclusive shapes.

### Not applicable

```text
## Host impact

Classification: NOT_APPLICABLE
Rationale: [why this change cannot alter workflow instructions, a hook,
permission policy, generated entry point, skill, CLI bootstrap, or host adapter]
```

This is the default for ordinary application work and documentation that does
not change a host-facing contract. It is intentionally one classification and
one rationale, not a host matrix.

### Required

```text
## Host impact

Classification: REQUIRED
Policy outcome: [host-independent behavior protected]

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| [host/version/invocation/config layer] | [state] | [state] | [facts] | [safe behavior] |

Evidence plan:
- Static: [fixture or deterministic check]
- Host execution: [command/tool fixture and expected outcome]
- Manual activation: [trust, install, or UI observation when needed]

Completion evidence:
- [profile]: [source, observed result, or explicitly retained `unverified` state]
```

`Before` and `Intended after` use only `enforced`, `advisory`, `unsupported`,
or `unverified`. A profile identity includes host product and version,
invocation mode, and the configuration layer that supplies the adapter; for
example, `Codex CLI 0.155.1 / project session / trusted .codex hooks` is not
equivalent to a Codex plugin session.

## Applicability and evidence rules

A task is `REQUIRED` when it changes a workflow instruction, generated entry
point, hook, command, skill, permission policy, CLI bootstrap path, or the
managed distribution of any of those. A task author selects the classification
rather than relying on a source-diff heuristic. This keeps the first release
bounded: a diff cannot reliably reveal a runtime configuration change or a
host integration added outside one expected path.

`NOT_APPLICABLE` is an assertion subject to review. Its rationale is the
auditable escape hatch; it must not be used to avoid a host probe for a known
host-sensitive surface.

For each `enforced` completion claim, the completion evidence must contain:

1. a static test or fixture for adapter or template semantics;
2. an execution observation from the named profile showing the prohibited
   action was prevented or the required action was available; and
3. any installation, trust, PATH, cwd, sandbox, or permission observation
   needed to explain why the adapter was active.

An unavailable probe does not permit an `enforced` claim. The profile remains
`unverified`, `advisory`, or `unsupported`, with its fallback stated. Sandbox
approval, trust, and command success remain separate observations.

## Lifecycle boundary

The first implementation adds the declaration shape to the governed-SDD task
blueprint and validates its syntax during `meridian execution preflight`.
It must not make every task run an interactive host probe.

For `NOT_APPLICABLE`, preflight requires the classification and non-empty
rationale. For `REQUIRED`, it requires every table column, all three evidence
plan categories, and a fallback for every profile. `ready-check` additionally
rejects an `enforced` completion claim lacking a named completion-evidence
entry for that profile. These checks validate durable declarations, not the
truth of a human observation; review remains responsible for comparing the
record with its cited evidence.

This boundary is deliberately smaller than automatic source classification or
host-runtime automation. A future enhancement may warn when an expected code
surface names a known host asset while the task says `NOT_APPLICABLE`, but it
must not block on heuristic inference.

## Current evidence reconciliation

| Profile and capability | Current state | Scope boundary |
|---|---|---|
| Claude Code 2.1.278 direct-plugin session, native `Read` guard | `enforced` | The direct `--plugin-dir` probe is evidence only for this invocation; marketplace installation and other runtimes are `unverified`. |
| Codex CLI 0.155.1 trusted project session, command approval rules | `enforced` | The verified profile requires trusted project rules and one shell command per invocation; approval does not grant sandbox access. |
| Codex trusted Palimpsest project session, read guard for project files | `enforced` | A 2,520-line project file was denied before execution. |
| Codex trusted Palimpsest project session, read guard for absolute external paths | `enforced` | `cat /private/tmp/meridian-read-guard-probe.txt > /dev/null` was denied before execution at 401 effective lines. Other Codex versions and plugin sessions remain `unverified`. |
| Codex plugin session | `unverified` | No plugin-layer hook or trust probe has been recorded. |
| Host-neutral CLI bootstrap | `unverified` | The Codex hook PATH was observed, but authority, upgrade, and adoption commands have not each been tested from every claimed profile. |

The implementation must update the open-evidence table in
`docs/HOST_CAPABILITY_CONTRACT.md` from this ledger only when the cited probe
is recorded. It must not collapse profile-qualified evidence into generic
“Claude” or “Codex” support.

## Bounded follow-ups

The design requires two implementation tasks, to be created only after this
design is accepted:

1. **Host-impact declaration distribution.** Update the governed-SDD task
   blueprint, the relevant routed implementation guidance, capability marker,
   migration, generated baseline, and tests that assert the managed template
   shape. Preserve existing consumer task records until their next material
   re-scope; do not rewrite historical tasks.
2. **Host-impact lifecycle validation.** Add parser and decision-table tests,
   then enforce the declaration shape in `meridian execution preflight` and
   `ready-check`. Cover `NOT_APPLICABLE`, malformed `REQUIRED`, an
   `enforced` claim missing completion evidence, and an intentionally retained
   `unverified` profile.

Neither follow-up makes a host probe automatic or treats a passing repository
test as host activation evidence.

## Out of scope

This design does not alter Claude or Codex hooks, expand read parsing, add a
Codex `UserPromptSubmit` equivalent, establish marketplace support, or change
Lean Delivery task records. It does not make host support a prerequisite for
ordinary product work.
