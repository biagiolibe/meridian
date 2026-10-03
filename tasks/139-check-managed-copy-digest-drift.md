# Task 139 — Make `check_repository.py` catch managed-copy digest drift

> **ID**: `139`
> **Category**: Bugfix
> **Priority**: 🟡 P2
> **Estimate**: ~1.5h
> **Assigned to**: unassigned
> **Session**: Candidate validation failure of task 134, 2026-10-03

## Objective

This repository records the SHA-256 of its own managed copies (for example
`docs/CONTEXT_BUDGET_POLICY.md`) in `.meridian/manifest.json`, in the
`managedFiles` map and in the self-hosting profile's digest evidence. A task that
edits a managed copy must refresh those digests, but nothing in
`python3 scripts/check_repository.py` verifies it. Task 134 changed
`docs/CONTEXT_BUDGET_POLICY.md` and left the digests unchanged; the task's own
checks passed, and the drift appeared only in the full suite
(`test_profile_doctor_is_read_only_and_resolves_required_probes`, four profile
surfaces failing with `drifted managed-copy surface`) during candidate
validation, after about two minutes. Make the repository check report this drift
at once, and give maintainers a deterministic way to refresh the digests.

## Acceptance Criteria

- [ ] `python3 scripts/check_repository.py` fails when a managed copy listed in
  `.meridian/manifest.json` has a different SHA-256 than the recorded one, naming
  each drifted file, the recorded digest, the current digest, and the command that
  refreshes it. It also reports digest evidence entries that no longer match the
  file.
- [ ] The check reuses the comparison the self-hosting profile doctor already
  performs instead of re-implementing it, so the two cannot disagree. A test proves
  that the repository check and `meridian profile doctor` give the same verdict on
  the same drifted fixture.
- [ ] The check is read-only and fast (it hashes the listed files only); it does not
  run the doctor's host probes.
- [ ] `python3 scripts/check_repository.py --write-managed-digests` rewrites the
  recorded digests of the managed copies from the files on disk, in the manifest's
  existing key order and formatting, touching only digest values, and prints each
  change. Running it twice changes nothing. It refuses to run if a listed file is
  missing, instead of recording an empty value.
- [ ] The refresh is explicit, like `--write-marker-baselines`: a plain check never
  rewrites the manifest. The failure message and `CONTRIBUTING.md` state when to
  run it (after a deliberate edit of a managed copy) and that the resulting diff
  must be reviewed.
- [ ] A drift introduced by editing a managed copy without refreshing the digests
  fails the check on a task branch, in the same way as on the candidate tree.
- [ ] Tests cover: no drift passes; a drifted copy fails with the expected message;
  stale digest evidence fails; the refresh fixes both and is idempotent; a missing
  listed file is refused; the check does not write; and agreement with the doctor.
- [ ] One changelog fragment is added per `CONTRIBUTING.md` if `CONTRIBUTING.md` or
  the script output changes for maintainers.
- [ ] `python3 scripts/check_repository.py` and the unit tests pass.

## Relevant Files

| File | Role |
|------|------|
| `scripts/check_repository.py` | New digest check and the `--write-managed-digests` option. |
| `scripts/meridian.py` | The profile doctor's managed-copy comparison to reuse. |
| `.meridian/manifest.json` | Recorded digests (`managedFiles` and profile evidence). |
| `CONTRIBUTING.md` | When to refresh the digests. |
| `tests/test_check_repository.py` | Check and refresh tests. |

## Technical Context

- Observed on 2026-10-03: the failing test reported `expected c3e30904…, got
  441afba6…` for `docs/CONTEXT_BUDGET_POLICY.md` on four surfaces
  (`context-budgeting`, `execution-evidence`, `minimal-read-only-status`,
  `validation-scoping`). The old digest appeared five times in the manifest.
- Task 120 had refreshed the manifest by hand for
  `docs/EXECUTION_EVIDENCE_PROFILE.md` (two lines); there was no written rule or
  tool for it, and task 134's targeted tests plus `check_repository.py` could not
  see the drift.
- Marker baselines already have the pattern to follow: a failing check that names
  the exact refresh command (`--write-marker-baselines`).

## Validation

- `python3 scripts/check_repository.py`
- `python3 -m unittest discover -s tests`
- `git diff --check`

## Out of scope

Changing the profile doctor's probes, host verification, template or consumer
manifests, and automatic refresh during any normal check.

## Dependencies

- **Depends on**: —
- **Blocks**: none
