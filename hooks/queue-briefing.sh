#!/bin/bash
# Meridian queue briefing — fires on UserPromptSubmit.
# Outputs a compact status only if the project's queue file exists in cwd.
# Silent exit in non-Meridian projects.

# governed-SDD's `execution-assets` capability defaults the queue to
# `tasks/QUEUE.md` "unless this section declares different locations for
# this project" (see templates/workflows/governed-sdd/PROJECT_WORKFLOW.md).
# A project that customizes it does so in an annotated paragraph immediately
# after that marker's END, still inside the "## Execution assets" section
# (the pattern task 014 documented from Palimpsest's own adoption). Scan
# exactly that zone for a `*queue*.md`-shaped path; a project with no
# customization has nothing there and falls through to the default.
resolve_queue_path() {
  local workflow="PROJECT_WORKFLOW.md"
  local default="tasks/QUEUE.md"
  [ -f "$workflow" ] || { echo "$default"; return; }

  local zone
  zone=$(awk '
    /<!-- MERIDIAN:BEGIN capability=execution-assets /{ inblock=1; next }
    inblock && /<!-- MERIDIAN:END -->/ { inblock=0; inzone=1; next }
    inzone && /^## / { exit }
    inzone { print }
  ' "$workflow")
  [ -n "$zone" ] || { echo "$default"; return; }

  # Case-insensitive, deduplicated candidates. Excluding an archive path
  # matters: task 009 itself documents archiving terminal rows to a
  # `*QUEUE*ARCHIVE*.md`-shaped file in this same zone, which would
  # otherwise be indistinguishable from the live queue's own declaration.
  local candidates
  candidates=$(printf '%s\n' "$zone" \
    | grep -Eio '[A-Za-z0-9_./-]*queue[A-Za-z0-9_./-]*\.md' \
    | grep -Eiv 'archive' \
    | sort -u)

  # Exactly one distinct, non-archive candidate is a confident resolution.
  # Zero, or more than one (an ambiguous zone this heuristic cannot safely
  # pick between), silently keep the default rather than guess wrong — a
  # briefing computed from the wrong file is worse than no briefing.
  if [ "$(printf '%s\n' "$candidates" | grep -c .)" = "1" ]; then
    echo "$candidates"
  else
    echo "$default"
  fi
}

QUEUE=$(resolve_queue_path)
[ -f "$QUEUE" ] || exit 0

# An archived ACCEPTED row (this task's own archiving convention) still
# satisfies a dependency and still counts toward the accepted tally; both
# queue formats below read it from here alongside the active queue's own
# rows, not as a separate uncounted total.
ARCHIVE="$(dirname "$QUEUE")/QUEUE_ARCHIVE.md"

# Governed SDD queues use explicit lifecycle states rather than checkbox rows.
# A governed queue needs lifecycle columns, not one exact framework-shaped
# header.  Established projects may intentionally omit the optional `Review`
# or task-file columns.  The parser below maps the required columns by name.
if grep -Eq '^\| Order \| ID \|.*\| Status \|.*Dependencies \|' "$QUEUE"; then
  ARCHIVE_ARG=""
  [ -f "$ARCHIVE" ] && ARCHIVE_ARG="$ARCHIVE"
  # Single awk pass: collect every row's ID/status/dependencies, then
  # resolve which QUEUED rows are actually startable (every dependency
  # ACCEPTED or, for a SPIKE, ANSWERED — task-lifecycle v2's rule) versus
  # blocked on an unmet one, so a session gets the same answer the queue's
  # own "choose the highest-priority queued task whose dependencies are all
  # accepted" instruction requires, without opening the file to compute it.
  # ANSWERED/INCONCLUSIVE rows stay outside the ACCEPTED tally (the same
  # capability's "invisible to those counts by design" rule for SPIKE rows) —
  # this only widens what counts as satisfying a *dependency*, a separate
  # question from what counts toward the accepted total.
  eval "$(awk -F'\\|' '
    function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
    # Single-quote a value for safe eval: close the quote, escape any
    # embedded single quote, reopen it. Values here are queue row IDs, never
    # attacker-controlled, but this is the only line standing between an
    # unquoted field and `eval`, so it earns the defensive treatment anyway.
    function shquote(s) { gsub(/'"'"'/, "'"'"'\\'"'"''"'"'", s); return "'"'"'" s "'"'"'" }
    /^\|/ && $0 ~ /\| Order \|/ {
      for (column = 2; column <= NF - 1; column++) {
        name = trim($column)
        if (name != "") columns[name] = column
      }
      next
    }
    /^\| [0-9]+ /{
      if (!("ID" in columns) || !("Status" in columns) || !("Dependencies" in columns)) next
      n++
      id[n]     = trim($(columns["ID"]))
      status[n] = trim($(columns["Status"]))
      deps[n]   = trim($(columns["Dependencies"]))
      by_status[id[n]] = status[n]
    }
    END {
      active = ""; review = ""
      ready_n = 0; blocked_n = 0
      ready = ""; blocked = ""
      accepted = 0
      for (i = 1; i <= n; i++) {
        s = status[i]
        if (s == "ACCEPTED") accepted++
        if (s == "IN_PROGRESS" && active == "") active = id[i]
        else if (s == "READY_FOR_REVIEW" && review == "") review = id[i]
        else if (s == "QUEUED") {
          d = trim(deps[i])
          gsub(/[][]/, "", d)
          met = 1
          if (d != "" && d != "—" && d != "-") {
            split(d, parts, ",")
            for (p in parts) {
              dep = trim(parts[p])
              dep_status = by_status[dep]
              if (dep_status != "ACCEPTED" && dep_status != "ANSWERED") met = 0
            }
          }
          if (met) {
            ready_n++
            if (ready_n <= 2) ready = ready (ready == "" ? "" : ", ") id[i]
          } else {
            blocked_n++
            if (blocked_n <= 2) blocked = blocked (blocked == "" ? "" : ", ") id[i]
          }
        }
      }
      printf "ACTIVE=%s\n", shquote(active)
      printf "REVIEW=%s\n", shquote(review)
      printf "READY=%s\n", shquote(ready)
      printf "READY_N=%d\n", ready_n
      printf "BLOCKED=%s\n", shquote(blocked)
      printf "BLOCKED_N=%d\n", blocked_n
      printf "ACCEPTED=%d\n", accepted
    }
  ' "$QUEUE" $ARCHIVE_ARG)"

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
  if [ "${READY_N:-0}" -gt 0 ]; then
    SUFFIX=""
    [ "$READY_N" -gt 2 ] && SUFFIX=" (+$((READY_N - 2)) more)"
    echo "  ⏳ Queued (startable): $READY$SUFFIX"
  fi
  if [ "${BLOCKED_N:-0}" -gt 0 ]; then
    SUFFIX=""
    [ "$BLOCKED_N" -gt 2 ] && SUFFIX=" (+$((BLOCKED_N - 2)) more)"
    echo "  🚧 Blocked on dependencies: $BLOCKED$SUFFIX"
  fi
  echo "  ✅ Accepted: ${ACCEPTED:-0}"
  exit 0
fi

# ARCHIVE was already resolved above, alongside QUEUE. Closed phases moved
# there (same directory) keep the active queue short — completed-task counts
# should still cover the whole project, so this is included whenever present.

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
