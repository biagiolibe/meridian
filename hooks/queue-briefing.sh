#!/bin/bash
# Meridian queue briefing — fires on UserPromptSubmit.
# Outputs a compact status only if tasks/QUEUE.md exists in cwd.
# Silent exit in non-Meridian projects.

QUEUE="tasks/QUEUE.md"
[ -f "$QUEUE" ] || exit 0

# Governed SDD queues use explicit lifecycle states rather than checkbox rows.
# Keep the briefing compact; dependency eligibility remains a task/spec decision.
if grep -q '^| Order | ID | Priority | Status | Review | Dependencies |' "$QUEUE"; then
  ACTIVE=$(grep -m1 '^| [0-9].* | IN_PROGRESS |' "$QUEUE" | sed -E 's/^\| [0-9]+ \| ([^|]*)\|.*/\1/' | xargs)
  REVIEW=$(grep -m1 '^| [0-9].* | READY_FOR_REVIEW |' "$QUEUE" | sed -E 's/^\| [0-9]+ \| ([^|]*)\|.*/\1/' | xargs)
  PENDING=$(grep '^| [0-9].* | QUEUED |' "$QUEUE" | head -2 | sed -E 's/^\| [0-9]+ \| ([^|]*)\|.*/\1/' | xargs)
  ACCEPTED=$(grep -c '^| [0-9].* | ACCEPTED |' "$QUEUE" 2>/dev/null)

  echo "[Meridian Governed Queue]"
  [ -n "$ACTIVE" ] && echo "  🔴 In progress: $ACTIVE" || echo "  ✅ No active task"
  # Echo the active task's diagnostic/evidence/context-expansion budget so
  # the cap stays at maximum salience every turn instead of a rule read once
  # at turn 1. Silent whenever there is no active task, no meridian CLI, or
  # the CLI itself has nothing to report (unknown task, stale queue row).
  if [ -n "$ACTIVE" ] && [ -n "$CLAUDE_PLUGIN_ROOT" ] && [ -x "$CLAUDE_PLUGIN_ROOT/bin/meridian" ]; then
    BUDGET=$("$CLAUDE_PLUGIN_ROOT/bin/meridian" budget show "$ACTIVE" --project . 2>/dev/null)
    if [ -n "$BUDGET" ]; then
      echo "  ⏱  $BUDGET"
      echo "  ⛔ On exhaustion: return BLOCKED. Do not raise a cap."
    fi
  fi
  [ -n "$REVIEW" ] && echo "  🔎 In review: $REVIEW"
  [ -n "$PENDING" ] && echo "  ⏳ Queued: $PENDING"
  echo "  ✅ Accepted: $ACCEPTED"
  exit 0
fi

# Closed phases can be moved out of QUEUE.md into an archive file (same
# directory) to keep the active queue short — completed-task counts should
# still cover the whole project, so this is included whenever present.
ARCHIVE="tasks/QUEUE_ARCHIVE.md"

# Only match actual queue table rows: "| `[x]` | NNN | Title | ... |".
# Anchoring on a leading "| `[x]` | NNN |" (a 3-digit task id right after
# the status cell) excludes prose bullets elsewhere in the file that happen
# to contain the same backticked status markers (e.g. "How to use this
# queue"'s "[ ]" / "[/]" / "[x]" examples).

# Extract active task ([/]). Anchored (`^`) so sed captures the ID/title
# columns right after the status cell, not a later 3-digit "| NNN |"-shaped
# match elsewhere in the row (e.g. a "Depends on" column) — sed's regex is
# greedy and, unanchored, matches the rightmost candidate instead.
ACTIVE=$(grep -m1 "^| \`\[/\]\` | [0-9]\{3\} |" "$QUEUE" | sed -E 's/^\| `\[.\]` \| [0-9]{3} \| ([^|]*)\|.*/\1/' | xargs)

# Extract next pending tasks ([ ])
PENDING=$(grep "^| \`\[ \]\` | [0-9]\{3\} |" "$QUEUE" | head -2 | sed -E 's/^\| `\[.\]` \| ([0-9]{3}) \| ([^|]*)\|.*/\1 - \2/' | xargs | sed 's/  */ /g')

# Count completed ([x]) rows across the active queue and, if present, the
# archive — a task moved to QUEUE_ARCHIVE.md is still a completed task for
# this project, not an uncounted one.
# `grep -c` already prints "0" and exits 1 on no match, so `|| echo 0` would
# double it up — redirect stderr only, don't fall back on exit status.
DONE_ACTIVE=$(grep -c "^| \`\[x\]\` | [0-9]\{3\} |" "$QUEUE" 2>/dev/null)
DONE_ARCHIVE=0
if [ -f "$ARCHIVE" ]; then
  DONE_ARCHIVE=$(grep -c "^| \`\[x\]\` | [0-9]\{3\} |" "$ARCHIVE" 2>/dev/null)
fi
DONE=$((DONE_ACTIVE + DONE_ARCHIVE))

echo "[Meridian Lean Delivery Queue]"
if [ -n "$ACTIVE" ]; then
  echo "  🔴 In progress: $ACTIVE"
else
  echo "  ✅ No active task"
fi
if [ -n "$PENDING" ]; then
  echo "  ⏳ Queued: $PENDING"
fi
echo "  ✅ Completed: $DONE"
