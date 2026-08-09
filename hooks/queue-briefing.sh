#!/bin/bash
# Meridian queue briefing — fires on UserPromptSubmit.
# Outputs a compact status only if tasks/QUEUE.md exists in cwd.
# Silent exit in non-Meridian projects.

QUEUE="tasks/QUEUE.md"
[ -f "$QUEUE" ] || exit 0

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

echo "[Meridian Queue]"
if [ -n "$ACTIVE" ]; then
  echo "  🔴 In corso: $ACTIVE"
else
  echo "  ✅ Nessun task attivo"
fi
if [ -n "$PENDING" ]; then
  echo "  ⏳ In coda: $PENDING"
fi
echo "  ✅ Completati: $DONE"
