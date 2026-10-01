# Contributing to Meridian

Thanks for helping improve Meridian.

## Scope

Meridian is a stack-agnostic workflow for agentic software development. Keep generic workflow assets free of product, language, framework, and hosting-specific rules. Project-specific architecture belongs in generated projects, not in this repository's templates.

## Language invariant

Meridian repository text is English-only. Keep documentation, source code, comments, identifiers, user-facing strings, tests, configuration text, and commit messages in English. The only configurable language is the agent-developer conversation language, persisted in generated projects through `LANGUAGE_POLICY.md`; an individual prompt in another language does not change it.

When changing this behavior, keep the base and governed-SDD language-policy templates identical. For a workflow-rule change, update the corresponding Codex and Claude Code instruction and skill assets for that mode.

## Migrations and capability markers

A migration that modifies framework-mandated prose already tracked as a
capability — not just adds a new managed file — must declare `capability`
and `capabilityVersion` in its migration record, wrap the affected text in
`<!-- MERIDIAN:BEGIN capability=<id> vN --> ... <!-- MERIDIAN:END -->`
markers if it doesn't already carry them, and describe the change in a
`delta` field scoped to what actually changed, not a from-scratch rewrite.
See [migrations/CAPABILITY_MARKERS.md](migrations/CAPABILITY_MARKERS.md) for
why: presence-only, phrase-based detection cannot tell a modified capability
from an unmodified one, and breaks on a project whose wording predates the
exact phrase or has diverged from the template. A migration that never
introduces or changes a capability (framework-CLI-only changes, for example)
does not need these fields. Do not add a migration merely to justify a version
bump: a release that changes only the CLI is a CLI-only release (see
[Release procedure](#release-procedure)) and ships no migration.

Retrofit markers into an older migration's content opportunistically, on its
next real change, rather than as a dedicated migration with no other
purpose — migrations 003, 004, and 005 do not carry markers yet for exactly
this reason.

## Before opening a change

1. Read the relevant template, command, hook, or skill end to end.
2. Keep a change focused on one behavior or document set.
3. Preserve parity between the Codex and Claude Code skills for the workflow mode being changed.
4. Do not change generated-project behavior accidentally while editing explanatory documentation.

## Validation

Run the repository checks before proposing a change:

```bash
python3 scripts/check_repository.py
```

The check validates JSON metadata, Bash syntax, required public-repository files, and links between the repository's Markdown documents.

For changes under `bin/`, `migrations/`, or `scripts/meridian.py`, also run:

```bash
python3 -m unittest discover -s tests -v
```

For a change to a template or workflow rule, also manually trace the affected path from initialization through task creation, implementation, review, acceptance, and a framework-upgrade plan. The templates are the product.

## Release procedure

`python3 scripts/release.py prepare --bump patch` (or `--bump minor`,
`--bump major`, or `--version X.Y.Z`) is the repeatable local preparation
command. It derives the release kind from migrations, writes the version,
ledger, and changelog files, runs the release checks, and makes one local
release commit. It never fetches, pushes, creates a tag, or compares manifests.
Use `--dry-run` to inspect its derived result first. The manual procedure below
remains valid; in particular, the manifest comparison remains a manual step.

When changing the release version, update both `VERSION` and the `version`
field in `.claude-plugin/plugin.json`; the repository check requires them to
match.

Every release adds a `releases/<version>.json` record (see
[releases/README.md](releases/README.md)); `python3 scripts/check_repository.py`
requires one for the current `VERSION`. Then choose the release kind:

- **CLI-only release**: no template, workflow rule, or managed file changed.
  Bump `VERSION` and add the ledger record with `baselineChanged: false` and an
  empty `migrations` list. Add no migration; `workflowBaselineVersion` stays at
  the newest existing migration's target.
- **Template-changing release**: add a migration whose `to` equals the new
  `VERSION`, and list its id in the ledger record with `baselineChanged: true`.
  This is what advances `workflowBaselineVersion`.

Every `CHANGELOG.md` release section states its kind in its first line: begin a
CLI-only section with `CLI-only release` and a template-changing section with
`Template-changing release`. The line must agree with the ledger's
`baselineChanged`, and a template-changing section must also have a non-empty
`### Upgrade notes` subsection listing the affected capabilities and managed
paths, the required action (`upgrade --apply`), likely conflict areas for
adapted projects, and any minimum framework or `protocolVersion` change. The
release script enforces both rules.

The last migration may lag behind `VERSION` but must never target a version
ahead of it.

Once the release commit is on `main` and the checks pass, the maintainer pushes
the tag `v<VERSION>`; CI publishes the release. The
`.github/workflows/release.yml` workflow runs `scripts/prepare_release.py`, which
fails unless the tag equals `v` plus `VERSION`, `releases/<VERSION>.json` exists
with a matching `gitTag`, `.claude-plugin/plugin.json` matches `VERSION`, and
`CHANGELOG.md` has a `## [<VERSION>]` section whose kind line and Upgrade notes
satisfy the rules above. It then runs the repository check
and the unit tests, and creates the GitHub Release whose body is that changelog
section plus a link to `releases/<VERSION>.json`. Do not create the release by
hand. A failed run publishes nothing; fix the cause, then move the tag only if
no release exists for it.

Before releasing, compare the manifest written by the new CLI with the prior
release. Bump `PROTOCOL_VERSION` only when the manifest shape or semantics
change in a way that an older CLI cannot safely read. Backward-compatible
additions, including fields with a safe legacy fallback, do not require a
protocol bump. When a bump is required, add compatibility tests that prove the
older protocol remains readable and the newer protocol is rejected by the
current reader with upgrade guidance.

## Support policy

The support window is defined by Decision 6 in
`docs/DISTRIBUTION_AND_UPDATE_DESIGN.md` and stated for adopters in the README:

- Every published release from `v1.1.49` forward upgrades to the newest release
  in a single `upgrade --apply`, and releases may be skipped.
  `test_oldest_published_release_upgrades_to_current_in_one_apply` proves this
  from the snapshot in `tests/fixtures/release-1.1.49-governed-sdd.tar.gz`.
- Fixes land only in the newest release; do not add backport branches.
- Downgrades, manifests with an unrecorded baseline, and unreleased `main` are
  unsupported. Projects older than `v1.1.49` use `meridian adopt` best-effort.
- Never remove a migration or packaged baseline, or change the window, without a
  CHANGELOG-announced release and a migration or `adopt` path for affected
  projects. A change to a template or migration must keep the proving test green.

## Pull requests

Explain the user-facing problem, the workflow behavior that changes, and how you validated it. When a change modifies a mode rule, identify every corresponding asset you updated—for example, the workflow document, `AGENTS.md`, `CLAUDE.md`, task template, queue template, commands, and skills.

Avoid unrelated formatting changes. They make workflow changes harder to audit.
