# Task 063 — Implement the task-identity declaration and resolver

> **ID**: `063`
> **Category**: Architecture / Compatibility
> **Priority**: 🔴 P1
> **Estimate**: ~6–8h
> **Assigned to**: unassigned
> **Session**: unassigned

## 🎯 Objective

Implement Task 039's project-selectable task-identity policy as one
host-neutral resolver shared by Meridian's task, location, handoff, review,
and budget consumers.

Projects with no declaration remain backwards-compatible `opaque` projects.
Projects that explicitly select `milestone` mode can use canonical IDs such as
`M30-INSPECT-001`, retain known historical opaque IDs, and receive deterministic
filesystem and Git-safe derivations without introducing a second source of
truth for task semantics.

## 📋 Acceptance Criteria

- [ ] Meridian reads the optional project-owned
      `.meridian/task-identity.json` declaration. Absence is exactly equivalent
      to `{"version": 1, "mode": "opaque"}`; version `1` accepts only `mode`
      values `opaque` and `milestone`, and malformed JSON, unsupported versions,
      or unknown properties fail closed.
- [ ] One `resolve_task_identity(project_root, supplied_id, intent)` boundary
      returns the policy version, mode, identity kind, canonical ID, branch
      name, artifact stem, optional semantic tuple, resolved task/queue/handoff/
      review paths, and attempt-qualified budget key defined by
      `docs/TASK_IDENTITY_POLICY.md`.
- [ ] `intent` distinguishes `existing` from `new`. Resolution consults the
      canonical task and queue authorities, accepts only unambiguous existing
      aliases, and rejects unknown, contradictory, or colliding identities
      without inferring status, dependencies, scope, priority, review policy,
      validation, or authority from the identifier.
- [ ] Opaque mode preserves every currently supported numeric alias and every
      unambiguous project-valid historical identifier. It does not introduce
      general case folding, reinterpret opaque tokens, or require existing
      projects to add a declaration.
- [ ] Milestone mode implements the exact canonical grammar
      `M<milestone>-<WORKSTREAM>-<ordinal>` from the design: positive milestone
      without a leading zero, uppercase ASCII workstream segments separated by
      `_`, and an ordinal from `001` through `999`. Lowercase command input may
      normalize to a canonical record; mixed-case authoritative records are
      invalid.
- [ ] In milestone mode, a new task must use the structured grammar. A known
      pre-existing non-matching task resolves as `legacy-opaque`, an existing
      matching task resolves as `structured`, and an unknown non-matching ID is
      rejected.
- [ ] Structured identities derive task filename, queue identity, lowercase
      branch/worktree-safe stem, handoff path, review path, semantic tuple, and
      budget key exactly as specified. Opaque and legacy-opaque identities use
      the same resolver with existing safe compatibility derivations.
- [ ] All derivations reject traversal, path separators, reserved or invalid
      Git-ref forms, case-fold collisions, unsafe filesystem components, and
      mismatched existing artifacts before returning a result.
- [ ] Project location resolution is performed once and remains independent
      from identity policy. Customized queue and task roots continue to use the
      canonical-locations extension rather than fields copied into the identity
      declaration.
- [ ] Existing task lookup, context, execution handoff/review lookup, and
      budget commands consume the shared resolver result rather than their own
      task-ID normalization. This task does not implement the Task 056 worktree
      lifecycle namespace or a second worktree-specific grammar.
- [ ] The read-only command
      `meridian task identity check <TASK-ID> --project <path> --format json`
      emits exactly one JSON success object and exits `0`; identity or policy
      failures emit no success object and exit `2`; usage errors exit `64`.
- [ ] The JSON result exposes the resolved scalar fields and paths required by
      the design. Tests compare those values with the same resolver values used
      by runtime consumers so diagnostics cannot drift from behavior.
- [ ] Managed Lean Delivery and Governed SDD guidance identifies
      `.meridian/task-identity.json` as the sole optional declaration and
      states that absence selects `opaque` mode. A versioned capability marker,
      migration, and release baseline deliver the managed pointer and schema
      support to existing and new adopters.
- [ ] The migration never creates `.meridian/task-identity.json`, opts a
      project into milestone mode, renames a task, rewrites a queue, or changes
      a consumer's project-owned location declarations.
