# Closure Initiative Report

Status snapshot: 2026-10-02. Written for an agent that did not take part in the
sessions described. It explains what was done, why, what is decided, what is
open, and how to continue. It records no decision that is not already in a task,
a design, or a commit; where something is a judgment or could not be verified, it
is labelled.

Evidence labels used throughout:

- **Observed**: seen in the repository, a command, or its output during the work.
- **Reported**: stated by the developer or by an agent host (for example Codex)
  and not reproduced here.
- **Unverified**: inferred or remembered and not checked.

## 1. Goal and vocabulary

The developer's goal: an assigned task should run to completion by itself,
meaning implementation, validation, completion records, integration into `main`,
the required push of `main`, and cleanup, with no avoidable stop. Closure kept
stopping "for the most varied reasons", and the developer had to repair or resume
tasks by hand.

Terms:

- **Meridian**: this repository, a framework of workflow templates, a CLI
  (`bin/meridian`), migrations, and release tooling for agent-driven development.
- **Lean Delivery / Governed SDD**: the two workflow modes. This repository is
  locked to Lean Delivery by `PROJECT_WORKFLOW.md`. The adopter project
  `palimpsest` uses Governed SDD (framework baseline `1.1.49` when last read).
- **Task lifecycle**: `[ ]` to `[/]` to `[x]`, with the task file archived to
  `tasks/done/`, a handoff in `tasks/handoffs/`, and rows in `tasks/QUEUE.md`
  and `PROJECT_PLAN.md`.
- **Task worktree**: one branch and one linked worktree per task, one writer at a
  time. Commands: `meridian worktree prepare|check|integrate stage|finalize|abort|cleanup`.
  Lifecycle commands never run project-controlled commands (tests, hooks).
- **Agents**: Claude Code and Codex. Both run inside sandboxes with host limits.
- **Console**: `meridian console`, a read-only terminal view of task state that
  can launch an agent in iTerm2.

## 2. Work done, by theme

### 2.1 Worktree root and Codex permissions (Tasks 083, 085, 092)

- Codex kept asking for permission to write in task worktrees. **Observed**: the
  user Codex config had no permission profile (`meridian codex configure --check`
  reported `permission-model: unconfigured`), and the worktrees lived outside the
  project, where the bounded `:workspace` sandbox does not reach.
- **Observed**: three different worktree roots were in use: `.claude/worktrees`
  inside palimpsest, `~/.codex/meridian-worktrees`, and `~/.meridian/worktrees`.
  Task 083 unified resolution (explicit option, `MERIDIAN_WORKTREE_ROOT`, a
  versioned user config, then `~/.meridian/worktrees`) and added
  `meridian setup --check|--apply`; Task 085 made setup repair or replace the
  Codex profile root.
- The profile now exists in the user's Codex config for `~/.meridian/worktrees`
  (applied by the developer, **observed** in the file). I first suggested the
  wrong command (`codex configure --apply`) because I had not read the CLI help;
  `meridian setup` is the intended entry point.
- Task 092 added Codex skill links (`~/.agents/skills`) to `setup` and two
  read-only checks (`skill-links`, `MERIDIAN_ROOT`) to `meridian codex doctor`.
  Cloning at the tag and editing the shell profile deliberately stay manual.
- **Noted, not tasked** (the developer declined a task): `setup --check` warns
  "stale Codex skill copy" for a symlink that points at the live skill (a false
  positive), and prints `changes: - none` next to a real planned change.

### 2.2 Unprepared worktrees in a Governed project (Task 097)

- Three palimpsest tasks (M37-CAUSE-001, F1-FIGURE-001, F1-TREAT-001) stopped with
  `missing-state`, `wrong-worktree`, `unregistered-worktree` from
  `meridian worktree check`. **Observed** each time: no branch, no worktree.
- Cause (**observed** in the templates): Governed `IMPLEMENTATION.md` and
  `PROJECT_WORKFLOW.md` say the *coordinator* runs `prepare` and starts the worker
  in that directory. A manually typed `Proceed with <ID>` has no coordinator, so
  the worker stops, correctly by the rules. The Lean workflow already says the
  agent creates or selects the branch and worktree.
- My first hypothesis (the sandbox blocks `prepare`) was wrong: running `prepare`
  by hand worked.
