#!/usr/bin/env python3
"""Small dependency-free checks for Meridian's distributable repository."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402

# Deliberately not directly inside migrations/: `meridian.py`'s
# capability_requirements() and migration_ids() glob `migrations/*.json`
# expecting every match to be a migration record (with "id"/"from"/"to"/...
# fields); a baseline file there would satisfy the glob and blow up the first
# reader with a KeyError. A subdirectory is invisible to that non-recursive
# glob, so this file sits one level down instead.
MARKER_BASELINE_PATH = ROOT / "migrations" / "marker-baselines" / "CAPABILITY_MARKER_BASELINES.json"
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
    "migrations/006-capability-markers.json",
    "migrations/007-validation-capability-markers.json",
    "migrations/008-review-remediation-record-v2.json",
    "migrations/009-lifecycle-orchestration-v2.json",
    "migrations/010-project-workflow-baseline-capabilities.json",
    "migrations/011-whole-file-baseline-capabilities.json",
    "migrations/012-agents-claude-residual-capabilities.json",
    "migrations/013-language-policy-v2.json",
    "migrations/README.md",
    "migrations/ASSISTED_ADOPTION.md",
    "release-baselines/1.0.0/templates/workflows/governed-sdd/PROJECT_WORKFLOW.md",
    "commands/meridian-upgrade.md",
    "commands/meridian-adopt.md",
    "commands/meridian-audit.md",
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


def current_marker_baselines(root: Path = ROOT) -> dict[str, dict[str, dict[str, object]]]:
    """capability marker content, by managed template file, for every mode.

    Every managed template (`meridian.managed_files`, the same set a project
    actually receives and `meridian audit` checks) is scanned for its capability
    markers. The result maps relative file path -> capability -> {version,
    sha256 of that marker's exact content}. Two templates can legitimately hold
    different content for the same capability+version (task 014's
    `command-triggers` v1 differs between `AGENTS.md` and `CLAUDE.md` by
    design), so content is keyed per file, never merged across files.
    """
    marked_content = re.compile(
        r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->\n?(.*?)<!-- MERIDIAN:END -->",
        re.DOTALL,
    )
    baselines: dict[str, dict[str, dict[str, object]]] = {}
    for mode in meridian.CLAUDE_MD_SHARED_ANCHOR:
        for item in meridian.managed_files(root, mode):
            relative = str(item.source.relative_to(root))
            if relative in baselines:
                continue
            text = item.source.read_text(encoding="utf-8")
            markers: dict[str, dict[str, object]] = {}
            for capability, version, content in marked_content.findall(text):
                markers[capability] = {
                    "version": int(version),
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                }
            if markers:
                baselines[relative] = markers
    return baselines


def write_marker_baselines(root: Path = ROOT) -> None:
    baseline_path = root / "migrations" / "marker-baselines" / "CAPABILITY_MARKER_BASELINES.json"
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(current_marker_baselines(root), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def check_capability_marker_baselines(root: Path = ROOT) -> None:
    """Protected marker content may change only via a version bump (task 014).

    `MARKER_BASELINE_PATH` records the content each template's capability
    markers held the last time a developer deliberately ran
    `check_repository.py --write-marker-baselines`, immediately after choosing
    to introduce or bump a marker. Comparing the live templates against that
    record catches both a hand edit and a generator regression: same version,
    different content is always a failure; any other mismatch means the
    baseline itself is stale and must be regenerated as part of the same
    change, so the record stays an explicit, reviewed act, not something a
    tool updates on its own.
    """
    baseline_path = root / "migrations" / "marker-baselines" / "CAPABILITY_MARKER_BASELINES.json"
    if not baseline_path.is_file():
        fail(f"capability marker baseline is missing: {baseline_path.relative_to(root)}")
    recorded = json.loads(baseline_path.read_text(encoding="utf-8"))
    current = current_marker_baselines(root)
    for relative, markers in current.items():
        recorded_file = recorded.get(relative, {})
        for capability, info in markers.items():
            baseline = recorded_file.get(capability)
            if baseline is None:
                fail(
                    f"{relative}: capability={capability} v{info['version']} has no recorded baseline; "
                    "run `python3 scripts/check_repository.py --write-marker-baselines` after a deliberate change"
                )
            elif baseline["version"] == info["version"] and baseline["sha256"] != info["sha256"]:
                fail(
                    f"{relative}: capability={capability} v{info['version']} — protected content changed "
                    "without a version bump; restore the released text or bump the version as a deliberate "
                    "migration"
                )
            elif baseline["version"] != info["version"] or baseline["sha256"] != info["sha256"]:
                fail(
                    f"{relative}: capability={capability} v{info['version']} does not match its recorded "
                    "baseline; run `python3 scripts/check_repository.py --write-marker-baselines` to record "
                    "this deliberate change"
                )
    for relative, markers in recorded.items():
        current_file = current.get(relative, {})
        for capability in markers:
            if capability not in current_file:
                fail(f"{relative}: recorded capability={capability} baseline no longer present in the template")


def main() -> None:
    if "--write-marker-baselines" in sys.argv[1:]:
        write_marker_baselines()
        print(f"Wrote {MARKER_BASELINE_PATH.relative_to(ROOT)}.")
        return
    check_required_files()
    check_language_policy()
    check_json()
    check_migrations()
    check_bash()
    check_local_markdown_links()
    check_capability_marker_baselines()
    print("Meridian repository checks passed.")


if __name__ == "__main__":
    main()
