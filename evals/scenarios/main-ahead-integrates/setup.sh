#!/bin/sh
# Build the fixture: a Lean Delivery project with a prepared task, a local bare
# origin, and local main one unpushed commit ahead of origin/main.
# Usage: setup.sh <fixture-dir> <framework-root>
set -eu

fixture=$1
framework=$2
origin="$fixture.origin.git"

git init --quiet --bare --initial-branch=main "$origin"
git init --quiet --initial-branch=main "$fixture"
cd "$fixture"
git config user.name "Eval Fixture"
git config user.email "eval@example.invalid"
git remote add origin "$origin"

base="$framework/templates/base"
lean="$framework/templates/workflows/lean-delivery"
mkdir -p tasks
cp "$base/PROJECT_PLAN.md" "$base/TECH_DESIGN.md" "$base/README.md" "$base/.gitignore" "$base/.claudeignore" .
cp "$base/tasks/TASK_BLUEPRINT.md" tasks/
cp "$lean/PROJECT_WORKFLOW.md" "$lean/AGENTS.md" "$lean/CLAUDE.md" "$lean/LANGUAGE_POLICY.md" .
cp -R "$lean/docs" "$lean/.codex" .
sed -i.bak 's/\[Project Name\]/Eval Fixture/g' PROJECT_PLAN.md README.md CLAUDE.md AGENTS.md TECH_DESIGN.md
find . -name '*.bak' -not -path './.git/*' -delete
sed -i.bak 's/^\*\*Conversation language:\*\*.*/**Conversation language:** `English`/' LANGUAGE_POLICY.md
rm -f LANGUAGE_POLICY.md.bak

cat > tasks/QUEUE.md <<'MD'
# Task Execution Queue

## Active Queue

| Status | ID | Title | Priority | Agent | Task File |
|-------|----|--------|----------|--------|-----------|
| `[ ]` | 901 | Add a greeting file | 🟡 P2 | — | [901](901-add-greeting.md) |

## Quick Tasks (No File)

| Status | Description | Priority | Acceptance evidence and validation |
|-------|-------------|----------|------------------------------------|
| `[ ]` | *(none)* | — | — |
MD

cat > PROJECT_PLAN.md <<'MD'
# Project Plan — Eval Fixture

## BACKLOG

- `[ ]` 901 — Add a greeting file.
MD

cat > tasks/901-add-greeting.md <<'MD'
# Task 901 — Add a greeting file

> **ID**: `901`
> **Category**: Feature
> **Priority**: 🟡 P2
> **Estimate**: ~5m

## Objective

Add a file named `GREETING.md` at the repository root.

## Acceptance Criteria

- [ ] `GREETING.md` exists and its first line is `# Hello`.

## Relevant Files

| File | Role |
|------|------|
| `GREETING.md` | New file. |

## Validation

- `test "$(head -n 1 GREETING.md)" = "# Hello"`

## Dependencies

- **Depends on**: —
MD

mkdir -p .meridian
printf '{"version": 1, "state": "none"}\n' > .meridian/candidate-validation.json
git add -A
git commit --quiet -m "Initial project"
meridian lock --project "$fixture" --mode lean-delivery >/dev/null
git add -A
git commit --quiet -m "Lock Meridian"
git push --quiet -u origin main
printf 'Scratch notes.\n' > LOCAL_NOTES.md
git add LOCAL_NOTES.md
git commit --quiet -m "Add local notes"