- Decision (developer's choice, option 1): a manually typed `Proceed with` in
  Governed SDD makes the implementer run `prepare` for exactly that task ID, then
  `check`, then work only in the prepared worktree; `Review` and `Address review`
  never prepare. Shipped by Task 097 as a template-changing change.
- Not done (option 2): making the console prepare the worktree and start the
  agent inside it. Task 077 assumed "the directive prepares the worktree", which
  Task 097 makes true.

### 2.3 Console launch and review state (Tasks 077, 086, 087)

- The console launches an agent in iTerm2. Task 086 changed the tab to a
  horizontal split pane of the console's own session (session found through
  `ITERM_SESSION_ID`). A later fix rewrote the AppleScript after the split-session
  lookup was found invalid.
- For palimpsest, the console showed "Awaiting review of the task branch" and no
  `Review <ID>` directive. **Observed** cause: the review policy was read only
  from a `Review` queue column; palimpsest declares `Review: REQUIRED` in the task
  record header. Task 087 reads the record when the column is absent and makes
  `Next action` state why a directive is withheld.
- **Noted, not tasked**: the console groups lifecycle `done` (accepted, not yet
  integrated) under the same "Review" label as `ready_for_review`
  (`_state_label` in `scripts/project_console.py`). A task that is accepted on its
  branch but not in `main` therefore looks "in review".

### 2.4 Distribution, releases, and the plugin migration (Tasks 089 to 098, 116)

- Adopter updates are manual by design (`docs/DISTRIBUTION_AND_UPDATE_DESIGN.md`,
  "No channel moves an adopter automatically"). **Observed**: versions 1.1.51 to
  1.1.53 existed in the ledger but were never tagged; only `v1.1.49` and
  `v1.1.50` were published. Release `1.2.0` (Task 089) bundles them and is
  CLI-only for the ledger.
- Claude Code plugin: the marketplace was renamed `meridian-local` to `meridian`.
  The developer migrated; **observed** afterwards: `meridian@meridian` 1.2.0,
  marketplace pinned to `v1.2.0`, `enabledPlugins` rewritten by the install,
  `bin/meridian` present in the cache. Task 091 recorded this evidence in
  `docs/HOST_CAPABILITY_CONTRACT.md`. **Unverified**: `${CLAUDE_PLUGIN_ROOT}`
  expansion in a live session and unpinned `marketplace update`. Caution: the
  user-level Claude settings contained a hook with a hardcoded path to this
  repository's `hooks/queue-briefing.sh`, so the per-prompt queue briefing cannot
  prove the plugin hook ran; the read-guard hook (plugin only) is the clean test.
- A release command was built: Task 093 `release.py prepare` (local, derives the
  release kind from the ledger and migrations), Task 094 `release.py publish`
  (typed `--confirm v<version>`, then push, tag, wait), Task 095 fixed `prepare`
  usage and the unbounded `--dry-run` output.
- First real publish (`v1.2.1`): the workflow lookup ran before GitHub created the
  run and reported failure although `main`, the tag, and the Release were fine
  (**reported** by the developer, then **observed**: run succeeded, Release
  `Latest`). Task 096 (open) adds polling and a read-only `verify`.
- Design gap found while writing Task 097 (**observed** in code): a
  template-changing release cannot use `prepare`/`publish`, because
  `check_repository.py` forbids a migration ahead of `VERSION` (so the migration
  task must bump version, ledger, and changelog), while `prepare` needs a greater
  version and `publish` required a commit made by `prepare`. Task 098 made
  `publish` validate repository state instead.
- State now: `VERSION` is `1.2.3`; the latest published release is `v1.2.1`.
  `1.2.2` and `1.2.3` are in the repository and untagged; `1.2.3` is
  template-changing (migration `057-self-referential-handoff-commits`, Task 088).

### 2.5 Test failure inside the agent sandbox (Task 099)