- [ ] Deterministic tests cover absent and explicit opaque policy, milestone
      grammar and case normalization, historical legacy identities, numeric
      aliases, customized and nested task locations, ambiguous authorities,
      collisions, traversal, unsafe Git forms, malformed declarations,
      unsupported versions, and CLI output and exit codes.
- [ ] `python3 scripts/check_repository.py`,
      `python3 -m unittest discover -s tests -v`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `docs/TASK_IDENTITY_POLICY.md` | Authoritative schema, grammar, compatibility rules, resolver contract, and CLI behavior. |
| `scripts/meridian.py` | Declaration parser, shared resolver, location integration, consumers, and diagnostic command. |
| `tests/test_meridian_cli.py` | Resolver, consumer, migration, CLI JSON, and exit-code coverage. |
| `tests/test_task_worktree_isolation.py` | Existing path and collision behavior that must remain compatible; Task 056 owns lifecycle changes. |
| `templates/workflows/lean-delivery/` | Managed pointer and default-opaque guidance for Lean adopters. |
| `templates/workflows/governed-sdd/` | Managed pointer and default-opaque guidance for Governed adopters. |
| `migrations/`, `baselines/` | Versioned delivery without creating a project-owned declaration. |
| `tasks/056-add-bounded-worktree-lifecycle-commands.md` | Downstream consumer of the completed resolver contract. |

## 🧩 Technical Context

Task 039 selected a closed, project-owned policy file and a single resolver
contract. The current CLI instead relies on numeric-only normalization in
`canonical_task_id()` for worktree paths while task, execution, context, and
budget operations resolve identifiers through partially separate paths. That
split prevents consumers such as Palimpsest from using their existing
milestone IDs consistently and would let Task 056 accidentally preserve a
host-era parser.

The identity resolver determines identity and safe mechanical derivations
only. Task records, queues, and workflow documents remain authoritative for
all lifecycle and semantic facts.

## 🔨 Suggested Implementation

1. Introduce typed policy and resolved-identity representations plus a strict
   parser for the optional declaration.
2. Centralize canonical project-location and authority lookup, then implement
   opaque, structured, and legacy-opaque resolution with collision and safety
   checks.
3. Route the existing non-worktree consumers through the resolver and add the
   read-only JSON diagnostic.
4. Add adversarial resolver and CLI fixtures before migrating managed workflow
   guidance and baselines.
5. Leave Task 056 to replace the public worktree surface and prove that its
   deprecated Codex alias consumes this same resolver.

## ⚠️ Constraints and Considerations

- Do not infer task semantics from milestone, workstream, or ordinal tokens.
- Do not accept a user-defined regular expression, delimiter, case policy,
  registry, path, or taxonomy in the declaration.
- Do not silently fall back to opaque mode when a declaration exists but is
  invalid.
- Do not enumerate Git history to identify legacy tasks; current task and queue
  authorities are the compatibility evidence.
- Do not create a repository-wide hook or expand `meridian audit`; the explicit
  check and resolver-backed consumers are the bounded first-delivery gate.
- Do not implement Task 056's prepare, check, integrate, or cleanup transitions
  in this task.
- Repository artifacts are English-only.

## Host impact

Classification: REQUIRED

Policy outcome: task identity becomes a host-neutral Meridian invariant.
Claude Code, Codex, and direct terminal users resolve the same canonical task,
paths, branch spelling, and budget key; host permission systems do not alter
identity semantics.

| Profile | Before | Intended after | Activation preconditions | Fallback |
|---|---|---|---|---|
| Host-neutral Meridian CLI | numeric-only or consumer-specific normalization | one declaration-driven resolver | Valid project authorities and absent or valid version-1 declaration. | Exit `2` with a bounded identity diagnostic. |
| Codex project | worktree helper accepts only numeric task IDs | resolver is available for Task 056 to consume | Updated CLI and migrated workflow guidance. | Retain current lifecycle block until Task 056 lands. |
| Claude plugin project | workflow can name structured tasks but CLI consumers disagree | plugin instructions and CLI share the resolver contract | Updated plugin/framework and migrated workflow guidance. | Treat structured lifecycle as unavailable until Task 056 lands. |

## 🔗 Dependencies

- **Depends on**: 039
- **Blocks**: 056

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/063-implement-task-identity-resolver.md)"$'\n\nExecute this task in the current project.'
```
