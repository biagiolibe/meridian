# Task 085 — Repair and replace the Codex profile root in one setup step

> **ID**: `085`
> **Category**: Host Integration / Reliability
> **Priority**: 🟡 P2
> **Estimate**: ~3–5h
> **Assigned to**: unassigned
> **Session**: 2026-10-01 first `meridian setup --apply` blocked on a real configuration

## 🎯 Objective

Let `meridian setup --apply` (and `meridian codex configure --apply`) move a
Meridian-owned Codex permission profile to a new worktree root even when a
Codex update has also dropped or normalized Meridian's ownership markers, in a
single reviewed and backed-up change.

Today the combination is `BLOCKED`. Task 062 recovers a profile whose markers
are damaged only when its root equals the requested root, and the ordinary
replacement path requires intact markers. A developer who has a valid but
unmarked profile for an old root, and who then adopts the unified default root
from Task 083, must discover and run a two-step sequence by hand. The real
case that exposed this: only the closing `# MERIDIAN:END worktree-permissions`
marker was missing, the profile was otherwise identical, and the root was the
old `…/palimpsest/.claude/worktrees`; `setup` answered "reconcile it manually".

## 📋 Acceptance Criteria

- [ ] A new classification, named in `--check` and `setup --check` output (for
      example `repair-and-replace-required`), is reported when all of these
      hold: `default_permissions` selects `meridian-worktrees`; the profile has
      exactly the Meridian `description`, `extends = ":workspace"`, and a
      `workspace_roots` table containing exactly one root set to `true`; that
      root differs from the requested root; and the ownership markers are
      missing, moved, or normalized.
- [ ] `--check` prints one unified diff covering both the marker restoration and
      the root replacement, states that the change repairs ownership metadata
      and replaces the root, and writes nothing.
- [ ] `--apply` performs that change only on explicit invocation, creates an
      exclusive owner-only backup before the first write, uses the existing
      atomic write path, verifies the file is unchanged since planning, and
      preserves unrelated keys, comments, tables, and application settings.
      Repeating it is a no-op.
- [ ] The resulting configuration parses to the same document as before except
      for the one root value; this is asserted by the same parsed-equivalence
      check Task 062 uses.
- [ ] Any profile that is not exactly the shape above stays `BLOCKED` and is
      never adopted or overwritten: a different description or parent, extra
      or multiple roots, extra grants, a partial match, duplicate tables,
      inline or dotted serializations Meridian cannot edit exactly, a different
      default selection, and legacy sandbox settings.
- [ ] The `BLOCKED` message no longer says only "reconcile it manually": it
      names every diverging field and, when the only blocker is a documented
      two-step case, the exact next command.
- [ ] `meridian doctor`-style diagnostics, `meridian codex doctor`, and the
      start-of-turn briefing report the new state on one line and do not
      modify anything.
- [ ] The intact-marker and equal-root paths from Tasks 054, 062, and 083
      behave exactly as before; existing tests for them pass unchanged.
- [ ] `docs/HOST_CAPABILITY_CONTRACT.md` updates the recovery section to
      include the new state and keeps its statement that repair proves only
      that the configuration file is effective, not that a running session
      reloaded it.
- [ ] Tests cover the real observed fixture (profile intact except the missing
      `END` marker, old root), a moved marker, a normalized marker, an exact
      equal-root repair, and each refusal case above. No test writes to the
      real Codex configuration or home directory.
- [ ] `python3 -m unittest discover -s tests`,
      `python3 scripts/check_repository.py`, and `git diff --check` pass.

## 📁 Relevant Files

| File | Role |
|------|------|
| `scripts/meridian.py` | `_codex_profile_divergence`, the Codex configuration plan and apply code, `plan_setup`, `_setup_codex_state`, `apply_setup`. |
| `docs/HOST_CAPABILITY_CONTRACT.md` | Recovery contract for lost ownership markers. |
| `hooks/queue-briefing.sh` | One-line state notice, read-only. |
| `tests/` | Codex configuration and setup coverage. |

## 🧩 Technical Context

- **Current behavior**: a profile with damaged markers is `repair-required`
  only for the exact requested root. For another root the planner reports the
  divergence in `workspace_roots` and `setup` blocks before any mutation. With
  intact markers around another root, the ordinary managed replacement applies.
- **Why the root is not ownership evidence on its own**: the Meridian-specific
  description plus `extends`, selection, and the single `workspace_roots`
  shape identify a Meridian-written profile. A root change is a deliberate
  request from the same user, so it must not force a manual edit of a file the
  host application also rewrites.
- **Desired behavior**: one explicit, backed-up change when the profile is
  provably Meridian-shaped and only the root differs; every other shape stays
  blocked.
- **Safety invariant**: no inference from comments, no merge with a foreign or
  extended profile, no network, home, or unrestricted filesystem grant.

## 🔨 Suggested Implementation

1. Add the fixture from the observed configuration and the other marker cases.
2. Extend the planner with the new classification and the combined diff,
   reusing the repair and replacement helpers instead of duplicating them.
3. Route `setup` and `codex configure` through it and update their messages.
4. Update the diagnostics, briefing line, and contract text.
5. Add the listed tests, including the refusal matrix.

## ⚠️ Constraints and Considerations

- Never write the user's real `~/.codex/config.toml` from tests.
- Do not weaken fail-closed behavior for foreign or ambiguous configuration.
- Preserve project-owned text outside managed capability markers.
- If a protected capability region changes, bump its version, rewrite marker
  baselines deliberately, and add a migration; otherwise state in the handoff
  why none is needed.
- Repository artifacts are English-only.

## 🔗 Dependencies

- **Depends on**: 062, 083.
- **Blocks**: none.

## 🤖 How to delegate this task to Claude CLI

```bash
claude "$(cat tasks/085-setup-repair-and-replace-codex-profile-root.md)"$'\n\nExecute this task in the current project.'
```