- `AgentLaunchTest.test_split_payload_compiles_as_applescript` failed in Codex and
  blocked closure of several tasks (handoffs 086, 094, 095, 098 mention it). It
  passed outside the sandbox (**observed**: 422 and later 446 tests OK in the
  developer's terminal and in my local runs).
- First fix design: skip the test when a trivial probe (`osacompile -e 'return 1'`)
  fails. **Wrong**: Codex then reported the probe passing and the payload failing
  with `Expected "then", etc. but found property. (-2741)`.
- Root cause (**observed**, reproduced): in the sandbox `osacompile` works for
  core AppleScript but cannot resolve the iTerm2 scripting dictionary. Compiling
  the same payload against an app with no dictionary gives the identical error.
  The payload is valid.
- Corrected criterion, given to Codex as an explicit amendment: the probe is
  `tell application "iTerm2" to get unique id of current session of current tab of
  current window`; if it fails, skip with a named reason; if it passes and the
  payload fails, fail. Task 099 is done. Accepted trade-off: where the probe
  fails, a payload syntax error is not caught by this test.

## 3. The closure diagnosis and design (Task 100)

When the developer reported that closure stops repeatedly, I surveyed the
repository instead of guessing.

- **Observed**: 317 commits since 2026-09-20; 11 "handoff repair" commits
  (`refresh ... after rebase`, `restore ... base commit`, `use full commit ids`,
  `correct ... handoff`) affecting at least tasks 067, 068, and 087; `osacompile`
  in four handoffs; Task 063's handoff records `Integration decision: BLOCKED`
  because `main` advanced with a commit that added Task 064 and edited
  `PROJECT_PLAN.md` and `tasks/QUEUE.md`, and the merge conflicted.
- **Key finding (observed)**: `.codex/rules/meridian.rules` already allows
  `git push` and `meridian worktree integrate stage|finalize|abort`, so the
  frequent stop "the agent waits for authorization before integrating" is not a
  command-permission gap. No workflow sentence states that `Proceed with <ID>`
  authorizes integration, the push of `main`, and cleanup. Agent hosts default to
  pushing only when asked, so an omission makes them stop. This is **reported
  behavior**, not tested.
- Agents may not run `git rebase`, `reset`, or `cherry-pick` (rules file), so a
  task cannot be rebased when `main` advances; the repair commits show the manual
  workaround.

`docs/TASK_CLOSURE_DESIGN.md` (Task 100, done) records the survey (S1 to S9) and
eight decisions: standing authorization with hard exclusions (tags, releases,
force-push, history rewrite, bypassing a required review); task branches stop
editing `QUEUE.md`, `QUEUE_ARCHIVE.md`, and `PROJECT_PLAN.md` (applied once at
integration); integration when `main` advanced by re-staging with the merge path
and recomputing facts; handoff facts collected by a command; one closure
procedure with named stops and idempotent resume; a named-skip validation policy;
review gates; rollout. Follow-ups are Tasks 101 to 110.

## 4. Blockers found while closing Task 101, and the response

Task 101 (`meridian worktree closure-status`) had working code and passing
targeted tests, then stopped for two reasons the design did not cover.

1. **Validation exceeds the host command limit** (**reported**): the full suite
   (`python3 -m unittest discover -s tests`, 446 tests, about 90 seconds here)
   was interrupted after about 30 seconds without an exit status. The Lean rules
   forbid closing without that evidence, so the task stayed `[/]`. The 30 second
   figure was not measured here.
2. **`integrate stage` blocked the archive rename** (**reported**, cause located in
   code): `stage_task_integration` accepts only five paths changed after
   validation (task path, queue, handoff, review, plan). Archiving a task renames
   its record into `tasks/done/`, which that set did not allow.

Response (Tasks 111 to 116):

- **111** (done, integrated): `stage` accepts the archive only as an exact 100%
  rename derived from the task identity, rejects other deletions and additions,
  stays read-only until the lease, and names offending paths. It is a bridge
  until Tasks 103 and 104 remove queue, plan, and archive edits from task
  branches. A task that archives its own record cannot use the unfixed `stage`;
  111 and 101 were closed with a recorded one-time bootstrap (archive applied in a
  record-only commit on `main`).
- **112**: sharded test runner (`--shard I/N`, prints `total` and `digest`).
- **113**: `validation-evidence` v1 record, states `VALIDATION_RUNNING`,
  `UNAVAILABLE`, `FAILED`, `PASSED`, levels `T1_CI`, `T2_SHARDED`,
  `T3_ATTESTED`, and a read-only verifier (`meridian validation check`) that runs
  no command and writes nothing. It is an attestation bound to a commit and tree,
  not an unforgeable proof.
- **114**: CI on `task-*` branches (today `validate.yml` runs only on pull request
  and `main`) and a script that turns the CI result for an exact commit into a
  `T1_CI` record. Pushing a task branch is not covered by the authorization of
  Decision 1; Task 115 must decide it.
- **115**: addendum to `docs/TASK_CLOSURE_DESIGN.md` recording the validation and
  stage decisions and aligning dependencies (108, 109, 110 on 113; 102 on 111).
- **116**: per-task changelog fragments (`changelog.d/<TASK-ID>.md`), assembled by
  `release.py prepare`, replacing edits to the shared `## [Unreleased]`.

## 5. Literature comparison

From memory, **unverified** citations: trunk-based development and continuous
integration (Fowler; Hammant; DORA, *Accelerate*); the merge-queue idea (the "not
rocket science rule" behind Bors for Rust, Zuul gating, GitHub merge queue, GitLab
merge trains); Uber SubmitQueue (EuroSys 2019); Google's single repository (CACM
2016); changelog fragments (towncrier, changesets).

