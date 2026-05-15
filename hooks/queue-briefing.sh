#!/bin/bash
# Meridian queue briefing — fires on UserPromptSubmit.
# Outputs a compact status only if tasks/QUEUE.md exists in cwd.
# Silent exit in non-Meridian projects.

QUEUE="tasks/QUEUE.md"
[ -f "$QUEUE" ] || exit 0

# Extract active task ([/])
ACTIVE=$(grep -m1 '`\[/\]`' "$QUEUE" | sed 's/.*| [0-9]\{3\} | \([^|]*\)|.*/\1/' | xargs)

# Extract next pending tasks ([ ])
PENDING=$(grep '`\[ \]`' "$QUEUE" | head -2 | sed 's/.*| \([0-9]\{3\}\) | \([^|]*\)|.*/\1 - \2/' | xargs | sed 's/  */ /g')

# Count completed ([x])
DONE=$(grep -c '`\[x\]`' "$QUEUE" 2>/dev/null || echo 0)

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
