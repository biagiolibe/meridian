# ADR: Cardine 1.0

Status: Proposed

*Drafted on 2026-10-17 from the Cardine 1.0 design review. Decided by the
developer on 2026-10-17: the project console stays in 1.0; the context budget
keeps only an automatic limit on failed validation attempts; only open work is
converted from Meridian; the field trial has an exit criterion; trademark
registration is deferred until after 1.0. Still open: the single workflow
model, PyPI distribution, task state only in JSON, and a new repository instead
of a rename. The [open decisions](#open-decisions) section lists them.*

## Context

Meridian is a delivery workflow for AI coding agents. It has one known user,
the maintainer, with two Governed SDD projects (consumer project A and
consumer project B) and Meridian itself on Lean Delivery.
Over the 14 days to 2026-10-17 the repository had 3 unique visitors, 0 stars,
0 forks, and 0 release asset downloads; its 676 "unique" clones come from CI,
plugin refreshes, and crawlers.

The name does not work:

- About 9,800 GitHub repositories are named `meridian`, several with thousands
  of stars, and a search for this project does not return it.
- Other agent tools already use the name: `haowjy/meridian-cli` ships a
  `meridian` command for LLM work, and `meridianlabs-ai/agents` publishes Claude
  Code workflows.

The code and process have also grown past what one maintainer can keep sharp:

- `scripts/meridian.py` has 13,050 lines and 357 functions;
  `tests/test_meridian_cli.py` has 9,565 lines.
- 72 argument subparsers, about 60 public commands, most of them Stable.
- 69 migrations, `release-baselines/`, and more than 400 code references to
  legacy, compatibility, or migration paths.
- Two parallel workflows. Governed SDD installs 24 files and about 21,000 words
  into a project, Lean Delivery 10 files and about 7,000 words, and four skills
  cover two workflows on two hosts.
- Task status lives in five places: the task record, `tasks/QUEUE.md`,
  `PROJECT_PLAN.md`, `.meridian/tasks/<TASK-ID>.json`, and the handoff.
- The lifecycle needs about ten commands per task, with two `--project`
  conventions. Tasks 218–220 and 227–230 all fixed stops that this shape
  causes.

The name `cardine` was checked on 2026-10-17. It is free on PyPI, npm,
crates.io, RubyGems, Homebrew, Debian, and Docker Hub, and no system command
uses it. No US trademark registration exists for `CARDINE`. The EU and Italian
registers were not checked automatically. Two service businesses use the name
(`cardine.ai`, an AI consultancy in the US, and `cardine.dev`, a software
agency in Brazil). The GitHub account `cardine` is taken, so the repository
will be `biagiolibe/cardine`.

The name keeps Meridian's image. *Cardine* is Italian for hinge and for a
founding principle. It shares its root with the Roman *cardo maximus*, the
north–south street of a city, which is the city's meridian. The logo is an
axis between two arcs, which is a hinge.

## Decision

### 1. Cardine is a new product, released as 1.0.0

Cardine starts at `1.0.0` in a new repository, `biagiolibe/cardine`. It
imports the code of Meridian 1.4.0 in its first commit and states that origin.
It carries no Meridian history and no Meridian tags. Meridian 1.4.0 is the last
Meridian release. After Cardine 1.0.0 the Meridian repository is archived with
a README notice that points to Cardine.

There are no `meridian` aliases, no deprecation period, and no migration
chain, because no external adopter exists. The stability promise restarts at
Cardine 1.0.0, under the rules of `docs/ADR_PUBLIC_SURFACE_AND_STABILITY.md`.

### 2. Positioning

Cardine is the delivery discipline for AI coding agents. Every task lands on
`main` validated, integrated, and reversible, or it stops with a reason and the
exact command to resume.

The 2026 tool market covers two of three phases.

| Category | Examples | Leaves uncovered |
| --- | --- | --- |
| Specification frameworks | GitHub Spec Kit, Kiro, OpenSpec, BMAD-METHOD | No enforcement gate or verification in Spec Kit. None handles Git isolation and integration. |
| Agent orchestrators | Conductor, Composio Agent Orchestrator, Crystal, Claude Squad, Vibe Kanban | No automatic validation before merge, no stop rules. At most a human approval. |
| Host features | Claude Code, Codex, Cursor | Primitives such as worktrees, hooks, and permissions, with no task contract or lifecycle. |

Cardine adds five things:

- a verifiable task contract;
- mechanical gates with registered stop codes;
- a protected `main` with candidate validation and denied destructive actions;
- local, host-neutral operation with no service;
- reliable unattended runs.

Cardine complements the other tools. A Spec Kit specification can become a
task contract, and an orchestrator can run Cardine inside each worktree. README
line: *Specs say what to build. Orchestrators run the agents. Cardine makes
sure what lands on main is right.*

### 3. One workflow, assurances chosen per task

Cardine has one lifecycle and one template set. The assurances that are
exclusive to Governed SDD today become task options, and the project sets their
defaults:

- `review: required` or `review: not_required`;
- required `Authority` and `Expected code surface` fields;
- the `spike` class.

Task states are `queued`, `in_progress`, `in_review` (only when review is
required), `done`, and `cancelled`. One skill exists per host.

Consumer project A already chooses review per task: 34 of its 342 task
records are `Review: NOT_REQUIRED`. A Lean project, for example Meridian itself,
cannot require review for one risky task today. Under this decision it can.

Every Governed SDD feature the two consumer projects use maps to Cardine 1.0.
Counts are task records on 2026-10-17, as consumer project A / consumer project B.

| Governed SDD feature | Use today | Cardine 1.0 |
| --- | --- | --- |
| Required review | 268 / 47 tasks | Project default `review: required` |
| Review not required, per task | 34 / 0 tasks | `review: not_required` on the task |
| Verdict bound to the approved commit | 167 / 24 review records | Unchanged, in the task's state file |
| Changes requested and a new attempt | yes | `cardine review` with changes requested, then `cardine run` |
| Exploratory tasks with `ANSWERED` or `INCONCLUSIVE` | 41 / 3 tasks | Class `spike` with the same outcomes |
| `Authority` citing ADRs | 282 / 46 tasks | Contract field, required by project default |
| `Expected code surface` | 261 / 43 tasks | Contract field, required by project default |
| ADR log | 139 / 20 ADRs | Unchanged; `cardine adr list` and `cardine adr show` |
| Blocking dependencies | yes | Blocking for every task |
| Milestone task identity | yes | Project option |
| Execution evidence | yes | Recorded by `cardine run` |
| Context budget counters | consumer project A | Replaced by the validation retry limit (decision 5) |

### 4. Task state only in its JSON file

`.meridian/tasks/<TASK-ID>.json` becomes `.cardine/tasks/<TASK-ID>.json`. It
remains the only source of truth for status, transitions, and review verdicts,
as `docs/ADR_MACHINE_TASK_STATE.md` decided. It is validated by a schema and
written only by the CLI. `cardine task new` creates it with the task, so it
cannot be missing.

Cardine removes the duplicates that coexist with it in Meridian:

- the `Status` field in the Markdown record;
- the move to `tasks/done/` as a status signal;
- hand-maintained queue and plan status.

`cardine status` generates the queue, and the plan's status lines are
generated too. Keeping state in a front matter block of the Markdown record was
considered and rejected. It would put status back in a file that people and
agents edit by hand, which is the failure the machine-state ADR fixed.

### 5. Context budget: one automatic limit

The usage data, as of 2026-10-17:

- Consumer project A recorded 261 budget spends across 83 tasks. No command
  emitted `BUDGET_EXHAUSTED` in that time. Two exhaustion stops were declared
  by agents without a command. One of them was the false exhaustion of
  issue #15.
- Consumer project B recorded 6 spends.
- Of the four counters, only diagnostic attempts approached their caps.

In Cardine 1.0:

- **Kept:** task-first reading rules and the read guard for large files.
- **New:** `cardine run` counts consecutive failed validation runs of the task
  itself. After N failures it stops with a registered code and a summary of
  the failures. N defaults to 3 and is configurable per project and per task.
  The counter lives in the task's state file and is bound to the attempt. The
  agent records nothing.
- **Removed:**
  - the self-reported counters: evidence captures, context expansions, and
    investigation scope;
  - the ledger in the Git common directory;
  - `budget show` and `budget spend`;
  - the `Budget usage` handoff line.

### 6. One lifecycle entry point

`cardine run <TASK-ID>` is the only lifecycle command an agent needs. Each call
reads the task state, performs the next possible step, and prints JSON with the
outcome and the next action. Its steps are:

1. contract check;
2. worktree preparation;
3. implementation;
4. validation;
5. review, when required;
6. candidate validation of `main` plus the task;
7. merge, push, and cleanup.

It is rerun after every step and every stop. It resolves the primary checkout
and the task worktree itself and works from any directory. It returns only
commands that run unchanged. These rules close the classes of stops fixed in
tasks 219, 227, 229, and 230. Single-step commands remain Internal, for
diagnosis and manual recovery.

### 7. Scope of 1.0

| Area | Decision |
| --- | --- |
| Migrations and release baselines | Removed. The migration mechanism stays for future releases. |
| `adopt` from historical versions | Removed. `adopt` handles projects without Cardine and Meridian projects (decision 10). |
| Maintainer-only commands (`profile`, `generate-*`, `report flow`, evaluations) | Moved out of the user CLI into development scripts. |
| Duplicate implementations | One each, in Python. Hooks are no longer written in both shell and Python. One entry-router generator. `release.py` and `prepare_release.py` merge. |
| Project console | Stays in 1.0, Experimental, rebuilt on the single task state and the `cardine run` engine. |
| Documentation | User guide, compact agent reference, README with the positioning. Meridian's design history and task records stay in the archived repository. |

Unchanged, because they are the product's value:

- registered stops with exact resume commands;
- denied destructive actions;
- one worktree and one writer per task;
- candidate validation before integration;
- fragment-based releases with a version-kind check;
- `setup` that always shows a diff before applying.

### 8. Package architecture

Cardine is a Python package. Its modules are:

| Module | Responsibility |
| --- | --- |
| `cardine.cli` | Argument parsing, JSON and text output, exit codes |
| `cardine.tasks` | Contract, states, transitions, dependencies, identity |
| `cardine.lifecycle` | The `cardine run` engine |
| `cardine.worktree` | Preparation, checks, cleanup, canonical paths |
| `cardine.integration` | Candidate, validation, merge, push |
| `cardine.review` | Independent review and verdicts |
| `cardine.stops` | Stop-code registry and resume commands |
| `cardine.hosts` | Setup and doctor for Claude Code and Codex: skills, rules, hooks |
| `cardine.templates` | Project files, markers, upgrade |
| `cardine.console` | Project console over the task state and `cardine run` |
| `cardine.release` | Release tooling, for Cardine development only |

Tests mirror the modules. No source or test file exceeds 1,500 lines.

The Stable surface of 1.0 is:

- `cardine init`, `setup`, `doctor`;
- `cardine task new`, `task list`, `task show`;
- `cardine run`, `status`, `review`, `cancel`, `abort`;
- `cardine upgrade`, `self-update`;
- `cardine adr list`, `adr show`.

`cardine hook …` is Host-facing. `cardine console` is Experimental. The
single-step lifecycle commands are Internal.

### 9. Distribution

Cardine is published on PyPI, with `pyproject.toml`, a registered `cardine`
command, and `requires-python >= 3.12`. It installs with
`uv tool install cardine` or `pipx install cardine`.

This removes the release checkout, `MERIDIAN_ROOT`, `PATH` edits, the wrapper's
Python version guard, and the exact-tag requirement. Templates and skills ship
as package data. Updates use `uv tool upgrade cardine`, then `cardine upgrade`
in each project.

The Claude Code plugin keeps skills and slash commands and calls the installed
CLI. `cardine doctor` checks that the plugin and the CLI versions match.
Cardine developers use `uv tool install --editable .` from a clone.

### 10. Transition from Meridian

1. **Release Meridian 1.4.0.** Integrate tasks 227–230 and publish 1.4.0. Its
   notes announce that Meridian will be archived.
2. **Create `biagiolibe/cardine`.** Import the code and publish a `0.0.1`
   placeholder on PyPI to reserve the name.
3. **Develop toward 0.9** with the work items below.
4. **Convert open work only.** `cardine adopt` converts the open tasks, the ADR
   log, and the project configuration: default assurances, validation commands,
   and task identity. Closed tasks and review records stay in place as an
   archive that Cardine ignores. Conversion runs on copies first, then on the
   originals.
5. **Field trial with an exit criterion.** Cardine 1.0.0 is released only when,
   on 0.9, at least one real task of each case has landed on `main` in consumer
   project A or consumer project B:
   - required review with one round of requested changes;
   - no review;
   - a spike;
   - `Authority` citing an ADR, with a declared code surface;
   - a stop followed by a resume with `cardine run`.

   A case that does not work as it does today becomes a task and blocks 1.0.
6. **Release Cardine 1.0.0** on GitHub and PyPI.
7. **Archive Meridian.** Add a README notice, make the repository read-only, and
   remove the Meridian plugin from its marketplace.

On the maintainer's machine:

- remove the Meridian plugin, `~/.local/share/meridian`, the `MERIDIAN_ROOT`
  and `PATH` lines, and the Meridian blocks under `~/.codex`;
- install Cardine with `uv tool install cardine`, then run
  `cardine setup --apply`.

Projects stay on Meridian 1.4.x until their conversion. 1.4.x receives fixes
only for blocking defects.

## Work items to 0.9

Most items are one or more tasks of 2–3 hours. Items 3 and 4 are mechanical
and leave behavior unchanged; simplification starts after them.

1. Accept this ADR.
2. Repository bootstrap: `pyproject.toml`, package skeleton, CI, code import.
3. Split `meridian.py` and its tests into the modules of decision 8, with the
   existing suite green.
4. Rename identifiers: command, environment variables, `.cardine/`, markers,
   Git-internal files, worktree root.
5. Remove historical compatibility: migrations, baselines, budget counters,
   maintainer commands, duplicates.
6. Single workflow: one template set, task contract fields, states, review
   option, `spike` class.
7. Single source of truth: state in the task JSON, generated queue and plan
   status.
8. `cardine run` engine: next step, resume, directory independence, runnable
   commands, validation retry limit. Rebuild the console on this engine.
9. Hosts: setup and doctor for Claude Code and Codex, two skills, user-level
   hooks.
10. Meridian conversion: open tasks, ADRs, configuration.
11. Documentation: README positioning, quick start, agent reference.
12. Release: GitHub and PyPI publication from one script.
13. Release 0.9, run the field trial, release 1.0.0.

## Consequences

- One product name with no collision in package registries or system
  commands.
- One workflow and one skill per host. A project chooses its default
  assurances, and a task can raise or lower them.
- Fewer Stable commands: about 15 instead of about 60 public commands.
- No historical migration code to maintain.
- Installation is one command, independent of the host.
- For several weeks Meridian receives only blocking fixes.
- Cardine's Git history starts at the import commit. Meridian's history stays
  readable in its archived repository.

## Risks

| Risk | Mitigation |
| --- | --- |
| Scope grows during the rewrite ("second system") | This ADR is the 1.0 scope; new ideas wait until after 1.0. |
| Behavior is lost while the code is split | Items 3 and 4 are mechanical, with the existing suite of more than 1,000 tests unchanged. |
| The single workflow misses a Governed SDD use | The parity table in decision 3 and the field-trial exit criterion in decision 10. |
| The `cardine` PyPI name is taken meanwhile | Publish a `0.0.1` placeholder first. |
| A trademark conflict with a business using the name | Registration is deferred until after 1.0. EU and Italian registers must be checked before registration. |

## Rejected alternatives

- **Rename the existing repository and keep version numbers.** Tags `v1.0.0`
  to `v1.4.0` already exist, so Cardine 1.0.0 would collide with Meridian
  1.0.0. A rename also carries the rewritten history and the open GitHub
  Support request.
- **Cardine 2.0.0 with deprecated `meridian` aliases, removed in 3.0.0.** This
  follows the stability rules for adopters who do not exist, at the cost of
  dual code paths for a full major cycle.
- **Keep two parallel workflows.** Keeps every cost listed in the context.
- **Lean Delivery only.** Drops independent review, which 268 tasks in one
  consumer project used.
- **Task state in Markdown front matter.** Rejected under decision 4.
- **Keep the context budget as it is.** The usage data in decision 5 shows cost
  without a single command-backed stop.

## Open decisions

- Single workflow with per-task assurances (decision 3).
- PyPI distribution instead of a Git checkout (decision 9).
- Task state only in its JSON file (decision 4).
- New repository instead of renaming `biagiolibe/meridian` (decision 1).

## Out of scope

- Trademark registration, deferred until after 1.0.
- Hosts other than Claude Code and Codex.
- Parallel orchestration of several agents. Cardine runs inside each worktree.
- Conversion of closed Meridian tasks and review records.
