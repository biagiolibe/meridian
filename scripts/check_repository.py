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
    "capabilities/catalog-v1.json",
    "schemas/capability-catalog-v1.schema.json",
    "schemas/manifest-v2.schema.json",
    ".meridian/probes/meridian-self-hosting/host-neutral-ci-v1.json",
    ".meridian/probes/meridian-self-hosting/claude-project-v1.json",
    ".meridian/probes/meridian-self-hosting/codex-project-v1.json",
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
    "migrations/048-manifest-capability-profile-schema.json",
    "migrations/052-install-meridian-self-hosting-surfaces.json",
    "migrations/README.md",
    "migrations/ASSISTED_ADOPTION.md",
    "release-baselines/1.0.0/templates/workflows/governed-sdd/PROJECT_WORKFLOW.md",
    "commands/meridian-upgrade.md",
    "commands/meridian-adopt.md",
    "commands/meridian-audit.md",
    "templates/workflows/lean-delivery/PROJECT_WORKFLOW.md",
    "templates/workflows/lean-delivery/AGENTS.md",
    "templates/workflows/lean-delivery/CLAUDE.md",
    "templates/workflows/lean-delivery/LANGUAGE_POLICY.md",
    "templates/workflows/lean-delivery/docs/CONTEXT_BUDGET_POLICY.md",
    "templates/workflows/lean-delivery/docs/EXECUTION_EVIDENCE_PROFILE.md",
    "templates/workflows/lean-delivery/.codex/hooks.json",
    "skills/meridian-lean-delivery/SKILL.md",
    "skills/meridian-lean-delivery-claude-code/SKILL.md",
)
LANGUAGE_POLICY_FILES = (
    "templates/base/LANGUAGE_POLICY.md",
    "templates/workflows/lean-delivery/LANGUAGE_POLICY.md",
    "templates/workflows/governed-sdd/LANGUAGE_POLICY.md",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
RETIRED_GOVERNED_REVIEW_PHRASES = (
    "uses that same primary checkout",
    "git switch <task-branch>",
    "leave the primary checkout clean and on the task branch",
)


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


def check_governed_review_worktree_contract(root: Path = ROOT) -> None:
    workflow = root / "templates" / "workflows" / "governed-sdd"
    review_paths = (
        workflow / "PROJECT_WORKFLOW.md",
        workflow / "docs" / "CODE_REVIEW_PROMPT.md",
        workflow / "docs" / "LIFECYCLE_ORCHESTRATION.md",
        workflow / "docs" / "workflows" / "REVIEW.md",
    )
    for path in review_paths:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for phrase in RETIRED_GOVERNED_REVIEW_PHRASES:
            if phrase in lowered:
                fail(
                    f"retired primary-checkout review instruction in "
                    f"{path.relative_to(root)}: {phrase}"
                )

    review = review_paths[-1].read_text(encoding="utf-8")
    preflight = "<!-- MERIDIAN:BEGIN capability=task-worktree-review-procedure v5 -->"
    boundary = "<!-- MERIDIAN:BEGIN capability=review-mode-boundary v1 -->"
    required = (
        "Before reading the assigned task",
        "meridian worktree check <TASK-ID>",
        "stops before any other read",
        "git worktree list\n   --porcelain",
        "git -C\n   <absolute-task-worktree>",
        "empty `git status --short`",
        "task and base commits exist",
        "Only after every preflight check passes",
        "initial current directory is never treated as\nthe task checkout",
    )
    if preflight not in review or boundary not in review or review.index(preflight) > review.index(boundary):
        fail("governed review must begin with the task-worktree preflight")
    for fragment in required:
        if fragment not in review:
            fail(f"governed task-worktree review preflight is incomplete: {fragment}")


def check_json() -> None:
    for path in ROOT.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            fail(f"invalid JSON in {path.relative_to(ROOT)}: {error}")


def check_plugin_version(root: Path = ROOT) -> None:
    expected_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    plugin_manifest = json.loads(
        (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    plugin_version = plugin_manifest.get("version")
    if plugin_version != expected_version:
        fail(
            ".claude-plugin/plugin.json version "
            f"{plugin_version!r} does not match VERSION {expected_version!r}"
        )


def check_capability_catalog(root: Path = ROOT) -> None:
    try:
        catalog = meridian.load_capability_catalog(root)
    except meridian.MeridianError as error:
        fail(f"invalid capability catalog: {error}")
    profile = catalog.profile("meridian-self-hosting")
    if profile is None or not profile.capabilities:
        fail("capability catalog is missing the versioned meridian-self-hosting profile")
    transition_path = root / "migrations/048-manifest-capability-profile-schema.json"
    if not transition_path.is_file():
        fail("manifest capability-profile schema transition is missing")
    transition = json.loads(transition_path.read_text(encoding="utf-8")).get(
        "schemaTransition", {}
    )
    if transition != {
        "catalogVersion": meridian.CAPABILITY_CATALOG_VERSION,
        "fromProtocolVersion": meridian.LEGACY_PROTOCOL_VERSION,
        "legacyWorkflowModeField": "mode",
        "toProtocolVersion": meridian.PROTOCOL_VERSION,
        "workflowModeField": "workflowMode",
    }:
        fail("manifest capability-profile schema transition does not match the parser")


def check_migrations(root: Path = ROOT) -> None:
    migration_paths = sorted((root / "migrations").glob("[0-9][0-9][0-9]-*.json"))
    if not migration_paths:
        fail("no framework migrations are defined")
    previous_to = None
    for index, path in enumerate(migration_paths, start=1):
        data = json.loads(path.read_text(encoding="utf-8"))
        expected_prefix = f"{index:03d}-"
        required = ("id", "from", "to", "description", "managedPaths", "verification")
        if not path.name.startswith(expected_prefix) or not str(data.get("id", "")).startswith(expected_prefix):
            fail(f"migration sequence is invalid: {path.relative_to(root)}")
        if any(key not in data for key in required):
            fail(f"migration is incomplete: {path.relative_to(root)}")
        if previous_to is not None and data["from"] != previous_to:
            fail(f"migration versions are not contiguous: {path.relative_to(root)}")
        previous_to = data["to"]
    current_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    # A CLI-only release bumps VERSION without a migration, so the last
    # migration may lag behind VERSION but must never be ahead of it.
    if meridian.version_key(previous_to) > meridian.version_key(current_version):
        fail("a migration must never target a version ahead of the current release")
    for error in meridian.validate_capability_moves(root, "governed-sdd"):
        fail(f"invalid capability move: {error}")


RELEASE_FIELDS = (
    "version",
    "releaseDate",
    "gitTag",
    "protocolVersion",
    "workflowBaselineVersion",
    "baselineChanged",
    "migrations",
)


def check_releases(root: Path = ROOT) -> None:
    current_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    release_dir = root / "releases"
    paths = list(release_dir.glob("*.json")) if release_dir.is_dir() else []
    # Numeric order, so 1.1.10 follows 1.1.9; duplicates cannot occur per filename.
    paths.sort(key=lambda path: meridian.version_key(re.split(r"[-+]", path.stem)[0]))
    if not any(path.stem == current_version for path in paths):
        fail(f"releases/{current_version}.json is missing for the current VERSION")
    migration_targets = {}
    for path in (root / "migrations").glob("[0-9][0-9][0-9]-*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        migration_targets[str(data.get("id", path.stem))] = str(data["to"])
    records = []
    for path in paths:
        relative = path.relative_to(root)
        data = json.loads(path.read_text(encoding="utf-8"))
        if set(data) != set(RELEASE_FIELDS):
            fail(f"{relative}: fields must be exactly {', '.join(RELEASE_FIELDS)}")
        if data["version"] != path.stem:
            fail(f"{relative}: version {data['version']!r} does not match the filename")
        if not re.fullmatch(r"\d+\.\d+\.\d+", str(data["version"])):
            fail(f"{relative}: version must not carry a prerelease or build suffix")
        migrations = data["migrations"]
        if not isinstance(migrations, list):
            fail(f"{relative}: migrations must be a list")
        if data["baselineChanged"] is not bool(migrations):
            fail(f"{relative}: baselineChanged must be true iff migrations is non-empty")
        for migration_id in migrations:
            if migration_targets.get(migration_id) != data["workflowBaselineVersion"]:
                fail(
                    f"{relative}: migration {migration_id!r} does not target "
                    "workflowBaselineVersion"
                )
        records.append(data)
    versions = [meridian.version_key(record["version"]) for record in records]
    if any(a >= b for a, b in zip(versions, versions[1:])):
        fail("release versions are not monotonically increasing across files")
    latest = max(records, key=lambda record: meridian.version_key(record["version"]))
    try:
        expected_baseline = meridian.latest_migration_to(root, latest["version"])
    except meridian.MeridianError as error:
        fail(f"cannot derive workflowBaselineVersion: {error}")
    if latest["workflowBaselineVersion"] != expected_baseline:
        fail(
            f"releases/{latest['version']}.json workflowBaselineVersion does not match "
            f"the migration-derived baseline {expected_baseline}"
        )


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
    retired = meridian.retired_capability_ids(root)
    for relative, markers in recorded.items():
        current_file = current.get(relative, {})
        for capability in markers:
            if capability not in current_file and capability not in retired:
                fail(f"{relative}: recorded capability={capability} baseline no longer present in the template")


# Tracked records identify checkouts and worktrees by names or paths relative
# to a root, so they resolve on every machine. Absolute home-directory paths
# exist only at runtime. Files listed here are frozen exceptions; none today.
MACHINE_PATH_ALLOWED_FILES: frozenset[str] = frozenset()
MACHINE_PATH_PATTERN = re.compile(
    r"/Users/[A-Za-z0-9_.-]+/"
    r"|/home/[A-Za-z0-9_.-]+/"
    r"|[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_.-]+[\\/]"
)


def check_no_machine_paths(
    root: Path = ROOT, allowed: frozenset[str] = MACHINE_PATH_ALLOWED_FILES
) -> None:
    listed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if listed.returncode != 0:
        fail("cannot list tracked files to check for machine-specific paths")
    for name in listed.stdout.decode("utf-8").split("\0"):
        path = root / name
        if not name or name in allowed or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if MACHINE_PATH_PATTERN.search(line):
                fail(f"machine-specific absolute path in {name}:{number}")


def main() -> None:
    if "--write-marker-baselines" in sys.argv[1:]:
        write_marker_baselines()
        print(f"Wrote {MARKER_BASELINE_PATH.relative_to(ROOT)}.")
        return
    check_required_files()
    check_language_policy()
    check_governed_review_worktree_contract()
    check_json()
    check_plugin_version()
    check_capability_catalog()
    check_migrations()
    check_releases()
    check_bash()
    check_local_markdown_links()
    check_capability_marker_baselines()
    check_no_machine_paths()
    print("Meridian repository checks passed.")


if __name__ == "__main__":
    main()
