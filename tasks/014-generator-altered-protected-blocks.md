# Task 014 — The `CLAUDE.md` generator altered protected marker content

> **ID**: `014`
> **Category**: Bugfix (templates + CLI guard)
> **Priority**: 🔴 P1
> **Estimate**: ~4h
> **Assigned to**: unassigned

## 🎯 Objective

Commit `0e116e0` (task 004) generates `CLAUDE.md`'s shared body from `AGENTS.md`
and, in doing so, changed the text inside three protected marker blocks without
bumping their version or shipping a migration. The framework silently changed
what `v1` means, so every adopted project still holding the previous text now
reads as an unauthorized edit.

Restore the three blocks, then make this class of change impossible to repeat.

## 📋 Acceptance Criteria

- [ ] The three blocks in `templates/workflows/governed-sdd/CLAUDE.md` carry
      their released `v1` text again: `command-triggers`,
      `implementer-reviewer-handoff`, `reviewer-integrator-identity`.
- [ ] The generator preserves marker-block content verbatim: it composes
      `CLAUDE.md`'s non-marker body from `AGENTS.md` and **never writes inside
      `MERIDIAN:BEGIN`/`MERIDIAN:END` delimiters**. Changing a marker's content
      is a migration's job, without exception.
- [ ] A test asserts that property directly: run the generator and confirm every
      marker block in its output is byte-identical to the corresponding block in
      the committed `CLAUDE.md`.
- [ ] A repository check fails when any template's marker content changes while
      its version does not, so a hand edit is caught as well as a generated one.
- [ ] `meridian audit` on a project at `1.1.20` returns no failures afterwards.
- [ ] `python3 scripts/check_repository.py` and the CLI suite pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | The generator added by `0e116e0`. |
| `templates/workflows/governed-sdd/CLAUDE.md` | The three altered blocks. |
| `scripts/check_repository.py` | Version-vs-content guard. |
| `tests/test_meridian_cli.py` | Generator preservation test. |

## 🧩 Technical Context

Observed on Palimpsest immediately after upgrading to 1.1.20:

```
FAIL CLAUDE.md: capability=command-triggers v1 — protected content does not match
FAIL CLAUDE.md: capability=implementer-reviewer-handoff v1 — idem
FAIL CLAUDE.md: capability=reviewer-integrator-identity v1 — idem
```

The project changed nothing. What changed is the released text these versions
point at. One of the three is not a rewording but a removal — `command-triggers`
lost guidance that was deliberately specific to `CLAUDE.md`:

```diff
- `Review <TASK-ID>` — … using `docs/CODE_REVIEW_PROMPT.md`, ideally in a fresh
-   chat or Task-tool subagent.
+ `Review <TASK-ID>` — … using `docs/CODE_REVIEW_PROMPT.md`.
```

**Why the existing test did not catch it.** Task 004 added a test asserting that
`CLAUDE.md` matches the generator's output. The generator produced the new text
and `CLAUDE.md` was regenerated from it, so the test passes. It verifies
self-consistency, not preservation — it can never fail on a change the generator
itself makes. This is the recurring shape in this queue: the intent was stated
correctly and the check compared the wrong thing.

`release-baselines/` holds only `1.0.0`, so it is not usable as the reference for
recent versions; the guard needs git history or a per-version content digest.

## ⚠️ Constraints and Considerations

- **Restore, do not bump.** Two of the three changes are pure rewording with
  identical meaning; bumping them to `v2` would ship a no-op migration to every
  project — churn that teaches operators that migrations are noise. Restoring
  `v1`'s released text fixes every adopted project with no migration at all.
- If, after restoring, the developer still wants `command-triggers` reworded,
  that is a separate deliberate change with a version bump and a migration —
  which is exactly the process this defect bypassed.
- Deciding "semantically identical" is not automatable. Do not try. The rule is
  mechanical and absolute: generated output never alters marker content.
- Palimpsest is at `1.1.20` with these three failures outstanding and was
  deliberately left red rather than hand-patched, so the audit keeps pointing at
  the real defect. It goes green when this task ships.

## 🔗 Dependencies

- **Depends on**: none
- **Blocks**: nothing formally, but it holds an adopted project's audit red.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/014-generator-altered-protected-blocks.md)"$'\n\nExecute this task in the current project.'
```