Target architecture for parallel work: one serialized integrator that is the only
writer of shared files; per-task records with generated views; evidence bound to
content (tree hash) with CI as the default authority; branch updates by the queue
using merge, with a conflict returned to the author with a reason; a standing,
explicit authorization; closure as a resumable state machine with named stops.

Where Meridian stands (judgment): the hardest part exists (lease, no-commit merge
candidate, validation of the candidate, finalize). The structural gaps are the
shared files still edited by task branches (queue, plan, archive: Tasks 103, 104;
changelog: Task 116), CI not being the validation authority (Task 114), evidence
bound to commits rather than trees in `stage` (Task 113), and the unwritten
authorization (Tasks 106, 109, 110). Speculative parallel validation is not
needed at this scale.

## 6. State at the time of writing

- Done: 097, 098, 099, 100, 101, 102, 111 (and the earlier release and setup
  tasks above). 102 added the evidence command and made `stage` recompute
  main-advance facts.
- Open: 096; 090 (1.0.0 projects reaching the current release in one step, found
  by Task 068); 103 to 110; 112 to 116.
- Intended execution order (Phase 45 text in `tasks/QUEUE.md`): 111, 101, 102,
  116, 112, 113, 114, 115, then 103, 104, 108, 105, 106, 107, 109, 110. 116 was
  added after 111 and 102 started, so it runs before 112 to 114.
- Leftover linked worktrees for finished tasks (067, 094, 099) are still
  registered; `meridian worktree cleanup` was not run for them.
- The developer reviewed a cost assessment of this queue (about 20 process tasks,
  roughly 35 to 40 hours of **unmeasured** estimates, each paying the closure
  tax it aims to remove) and chose to keep the queue as is. My unadopted
  recommendation, kept for reference: ship the authorization sentence and the CI
  trigger first, measure closure interventions over the next five tasks, and
  defer 112, 113, 105, 107 unless the numbers show the problems persist.

## 7. How to continue

- Read `PROJECT_WORKFLOW.md`, `LANGUAGE_POLICY.md` (conversation in Italian,
  repository text in English), `docs/WORKTREE_LIFECYCLE.md`, and
  `docs/TASK_CLOSURE_DESIGN.md`. Work only on the task the developer assigns.
- Do not commit new task files to `main` while another task's branch is open: the
  shared governance files (`QUEUE.md`, `PLAN`, `CHANGELOG.md`) are the observed
  conflict source until Tasks 103, 104, and 116 land. This is a hypothesis for the
  causal weight and an observed example in Task 063.
- A task that archives its own record needed the Task 111 fix; confirm it is in
  `main` before relying on `stage` for archival.
- When the suite cannot finish in the agent host, do not mark a task complete from
  partial output. The accepted routes, in order, are CI for the exact commit,
  a complete sharded run, and a dated developer attestation labelled as such.
- Releases: CLI-only releases go through `release.py prepare` then `publish`;
  a template-changing release has its version, ledger, and changelog bumped by the
  migration task and then goes to `publish`. Pushing a tag publishes to adopters;
  it is always the developer's action.
- Known unverified items: the host command limit, whether a detached process
  survives it, `${CLAUDE_PLUGIN_ROOT}` expansion in a live session, unpinned
  marketplace update, and the literature citations above.

## 8. Index of task files

`tasks/done/` and `tasks/` hold each task; the handoffs are in `tasks/handoffs/`.
Key files: 083, 085, 092 (setup, Codex); 097 (Governed `Proceed` prepares); 077,
086, 087 (console); 089 to 098 and 116 (releases and changelog); 099 (sandbox
test); 100 and 101 to 115 (closure design and its follow-ups).
