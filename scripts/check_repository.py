#!/usr/bin/env python3
"""Small dependency-free checks for Meridian's distributable repository."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "VERSION",
    "LICENSE",
    "CONTRIBUTING.md",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "hooks/hooks.json",
    "hooks/queue-briefing.sh",
    "bin/meridian",
    "scripts/meridian.py",
    "migrations/001-review-remediation-record.json",
    "migrations/002-lifecycle-orchestration.json",
    "migrations/003-framework-updater.json",
    "migrations/004-validation-scoping.json",
    "migrations/005-ci-verified-validation.json",
    "migrations/README.md",
    "migrations/ASSISTED_ADOPTION.md",
    "release-baselines/1.0.0/templates/workflows/governed-sdd/PROJECT_WORKFLOW.md",
    "commands/meridian-upgrade.md",
    "commands/meridian-adopt.md",
    "templates/workflows/lean-delivery/PROJECT_WORKFLOW.md",
    "templates/workflows/lean-delivery/AGENTS.md",
    "templates/workflows/lean-delivery/CLAUDE.md",
    "skills/meridian-lean-delivery/SKILL.md",
    "skills/meridian-lean-delivery-claude-code/SKILL.md",
)
LANGUAGE_POLICY_FILES = (
    "templates/base/LANGUAGE_POLICY.md",
    "templates/workflows/governed-sdd/LANGUAGE_POLICY.md",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_required_files() -> None:
    for name in REQUIRED_FILES:
        if not (ROOT / name).is_file():
            fail(f"required file is missing: {name}")


def check_language_policy() -> None:
    for name in LANGUAGE_POLICY_FILES:
        path = ROOT / name
        if not path.is_file():
            fail(f"language policy template is missing: {name}")
        text = path.read_text(encoding="utf-8")
        for required_text in (
            "[Conversation language]",
            "another language is not a request to switch languages",
            "All text that remains in the repository must be written in English.",
        ):
            if required_text not in text:
                fail(f"language policy is incomplete: {name}")

    for name in (
        "templates/base/CLAUDE.md",
        "templates/workflows/lean-delivery/AGENTS.md",
        "templates/workflows/lean-delivery/CLAUDE.md",
        "templates/workflows/governed-sdd/AGENTS.md",
        "templates/workflows/governed-sdd/CLAUDE.md",
    ):
        if "LANGUAGE_POLICY.md" not in (ROOT / name).read_text(encoding="utf-8"):
            fail(f"agent instructions do not load the language policy: {name}")

    mode_lock_files = (
        "commands/meridian-task.md",
        "templates/workflows/governed-sdd/PROJECT_WORKFLOW.md",
        "templates/workflows/governed-sdd/AGENTS.md",
        "templates/workflows/governed-sdd/CLAUDE.md",
        "templates/workflows/governed-sdd/docs/CODE_REVIEW_PROMPT.md",
        "templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md",
    )
    for name in mode_lock_files:
        text = (ROOT / name).read_text(encoding="utf-8")
        if "GOVERNED_SDD" not in text or "BLOCKED" not in text:
            fail(f"governed-SDD mode lock is incomplete: {name}")

    lean_mode_lock_files = (
        "templates/workflows/lean-delivery/PROJECT_WORKFLOW.md",
        "templates/workflows/lean-delivery/AGENTS.md",
        "templates/workflows/lean-delivery/CLAUDE.md",
        "skills/meridian-lean-delivery/SKILL.md",
        "skills/meridian-lean-delivery-claude-code/SKILL.md",
    )
    for name in lean_mode_lock_files:
        text = (ROOT / name).read_text(encoding="utf-8")
        if "LEAN_DELIVERY" not in text or "BLOCKED" not in text:
            fail(f"Lean Delivery mode lock is incomplete: {name}")

    operator_prompts = ROOT / "templates/workflows/governed-sdd/docs/OPERATOR_PROMPTS.md"
    if not operator_prompts.is_file():
        fail("governed-SDD operator prompts are missing")
    if "This non-normative cookbook" not in operator_prompts.read_text(
        encoding="utf-8"
    ):
        fail("governed-SDD operator prompts must remain non-normative")


def check_json() -> None:
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail(f"invalid JSON in {path.relative_to(ROOT)}: {error}")


def check_migrations() -> None:
    migration_paths = sorted((ROOT / "migrations").glob("[0-9][0-9][0-9]-*.json"))
    if not migration_paths:
        fail("no framework migrations are defined")
    previous_to = None
    for index, path in enumerate(migration_paths, start=1):
        data = json.loads(path.read_text(encoding="utf-8"))
        expected_prefix = f"{index:03d}-"
        required = ("id", "from", "to", "description", "managedPaths", "verification")
        if not path.name.startswith(expected_prefix) or not str(data.get("id", "")).startswith(expected_prefix):
            fail(f"migration sequence is invalid: {path.relative_to(ROOT)}")
        if any(key not in data for key in required):
            fail(f"migration is incomplete: {path.relative_to(ROOT)}")
        if previous_to is not None and data["from"] != previous_to:
            fail(f"migration versions are not contiguous: {path.relative_to(ROOT)}")
        previous_to = data["to"]
    current_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if previous_to != current_version:
        fail("latest migration does not match VERSION")


def check_bash() -> None:
    for path in ROOT.rglob("*.sh"):
        result = subprocess.run(
            ["bash", "-n", str(path)], check=False, capture_output=True, text=True
        )
        if result.returncode:
            fail(f"invalid Bash in {path.relative_to(ROOT)}: {result.stderr.strip()}")


def check_local_markdown_links() -> None:
    for path in ROOT.rglob("*.md"):
        relative_path = path.relative_to(ROOT)
        # Templates deliberately link to files that an initialized project may
        # create later (for example, QUEUE_ARCHIVE.md). They are examples of a
        # future project tree, not broken links in this repository.
        if "templates" in relative_path.parts or relative_path == Path(
            "tasks/QUEUE_TEMPLATE.md"
        ):
            continue
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            destination = (path.parent / target).resolve()
            if not destination.exists():
                fail(
                    f"broken local Markdown link in {relative_path}: {target}"
                )


def main() -> None:
    check_required_files()
    check_language_policy()
    check_json()
    check_migrations()
    check_bash()
    check_local_markdown_links()
    print("Meridian repository checks passed.")


if __name__ == "__main__":
    main()
