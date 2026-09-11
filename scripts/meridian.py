#!/usr/bin/env python3
"""Versioned, deterministic upgrades for Meridian-generated projects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


MANIFEST_PATH = Path(".meridian/manifest.json")
BASELINES_PATH = Path(".meridian/baselines")
ADOPTION_REVIEW_PATH = Path(".meridian/adoption-review.md")
PROTOCOL_VERSION = 1
ADOPTION_VERDICTS = ("APPROVE", "CHANGES_REQUESTED", "BLOCKED")
ADOPTION_RETRY_LIMIT = 2
CAPABILITY_MARKER = re.compile(r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->")
MARKED_BLOCK = re.compile(
    r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->\n?.*?<!-- MERIDIAN:END -->",
    re.DOTALL,
)


class MeridianError(RuntimeError):
    """Raised when an upgrade cannot be safely planned or applied."""


@dataclass(frozen=True)
class ManagedFile:
    source: Path
    target: Path


@dataclass(frozen=True)
class PlanItem:
    file: ManagedFile
    action: str
    detail: str


@dataclass(frozen=True)
class Capability:
    migration: str
    present: bool
    evidence: str


@dataclass(frozen=True)
class ReviewRecord:
    verdict: str
    attempt: int
    unchecked: int


@dataclass(frozen=True)
class AdoptionState:
    action: str
    missing: list[Capability]
    review: "ReviewRecord | None"
    reason: str


@dataclass(frozen=True)
class ProjectLocations:
    queue: Path
    task_roots: tuple[Path, ...]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_version(framework_root: Path) -> str:
    version_file = framework_root / "VERSION"
    if not version_file.is_file():
        raise MeridianError(f"framework VERSION file is missing: {version_file}")
    return version_file.read_text(encoding="utf-8").strip()


def version_key(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError as error:
        raise MeridianError(f"invalid framework version: {value}") from error


def managed_files_for_workflow(workflow: Path, mode: str) -> list[ManagedFile]:
    if not workflow.is_dir():
        raise MeridianError(f"workflow template is missing: {workflow}")

    paths = [Path("PROJECT_WORKFLOW.md"), Path("AGENTS.md"), Path("CLAUDE.md")]
    if mode == "governed-sdd":
        paths.extend(
            [
                Path("LANGUAGE_POLICY.md"),
                Path("tasks/TASK_BLUEPRINT.md"),
                *[
                    Path("docs") / item.name
                    for item in sorted((workflow / "docs").glob("*.md"))
                ],
            ]
        )

    result = []
    for target in paths:
        source = workflow / target
        if not source.is_file():
            raise MeridianError(f"managed template is missing: {source}")
        result.append(ManagedFile(source=source, target=target))
    return result


def managed_files(framework_root: Path, mode: str) -> list[ManagedFile]:
    return managed_files_for_workflow(
        framework_root / "templates" / "workflows" / mode, mode
    )


def load_manifest(project_root: Path) -> dict[str, object]:
    manifest_path = project_root / MANIFEST_PATH
    if not manifest_path.is_file():
        raise MeridianError(
            "project is not locked; run `meridian lock --project <path> --mode <mode>` first"
        )
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"invalid manifest: {manifest_path}") from error


def write_manifest(project_root: Path, manifest: dict[str, object]) -> None:
    destination = project_root / MANIFEST_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def migration_ids(framework_root: Path, installed_version: str, target_version: str) -> list[str]:
    result = []
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if version_key(str(data["to"])) > version_key(installed_version) and version_key(
            str(data["to"])
        ) <= version_key(target_version):
            result.append(str(data["id"]))
    return result


def migration_record_paths(framework_root: Path, migration_ids_to_find: list[str]) -> list[Path]:
    records = []
    wanted = set(migration_ids_to_find)
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(data["id"]) in wanted:
            records.append(path)
    if len(records) != len(wanted):
        raise MeridianError("a requested migration record is missing from the framework source")
    return records


def migration_capability_entries(data: dict[str, object]) -> list[tuple[str, int]]:
    """A migration record's declared (capability, capabilityVersion) pairs.

    Most migrations declare at most one, via the singular `capability` /
    `capabilityVersion` fields. A migration introducing several independent,
    pre-existing capabilities at once (a marker-retrofit pass over one file's
    several sections, for example) may instead declare a `capabilities` list
    of `{"capability": ..., "capabilityVersion": ...}` objects, so it doesn't
    need one near-duplicate migration record per capability.
    """
    entries = []
    capability = data.get("capability")
    if capability:
        entries.append((str(capability), int(data["capabilityVersion"])))
    for entry in data.get("capabilities", []):
        entries.append((str(entry["capability"]), int(entry["capabilityVersion"])))
    return entries


def migration_capability_removals(data: dict[str, object]) -> list[tuple[str, int, str | None]]:
    """A migration record's declared (capability, capabilityVersion, supersededBy)
    retirements — the mirror of `migration_capability_entries` for task 007's
    retirement path. `supersededBy` is an optional pointer, named in reports
    only, to the capability that now covers the same rule; nothing writes it
    into a managed file (see tasks/007-capability-retirement-path.md — a slot
    left behind inside a merge target is exactly the tension task 014 flagged
    as out of scope)."""
    return [
        (str(entry["capability"]), int(entry["capabilityVersion"]), entry.get("supersededBy"))
        for entry in data.get("removes", [])
    ]


def capability_requirements(framework_root: Path) -> dict[str, tuple[int, str]]:
    """Map capability id -> (required version, the migration id that requires it).

    Built from every migration record's declared capability entries (see
    `migration_capability_entries`), processed in migration order (the glob
    is already sorted by the zero-padded numeric filename prefix, the same
    order `migration_ids` and `check_migrations` assume is contiguous). When
    more than one migration touches the same capability, the highest
    declared `capabilityVersion` wins. A migration's `removes` entries then
    drop that capability from the requirements entirely — no version of it
    is required — unless a *later* migration reintroduces it, which
    naturally wins back by virtue of running after the removal in sequence.
    Without this, `capability_presence_map` would report a correctly retired
    capability as MISSING on every project that removed it exactly as asked.
    """
    requirements: dict[str, tuple[int, str]] = {}
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for capability, version in migration_capability_entries(data):
            current = requirements.get(capability)
            if current is None or version > current[0]:
                requirements[capability] = (version, str(data["id"]))
        for capability, _version, _superseded_by in migration_capability_removals(data):
            requirements.pop(capability, None)
    return requirements


def retired_capability_ids(framework_root: Path) -> set[str]:
    """Every capability id ever declared `removes` by a migration, regardless
    of whether a later migration reintroduced it. Used to distinguish a
    legitimate, migration-declared removal from an unexplained one — see
    `check_capability_marker_baselines` in check_repository.py, which must
    not fail merely because a retired capability's marker is gone from the
    framework's own current templates.
    """
    ids: set[str] = set()
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for capability, _version, _superseded_by in migration_capability_removals(data):
            ids.add(capability)
    return ids


def pending_capability_removals(
    framework_root: Path, migration_ids_to_find: list[str]
) -> list[tuple[str, int, str | None, list[str]]]:
    """(capability, version, supersededBy, managedPaths) for every retirement
    declared by the specific migrations about to be applied in one upgrade
    run (not every removal in framework history — that scope belongs to
    `retired_capability_ids`). `managedPaths` scopes which files an upgrade
    should attempt to remove the marker from, the same field migration
    records already use for the additive case.
    """
    result: list[tuple[str, int, str | None, list[str]]] = []
    wanted = set(migration_ids_to_find)
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(data["id"]) not in wanted:
            continue
        managed_paths = [str(p) for p in data.get("managedPaths", [])]
        for capability, version, superseded_by in migration_capability_removals(data):
            result.append((capability, version, superseded_by, managed_paths))
    return result


def removals_for_managed_file(
    framework_root: Path, migration_ids_to_find: list[str], target: Path
) -> list[tuple[str, int, str | None]]:
    """(capability, version, supersededBy) triples a pending upgrade should
    retire from this one managed file — `pending_capability_removals`
    filtered to the entries whose migration declares this file among its
    `managedPaths`."""
    return [
        (capability, version, superseded_by)
        for capability, version, superseded_by, managed_paths in pending_capability_removals(
            framework_root, migration_ids_to_find
        )
        if str(target) in managed_paths
    ]


def find_capability_marker_version(text: str, capability: str) -> int | None:
    for marker_capability, version in CAPABILITY_MARKER.findall(text):
        if marker_capability == capability:
            return int(version)
    return None


# Pre-marker capabilities (001, 002) shipped as bare phrases before migration
# 006 introduced markers. A project adopted between their release and 006 is
# legitimately compliant but has no marker to find; without this fallback,
# every such already-adopted project would regress to fully MISSING. Each
# entry proves only that v1 was implemented — the version that predates
# markers entirely — never a later one.
LEGACY_CAPABILITY_EVIDENCE = {
    "review-remediation-record": lambda project_root, text: (
        (project_root / "docs/REVIEW_RECORD_TEMPLATE.md").is_file() and "Address review" in text
    ),
    "lifecycle-orchestration": lambda project_root, text: (
        (project_root / "docs/LIFECYCLE_ORCHESTRATION.md").is_file() and "Run lifecycle" in text
    ),
}


def capability_presence_map(
    project_root: Path, mode: str, framework_root: Path
) -> dict[str, tuple[bool, str]]:
    """capability id -> (present, evidence), by behavior rather than exact wording.

    A capability is present when the project carries a
    `<!-- MERIDIAN:BEGIN capability=<id> vN --> ... <!-- MERIDIAN:END -->`
    marker for it at or above the version the framework currently requires,
    found anywhere among the project's managed governed-SDD files. When no
    marker is found, a capability with a pre-marker legacy check
    (`LEGACY_CAPABILITY_EVIDENCE`) still counts as present at v1 — never
    higher, since that check cannot distinguish v1 from any later version.
    See migrations/CAPABILITY_MARKERS.md for why this replaced pure phrase
    matching without breaking every project adopted before markers existed.
    """
    if mode != "governed-sdd":
        return {}

    combined_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (project_root / item.target for item in managed_files(framework_root, mode))
        if path.is_file()
    )

    presence: dict[str, tuple[bool, str]] = {}
    for capability_id, (required_version, _migration_id) in capability_requirements(framework_root).items():
        found_version = find_capability_marker_version(combined_text, capability_id)
        if found_version is not None:
            if found_version < required_version:
                presence[capability_id] = (
                    False,
                    f"marker present at v{found_version}, but v{required_version} is required",
                )
            else:
                presence[capability_id] = (
                    True,
                    f"marker present at v{found_version} (>= required v{required_version})",
                )
        else:
            legacy_check = LEGACY_CAPABILITY_EVIDENCE.get(capability_id)
            legacy_present = legacy_check is not None and legacy_check(project_root, combined_text)
            if legacy_present and required_version <= 1:
                presence[capability_id] = (True, "no marker found; legacy pre-marker evidence confirms v1")
            elif legacy_present:
                presence[capability_id] = (
                    False,
                    "no marker found; legacy pre-marker evidence only confirms v1, but "
                    f"v{required_version} is required",
                )
            else:
                presence[capability_id] = (
                    False,
                    f"no MERIDIAN:BEGIN capability={capability_id} marker found",
                )
    return presence


def capability_ids_in_template(template: Path) -> list[str]:
    """Capability ids whose marker actually appears in this template file.

    `managedPaths` on a migration record lists every file that migration's
    diff touches, which is not the same as "every file that must carry that
    migration's capability marker" — a migration can mention or reference a
    capability in several files while only marking it in one (see
    `migrations/011-whole-file-baseline-capabilities.json`, where each of its
    four capabilities belongs to a different one of its four managed paths).
    The template's own marker set is the ground truth for what a project's
    copy of this file must contain to be verified, and it is the same source
    `audit_capability_markers` already checks against.
    """
    if not template.is_file():
        return []
    text = template.read_text(encoding="utf-8")
    return [capability for capability, _version in CAPABILITY_MARKER.findall(text)]


def extract_marker_block(text: str, capability: str, version: int) -> str | None:
    """The exact bracketed content of one capability+version marker occurrence.

    Returns None if that specific version's marker is not present in `text`
    (a different version, or no marker at all, are both "not present" here).
    The marker may sit on its own line (a whole-section wrap) or inline mid-
    sentence (a single clause inside a larger numbered step); both are legal.
    """
    pattern = re.compile(
        rf"<!-- MERIDIAN:BEGIN capability={re.escape(capability)} v{version} -->\n?(.*?)"
        r"<!-- MERIDIAN:END -->",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1) if match else None


def extract_marked_block(text: str, capability: str, version: int) -> str | None:
    """Return one complete protected marker block, delimiters included."""
    pattern = re.compile(
        rf"<!-- MERIDIAN:BEGIN capability={re.escape(capability)} v{version} -->\n?(.*?)"
        r"<!-- MERIDIAN:END -->",
        re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else None


def marker_pairs(text: str) -> list[tuple[str, int]]:
    return [(capability, int(version)) for capability, version in CAPABILITY_MARKER.findall(text)]


def append_only_new_markers(local_text: str, base_text: str, template_text: str) -> str | None:
    """Reconcile newly introduced or superseded marker blocks into a customized
    local file, without touching any other project-owned text.

    A three-way line merge cannot recognize a protected block that a project has
    moved elsewhere in a file. This narrowly handles two safe cases, distinguished
    by capability *name* rather than by `(name, version)` pair — comparing pairs
    alone cannot tell a version bump from an unrelated new capability, since the
    bumped pair is absent from both the local and base pair sets exactly like a
    genuinely new one would be:

    - **Added**: the template introduces a capability the local file does not
      carry at all, and the base never carried it either. Its block is
      appended at the end, as before.
    - **Superseded**: the template raises a capability's version, and the
      local file's block for the *old* version still matches the base
      byte-for-byte (the project never edited it). The new version's block
      replaces the old one in place, preserving all surrounding text — never
      appended alongside it, where a stale rule would sit in the position an
      agent actually reads while the fix sits inert at the end of the file.

    Any other case returns None so the caller falls through to a manual
    conflict instead of guessing: a capability whose local block was edited
    from the base, a capability the base carried but the local file no longer
    does (a deliberate removal, not a merge target), or a local file that
    already carries more than one version of the same capability (itself the
    symptom of this defect; do not compound it, let `meridian audit` surface
    it for manual reconciliation instead).
    """
    base_pairs = set(marker_pairs(base_text))
    local_pairs = marker_pairs(local_text)
    template_pairs = marker_pairs(template_text)

    local_names = [capability for capability, _version in local_pairs]
    if len(local_names) != len(set(local_names)):
        return None

    local_by_name = dict(local_pairs)
    to_append: list[tuple[str, int]] = []
    to_supersede: list[tuple[str, int, int]] = []
    for capability, new_version in template_pairs:
        old_version = local_by_name.get(capability)
        if old_version is None:
            if (capability, new_version) in base_pairs:
                return None
            to_append.append((capability, new_version))
        elif old_version < new_version:
            to_supersede.append((capability, old_version, new_version))
        elif old_version == new_version:
            if extract_marker_block(local_text, capability, old_version) != extract_marker_block(
                template_text, capability, new_version
            ):
                return None
        # old_version > new_version: local is already ahead; leave it alone.

    if not to_append and not to_supersede:
        return None

    result = local_text
    for capability, old_version, new_version in to_supersede:
        base_block = extract_marker_block(base_text, capability, old_version)
        local_block = extract_marker_block(result, capability, old_version)
        if base_block is None or local_block != base_block:
            return None
        old_marked = extract_marked_block(result, capability, old_version)
        new_marked = extract_marked_block(template_text, capability, new_version)
        if old_marked is None or new_marked is None:
            return None
        result = result.replace(old_marked, new_marked, 1)

    if to_append:
        new_blocks = []
        for capability, version in to_append:
            block = extract_marked_block(template_text, capability, version)
            if block is None:
                return None
            content = extract_marker_block(template_text, capability, version)
            # A project can have manually adopted the exact new rule before a
            # later framework release wraps it in a marker. Promote that one
            # durable occurrence in place rather than appending a duplicate.
            if content and content not in base_text and result.count(content) == 1:
                result = result.replace(content, block, 1)
            else:
                new_blocks.append(block)
        if new_blocks:
            result = result.rstrip() + "\n\n" + "\n\n".join(new_blocks) + "\n"

    return result


def is_agents_pointer(text: str) -> bool:
    """Recognize a project-owned CLAUDE.md that deliberately delegates to AGENTS.

    This narrow signature keeps the exception explicit: a short Claude file is
    not enough. It must name AGENTS as authoritative and explicitly say that
    Meridian markers live there once, which makes the duplicate-context tradeoff
    durable and reviewable.
    """
    return (
        "`AGENTS.md`, which is authoritative" in text
        and "Every Meridian capability marker" in text
        and "lives in `AGENTS.md`, once" in text
        and "Keep this file a pointer" in text
        and not marker_pairs(text)
    )


def agents_pointer_satisfies_claude(
    project_root: Path, framework_root: Path, mode: str, claude_template_text: str, claude_local_text: str
) -> bool:
    """A pointer is safe only when AGENTS carries every shared Claude marker."""
    if not is_agents_pointer(claude_local_text):
        return False
    agent_local = project_root / "AGENTS.md"
    agent_template = framework_root / "templates" / "workflows" / mode / "AGENTS.md"
    if not agent_local.is_file() or not agent_template.is_file():
        return False
    local_text = agent_local.read_text(encoding="utf-8")
    template_text = agent_template.read_text(encoding="utf-8")
    pairs = marker_pairs(claude_template_text)
    return bool(pairs) and all(
        extract_marker_block(local_text, capability, version)
        == extract_marker_block(template_text, capability, version)
        for capability, version in pairs
    )


def reflowed_marker_normalization(local_text: str, template_text: str) -> str | None:
    """Canonicalize protected prose whose only drift is hard line wrapping.

    Fenced blocks must remain byte-identical. Outside fences, paragraph
    boundaries and non-whitespace characters must be identical; this permits a
    formatter's line wrap, not a content edit.
    """
    def paragraphs(value: str) -> list[str] | None:
        chunks = re.split(r"(```.*?```)", value, flags=re.DOTALL)
        result: list[str] = []
        for index, chunk in enumerate(chunks):
            if index % 2:
                result.append("FENCE:" + chunk)
                continue
            result.extend(
                " ".join(paragraph.split())
                for paragraph in re.split(r"\n\s*\n", chunk)
                if paragraph.strip()
            )
        return result

    local_pairs = dict(marker_pairs(local_text))
    template_pairs = dict(marker_pairs(template_text))
    if local_pairs != template_pairs:
        return None
    result = local_text
    changed = False
    for capability, version in marker_pairs(template_text):
        local_content = extract_marker_block(result, capability, version)
        template_content = extract_marker_block(template_text, capability, version)
        if local_content == template_content:
            continue
        if local_content is None or template_content is None or paragraphs(local_content) != paragraphs(template_content):
            return None
        local_marked = extract_marked_block(result, capability, version)
        template_marked = extract_marked_block(template_text, capability, version)
        if local_marked is None or template_marked is None or result.count(local_marked) != 1:
            return None
        result = result.replace(local_marked, template_marked, 1)
        changed = True
    return result if changed else None


def remove_retired_markers(
    local_text: str, base_text: str, removals: list[tuple[str, int]]
) -> str | None:
    """Delete each retired capability's marker block from a customized local
    file — task 007's retirement path, the mirror of `append_only_new_markers`'s
    supersession case. Safe only when the local block still matches the
    project's own locked baseline for that capability+version byte-for-byte
    (unmodified since the project last upgraded): the same "replace in place
    only when it still matches the base" rule that case already applies,
    reused here for "remove" instead of "replace."

    Idempotent by design: a capability already absent locally (never present,
    or already removed by hand) is skipped, not an error, so retiring the
    same capability twice — or upgrading a project that already lacks it —
    never fails. Returns the input unchanged when no listed capability was
    found to remove, so a caller that only wants to know whether removal
    actually did anything can compare the result to `local_text`.

    Refuses (returns `None`) the moment a targeted block is present locally
    but no longer matches the base: a local edit under a marker this upgrade
    is about to delete, which must be reconciled by hand rather than
    silently discarded along with the block. Also refuses when the exact
    same block text occurs more than once in the file — `str.replace` is
    content-addressed, not position-addressed, and would otherwise delete
    only the first occurrence and silently leave the second (the duplicate-
    paste case `audit_duplicate_headings` exists to catch), a partial
    mutation this function's contract promises never to produce.
    """
    result = local_text
    changed = False
    for capability, version in removals:
        local_block = extract_marked_block(result, capability, version)
        if local_block is None:
            continue
        if result.count(local_block) > 1:
            return None
        base_block = extract_marked_block(base_text, capability, version)
        if base_block is None or local_block != base_block:
            return None
        start = result.index(local_block)
        end = start + len(local_block)
        before, after = result[:start], result[end:]
        # Collapse the blank-line run the deletion leaves behind, bounded to
        # a small window right at the splice point so a run of blank lines
        # anywhere else in the file — this project's own, unrelated to this
        # removal — is never touched.
        boundary = re.sub(r"\n{3,}", "\n\n", before[-4:] + after[:4])
        result = before[:-4] + boundary + after[4:]
        changed = True
    return result if changed else local_text


def retired_capability_versions(framework_root: Path) -> set[tuple[str, int]]:
    """Every exact (capability, version) pair ever declared `removes` by a
    migration, regardless of which files its `managedPaths` named. Used by
    `audit_capability_markers` to tell "stale, upgrade hasn't run yet" apart
    from "retired, and this marker should already be gone" — the latter
    reported `FAIL` rather than `SKIP`, since `meridian upgrade`'s own
    retirement path only ever touches the specific files a migration lists,
    so a marker in a file that migration's `managedPaths` omitted would
    otherwise sit as an invisible `SKIP` forever.
    """
    pairs: set[tuple[str, int]] = set()
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for capability, version, _superseded_by in migration_capability_removals(data):
            pairs.add((capability, version))
    return pairs


def audit_capability_markers(
    project_root: Path, framework_root: Path, mode: str
) -> list[tuple[str, str]]:
    """Phase 4 of migrations/CAPABILITY_MARKERS.md: protected-region integrity.

    For every capability marker found in a project's managed files, compare
    its exact bracketed content against the framework's own current template
    for that same file — not a project-wide search, since two files can
    carry different canonical text for the same capability (a workflow
    section in AGENTS.md is not the same text as a template file's body).
    `PASS` means unmodified; `FAIL` means the protected text was edited
    outside `meridian upgrade`; `SKIP` means the project's marker version
    predates what the current template carries, so there is nothing current
    to verify against yet (a staleness question for `upgrade`, not a drift
    question for this audit). Also reports `FAIL` when a single file carries
    more than one version of the same capability — the symptom left behind
    when a version bump was appended instead of replacing the version it
    superseded, so an already-damaged project is found instead of left to
    accumulate a growing set of contradictory pairs.
    """
    if mode != "governed-sdd":
        return []
    retired_versions = retired_capability_versions(framework_root)
    results: list[tuple[str, str]] = []
    for item in managed_files(framework_root, mode):
        local = project_root / item.target
        if not local.is_file():
            continue
        local_text = local.read_text(encoding="utf-8")
        local_pairs = marker_pairs(local_text)
        versions_by_name: dict[str, list[int]] = {}
        for capability, version in local_pairs:
            versions_by_name.setdefault(capability, []).append(version)
        for capability, versions in versions_by_name.items():
            if len(versions) > 1:
                results.append(
                    (
                        "FAIL",
                        f"{item.target}: capability={capability} carries {len(versions)} versions "
                        f"({', '.join(f'v{v}' for v in sorted(versions))}) in the same file — a "
                        "superseded marker was left in place instead of replaced; reconcile by hand",
                    )
                )
        for capability, version_text in CAPABILITY_MARKER.findall(local_text):
            version = int(version_text)
            local_block = extract_marker_block(local_text, capability, version)
            template_text = item.source.read_text(encoding="utf-8")
            template_block = extract_marker_block(template_text, capability, version)
            if template_block is None and (capability, version) in retired_versions:
                results.append(
                    (
                        "FAIL",
                        f"{item.target}: capability={capability} v{version} is retired but still "
                        "present here; run `meridian upgrade`, or reconcile by hand if this file was "
                        "outside the retiring migration's `managedPaths`",
                    )
                )
            elif template_block is None:
                results.append(
                    (
                        "SKIP",
                        f"{item.target}: capability={capability} v{version} — the current framework "
                        "template has no matching version to verify against here (likely stale; "
                        "run `meridian upgrade` first)",
                    )
                )
            elif local_block == template_block:
                results.append(
                    ("PASS", f"{item.target}: capability={capability} v{version} matches the released text")
                )
            else:
                results.append(
                    (
                        "FAIL",
                        f"{item.target}: capability={capability} v{version} — protected content does not "
                        "match the released text for this version; possible unauthorized edit",
                    )
                )
    return sorted(results, key=lambda pair: pair[1])


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def marker_headings(text: str) -> list[tuple[str, int, str | None]]:
    """(capability, version, nearest preceding heading text) for every marker
    in `text`. `None` when a marker appears before any heading in the file.
    """
    headings = [(match.start(), match.group(2).strip()) for match in HEADING.finditer(text)]
    result: list[tuple[str, int, str | None]] = []
    for match in CAPABILITY_MARKER.finditer(text):
        capability, version = match.group(1), int(match.group(2))
        heading = None
        for offset, title in headings:
            if offset <= match.start():
                heading = title
            else:
                break
        result.append((capability, int(version), heading))
    return result


def audit_duplicate_headings(project_root: Path, framework_root: Path, mode: str) -> list[tuple[str, str]]:
    """Task 007's duplication-detection half: flag a capability whose marker
    sits under more than one distinct heading *within the same managed file*
    — the mechanical signature of an accidental duplicate paste, or a
    section split in two without updating the marker placement.

    Deliberately scoped to one file at a time, not across a project's whole
    managed-files set: the same capability legitimately appears under
    different heading names in different documents by design (for example
    `ci-verified-validation` under "Code Review and Integration Prompt" in
    `docs/CODE_REVIEW_PROMPT.md` and under "Completion Report" in
    `docs/COMPLETION_REPORT_TEMPLATE.md` — one canonical rule, several
    consuming documents, not a drifted duplicate). A cross-file heuristic
    was tried against these templates and produced five false positives on
    exactly that intentional pattern before this scope was chosen. This does
    not (and cannot) catch a *paraphrased* duplicate with no shared marker at
    all, such as the reviewer-integrator-identity triplication that
    motivated this task — that is invisible to any mechanical check and
    remains a human review concern; this only catches the structural case a
    marker can see.
    """
    if mode != "governed-sdd":
        return []
    results: list[tuple[str, str]] = []
    for item in managed_files(framework_root, mode):
        local = project_root / item.target
        if not local.is_file():
            continue
        by_capability: dict[str, set[str]] = {}
        for capability, _version, heading in marker_headings(local.read_text(encoding="utf-8")):
            if heading is not None:
                by_capability.setdefault(capability, set()).add(heading)
        for capability, headings in sorted(by_capability.items()):
            if len(headings) > 1:
                results.append(
                    (
                        "FAIL",
                        f"{item.target}: capability={capability} appears under {len(headings)} "
                        f"distinct headings ({', '.join(sorted(headings))}) in this file — merge "
                        "into one canonical location, or retire the duplicate via a migration's "
                        "`removes`/`supersededBy`",
                    )
                )
    return results


def run_audit(project_root: Path, framework_root: Path, mode: str) -> int:
    results = audit_capability_markers(project_root, framework_root, mode)
    results += audit_duplicate_headings(project_root, framework_root, mode)
    results = sorted(results, key=lambda pair: pair[1])
    if not results:
        print("No capability markers found to audit.")
        return 0
    for status, message in results:
        print(f"{status:4} {message}")
    failures = sum(1 for status, _ in results if status == "FAIL")
    if failures:
        print(f"BLOCKED: {failures} protected-region integrity failure(s).")
        return 2
    return 0


def detect_capabilities(project_root: Path, mode: str, framework_root: Path) -> list[Capability]:
    if mode != "governed-sdd":
        return []
    requirements = capability_requirements(framework_root)
    presence = capability_presence_map(project_root, mode, framework_root)
    return [
        Capability(migration_id, *presence[capability_id])
        for capability_id, (_required_version, migration_id) in sorted(requirements.items())
    ]


def parse_adoption_review(project_root: Path) -> "ReviewRecord | None":
    path = project_root / ADOPTION_REVIEW_PATH
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    verdict_match = re.search(r"^Verdict:\s*(\S+)\s*$", text, re.MULTILINE)
    attempt_match = re.search(r"^Attempt:\s*(\d+)\s*$", text, re.MULTILINE)
    if not verdict_match or verdict_match.group(1) not in ADOPTION_VERDICTS or not attempt_match:
        raise MeridianError(
            f"adoption review record is missing a machine-readable Verdict/Attempt header: {path}"
        )
    unchecked = len(re.findall(r"^\s*-\s*\[ \]", text, re.MULTILINE))
    return ReviewRecord(verdict=verdict_match.group(1), attempt=int(attempt_match.group(1)), unchecked=unchecked)


def compute_adoption_state(project_root: Path, mode: str, framework_root: Path) -> AdoptionState:
    if mode != "governed-sdd":
        raise MeridianError(
            "assisted adoption tracks capabilities only for governed-sdd mode; "
            "use `meridian adopt --mode lean-delivery --from <version> --check` instead"
        )
    capabilities = detect_capabilities(project_root, mode, framework_root)
    missing = [capability for capability in capabilities if not capability.present]
    review = parse_adoption_review(project_root)

    if review is not None and review.verdict == "CHANGES_REQUESTED" and review.attempt >= ADOPTION_RETRY_LIMIT:
        return AdoptionState(
            "BLOCKED",
            missing,
            review,
            f"two consecutive CHANGES_REQUESTED verdicts (attempt {review.attempt}); "
            f"resolve {project_root / ADOPTION_REVIEW_PATH} manually before retrying",
        )
    if missing:
        if review is not None and review.verdict == "CHANGES_REQUESTED":
            return AdoptionState("ADDRESS_REVIEW", missing, review, "unresolved findings in the adoption review record")
        return AdoptionState("IMPLEMENT_MIGRATION", missing, review, "missing framework capabilities")
    if review is None:
        return AdoptionState(
            "REVIEW_MIGRATION", missing, review, "capabilities detected as present; independent review has not run yet"
        )
    if review.verdict == "CHANGES_REQUESTED":
        return AdoptionState(
            "ADDRESS_REVIEW", missing, review, "reviewer requested changes despite capability detection"
        )
    if review.verdict == "APPROVE":
        if review.unchecked:
            return AdoptionState(
                "BLOCKED", missing, review, "approved adoption review record still has unchecked findings"
            )
        return AdoptionState("FINALIZE", missing, review, "review approved; ready to finalize")
    return AdoptionState("BLOCKED", missing, review, f"unexpected verdict in adoption review record: {review.verdict}")


def detect_mode(project_root: Path) -> str:
    workflow = project_root / "PROJECT_WORKFLOW.md"
    if not workflow.is_file():
        raise MeridianError(
            "cannot detect workflow mode: PROJECT_WORKFLOW.md is missing; pass --mode explicitly"
        )
    text = workflow.read_text(encoding="utf-8")
    is_governed = "GOVERNED_SDD" in text
    is_lean = "LEAN_DELIVERY" in text
    if is_governed and is_lean:
        raise MeridianError(
            "cannot detect workflow mode: PROJECT_WORKFLOW.md mentions both mode locks; pass --mode explicitly"
        )
    if is_governed:
        return "governed-sdd"
    if is_lean:
        return "lean-delivery"
    raise MeridianError(
        "cannot detect workflow mode: PROJECT_WORKFLOW.md has no recognized mode lock; pass --mode explicitly"
    )


def detect_source_version(framework_root: Path, mode: str) -> str:
    baselines_root = framework_root / "release-baselines"
    candidates = sorted(
        path.name
        for path in baselines_root.iterdir()
        if path.is_dir() and (path / "templates" / "workflows" / mode).is_dir()
    ) if baselines_root.is_dir() else []
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise MeridianError(
            f"cannot detect source version: no packaged baseline for {mode}; pass --from explicitly"
        )
    raise MeridianError(
        "cannot detect source version: multiple packaged baselines are available "
        f"({', '.join(candidates)}); pass --from explicitly"
    )


def assisted_implementer_prompt(
    project_root: Path,
    framework_root: Path,
    mode: str,
    source_version: str,
    missing: list[Capability],
) -> str:
    migration_ids_to_find = [capability.migration for capability in missing]
    migration_ids = ", ".join(migration_ids_to_find)
    records = migration_record_paths(framework_root, migration_ids_to_find)
    deltas = [
        f"- {data['id']}: {data['delta']}"
        for data in (json.loads(path.read_text(encoding="utf-8")) for path in records)
        if data.get("delta")
    ]
    executable = framework_root / "bin" / "meridian"
    return "\n".join(
        [
            "Perform the capability-aware Meridian adoption migration for this project.",
            "",
            "Read the local LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md,",
            "and docs/CONTEXT_BUDGET_POLICY.md before editing.",
            "Read these framework migration records before planning the change:",
            *[f"- {path}" for path in records],
            f"- {framework_root / 'migrations/ASSISTED_ADOPTION.md'}",
            f"The project is adopting from Meridian {source_version} in {mode} mode.",
            f"Implement only these missing framework capabilities: {migration_ids}.",
            *(
                [
                    "",
                    "For a capability already partially present at an older version, apply only this",
                    "delta — do not rewrite the capability from scratch:",
                    *deltas,
                ]
                if deltas
                else []
            ),
            "",
            "Use the project's established paths, terminology, governance, validation, and Git rules.",
            "Preserve every capability already detected as present. Do not replace local workflow",
            f"documents with generic Meridian templates and do not run `{executable} adopt --apply`.",
            f"If {project_root / '.meridian/adoption-review.md'} exists, read it and address only its",
            "unchecked findings; otherwise implement the missing capability named above.",
            "Create a dedicated migration branch, then run only the project checks whose surface the",
            "migration actually touches — this migration edits documentation/policy text, so skip the",
            "project's full build/test/lint suite and state that explicitly instead of running it",
            "defensively. Commit only this bounded migration. Do not review your own work and do not",
            "run `finalize-adoption`.",
            "",
            "Report the changed files, validation evidence, and the named migration IDs for a fresh",
            "independent reviewer. After an APPROVE verdict, run:",
            f"{executable} finalize-adoption --project {project_root} --mode {mode}",
        ]
    )


def assisted_reviewer_prompt(
    project_root: Path,
    framework_root: Path,
    mode: str,
    source_version: str,
    missing: list[Capability],
) -> str:
    migration_ids_to_find = [capability.migration for capability in missing]
    records = migration_record_paths(framework_root, migration_ids_to_find)
    executable = framework_root / "bin" / "meridian"
    review_path = project_root / ADOPTION_REVIEW_PATH
    if missing:
        scope_line = "Review only the missing capabilities named by the adoption plan."
    else:
        scope_line = (
            "No capability is reported missing; independently confirm that detection is correct "
            "and that no prior migration attempt is incomplete."
        )
    return "\n".join(
        [
            "Independently review the completed capability-aware Meridian adoption migration.",
            "",
            "This reviewer session must be fresh and must not have implemented the migration.",
            "Read the local LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md,",
            "docs/CONTEXT_BUDGET_POLICY.md, the exact migration diff, and these records:",
            *[f"- {path}" for path in records],
            f"- {framework_root / 'migrations/ASSISTED_ADOPTION.md'}",
            f"The project is adopting from Meridian {source_version} in {mode} mode.",
            "",
            scope_line,
            "Confirm that existing review-remediation behavior and local project workflow",
            "customizations remain intact. Verify the migration record's criteria and that no generic",
            "template replacement or unrelated workflow change is included. Verify validation evidence",
            "is scoped to the actual diff surface: a documentation/policy-only migration should report",
            "the project's full build/test/lint suite as explicitly skipped, not run defensively; flag",
            "it as a finding if disproportionate validation output was run and presented as evidence, or",
            "if a command that should have run for the actual diff was skipped instead. Do not edit",
            "implementation artifacts or repair findings during review.",
            "",
            f"Write your verdict as a machine-readable record at {review_path} with this exact header",
            "shape (increment Attempt by one from any prior record; use 0 if none exists):",
            "Verdict: APPROVE | CHANGES_REQUESTED | BLOCKED",
            "Attempt: <n>",
            "then a `## Findings` list using `- [ ]` for each open finding (leave empty, or check every",
            "item `- [x]`, only when the verdict is APPROVE). Commit only that review record.",
            "",
            "After APPROVE with zero unchecked findings only, register the deterministic framework",
            "baseline with:",
            f"{executable} finalize-adoption --project {project_root} --mode {mode}",
            "Then review the resulting manifest and baseline snapshot diff and commit it with the",
            "approved migration. On CHANGES_REQUESTED or BLOCKED, do not finalize adoption.",
        ]
    )


def assisted_orchestrator_prompt(
    project_root: Path, framework_root: Path, mode: str, source_version: str
) -> str:
    executable = framework_root / "bin" / "meridian"
    command = (
        f"{executable} adopt --project {project_root} --mode {mode} "
        f"--from {source_version} --assisted --check"
    )
    return "\n".join(
        [
            "Coordinate a capability-aware Meridian adoption as a stateless loop. Do not implement or",
            "review the migration yourself, and never copy an implementer's or reviewer's chat context",
            "into the next session — only the fields below cross a session boundary.",
            "",
            f"Repeat: run `{command}` and read its first `NEXT_ACTION <value>` line plus its exit code.",
            "",
            "NEXT_ACTION IMPLEMENT_MIGRATION or ADDRESS_REVIEW (exit 3): start a fresh implementer",
            "session (a distinct Task-tool subagent when this host supports one, otherwise a separate",
            "chat) and send it the exact text between IMPLEMENTER_PROMPT_BEGIN and IMPLEMENTER_PROMPT_END",
            f"(or `{executable} adopt ... --assisted --check --emit implementer` to fetch just that block).",
            "Wait for it to report completion, then loop.",
            "",
            "NEXT_ACTION REVIEW_MIGRATION or ADDRESS_REVIEW's next pass (exit 3): start a fresh reviewer",
            "session that did not implement the migration and send it the text between",
            "REVIEWER_PROMPT_BEGIN and REVIEWER_PROMPT_END (or `--emit reviewer`). Wait for it to commit",
            f"its verdict to {project_root / ADOPTION_REVIEW_PATH}, then loop.",
            "",
            "NEXT_ACTION FINALIZE (exit 0, READY_TO_FINALIZE): have the reviewer that approved the",
            "migration run the emitted absolute finalize-adoption command, inspect the manifest/baseline",
            "diff, and commit it together with the approved migration. Never run generic adopt --apply",
            "for an assisted adoption.",
            "",
            "Exit 2 (BLOCKED): stop immediately and report the exact printed reason — this covers two",
            "consecutive CHANGES_REQUESTED verdicts and any malformed review record. A developer must",
            "resolve the underlying issue before an orchestrator restarts the loop.",
            "",
            "The command's own state (capability detection plus the adoption review record) is the only",
            "handoff interface; do not track progress in the chat.",
        ]
    )


def print_assisted_adoption_plan(
    project_root: Path,
    framework_root: Path,
    mode: str,
    source_version: str,
    emit: str | None = None,
) -> int:
    state = compute_adoption_state(project_root, mode, framework_root)
    snapshot_workflow = (
        framework_root
        / "release-baselines"
        / source_version
        / "templates"
        / "workflows"
        / mode
    )
    if not snapshot_workflow.is_dir():
        raise MeridianError(
            f"no packaged baseline for {mode} {source_version}; adoption cannot infer it safely"
        )

    if emit is not None:
        if emit == "orchestrator":
            print(assisted_orchestrator_prompt(project_root, framework_root, mode, source_version))
        elif emit == "implementer":
            if state.action not in ("IMPLEMENT_MIGRATION", "ADDRESS_REVIEW"):
                raise MeridianError(f"no implementer prompt applies to the current state: {state.action}")
            print(
                assisted_implementer_prompt(
                    project_root, framework_root, mode, source_version, state.missing
                )
            )
        elif emit == "reviewer":
            if state.action not in ("REVIEW_MIGRATION", "ADDRESS_REVIEW"):
                raise MeridianError(f"no reviewer prompt applies to the current state: {state.action}")
            print(
                assisted_reviewer_prompt(
                    project_root, framework_root, mode, source_version, state.missing
                )
            )
        return 0 if state.action == "FINALIZE" else (2 if state.action == "BLOCKED" else 3)

    target_version = read_version(framework_root)
    print(f"Assisted adoption {source_version} -> {target_version} ({mode})")
    capabilities = detect_capabilities(project_root, mode, framework_root)
    for capability in capabilities:
        capability_state = "PRESENT" if capability.present else "MISSING"
        print(f"CAPABILITY {capability_state:7} {capability.migration} — {capability.evidence}")

    if state.action == "BLOCKED":
        raise MeridianError(state.reason)

    if state.action in ("IMPLEMENT_MIGRATION", "ADDRESS_REVIEW"):
        print("AGENT_REQUIRED")
        for capability in state.missing:
            print(f"MIGRATION {capability.migration}")
        print(f"NEXT_ACTION {state.action}")
        if state.review is not None:
            print(f"ATTEMPT {state.review.attempt}")
        print("IMPLEMENTER_PROMPT_BEGIN")
        print(
            assisted_implementer_prompt(
                project_root, framework_root, mode, source_version, state.missing
            )
        )
        print("IMPLEMENTER_PROMPT_END")
        print("REVIEWER_PROMPT_BEGIN")
        print(
            assisted_reviewer_prompt(
                project_root, framework_root, mode, source_version, state.missing
            )
        )
        print("REVIEWER_PROMPT_END")
        print("ORCHESTRATOR_PROMPT_BEGIN")
        print(assisted_orchestrator_prompt(project_root, framework_root, mode, source_version))
        print("ORCHESTRATOR_PROMPT_END")
        print("No files were changed.")
        return 3

    if state.action == "REVIEW_MIGRATION":
        print("AGENT_REQUIRED")
        print(f"NEXT_ACTION {state.action}")
        print("REVIEWER_PROMPT_BEGIN")
        print(
            assisted_reviewer_prompt(
                project_root, framework_root, mode, source_version, state.missing
            )
        )
        print("REVIEWER_PROMPT_END")
        print("ORCHESTRATOR_PROMPT_BEGIN")
        print(assisted_orchestrator_prompt(project_root, framework_root, mode, source_version))
        print("ORCHESTRATOR_PROMPT_END")
        print("No files were changed.")
        return 3

    print("READY_TO_FINALIZE")
    print("NEXT_ACTION FINALIZE")
    print("No files were changed.")
    return 0


def copy_baseline(project_root: Path, framework_root: Path, mode: str, version: str) -> None:
    destination_root = project_root / BASELINES_PATH / version
    for item in managed_files(framework_root, mode):
        destination = destination_root / item.target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item.source, destination)


def prune_stale_baselines(project_root: Path, keep_version: str) -> None:
    """Remove every baseline snapshot except the one the manifest now points at.

    Only the baseline matching `manifest.frameworkVersion` is ever read again
    (see `plan_upgrade`); older snapshots are dead weight the moment an
    upgrade or adoption completes.
    """
    baselines_root = project_root / BASELINES_PATH
    if not baselines_root.is_dir():
        return
    for entry in baselines_root.iterdir():
        if entry.is_dir() and entry.name != keep_version:
            shutil.rmtree(entry)


def lock_project(project_root: Path, framework_root: Path, mode: str) -> None:
    version = read_version(framework_root)
    files = managed_files(framework_root, mode)
    missing = [str(item.target) for item in files if not (project_root / item.target).is_file()]
    if missing:
        raise MeridianError("project is missing managed files: " + ", ".join(missing))

    copy_baseline(project_root, framework_root, mode, version)
    manifest = {
        "frameworkVersion": version,
        "protocolVersion": PROTOCOL_VERSION,
        "mode": mode,
        "managedFiles": {str(item.target): sha256(item.source) for item in files},
        "appliedMigrations": migration_ids(framework_root, "0.0.0", version),
    }
    write_manifest(project_root, manifest)
    print(f"Locked {project_root} to Meridian {version} ({mode}).")


def merge_clean(local: Path, base: Path, incoming: Path) -> tuple[bool, bytes]:
    with tempfile.TemporaryDirectory(prefix="meridian-merge-") as directory:
        output = Path(directory) / "merged"
        process = subprocess.run(
            ["git", "merge-file", "-p", str(local), str(base), str(incoming)],
            check=False,
            capture_output=True,
        )
        # git merge-file returns the number of conflicts (not merely 1) for a
        # successful merge operation with conflict markers. Only 128+ signals
        # a command failure.
        if process.returncode >= 128:
            detail = process.stderr.decode("utf-8", errors="replace").strip()
            raise MeridianError(detail or "git merge-file failed")
        output.write_bytes(process.stdout)
        return process.returncode == 0, output.read_bytes()


def plan_from_baseline(
    project_root: Path,
    framework_root: Path,
    mode: str,
    installed_version: str,
    baseline_root: Path,
    applied_migrations: list[object],
) -> tuple[dict[str, object], list[PlanItem]]:
    target_version = read_version(framework_root)
    if version_key(target_version) < version_key(installed_version):
        raise MeridianError("framework source is older than the project lockfile")
    if not baseline_root.is_dir():
        raise MeridianError(f"baseline snapshot is missing: {baseline_root}")

    manifest: dict[str, object] = {
        "frameworkVersion": installed_version,
        "mode": mode,
        "appliedMigrations": applied_migrations,
    }

    requirements = capability_requirements(framework_root)
    applied = {str(migration) for migration in applied_migrations}
    pending_migrations = [
        migration
        for migration in migration_ids(framework_root, installed_version, target_version)
        if migration not in applied
    ]

    plan = []
    for item in managed_files(framework_root, mode):
        local = project_root / item.target
        base = baseline_root / item.target
        if not base.is_file():
            if local.exists():
                plan.append(PlanItem(item, "conflict", "managed baseline is missing"))
            else:
                plan.append(PlanItem(item, "add", "new managed file"))
            continue
        if not local.is_file():
            plan.append(PlanItem(item, "conflict", "local managed file is missing"))
            continue
        if sha256(item.source) == sha256(base):
            plan.append(PlanItem(item, "keep", "template unchanged"))
        elif sha256(local) == sha256(base):
            plan.append(PlanItem(item, "replace", "local file matches installed baseline"))
        elif sha256(local) == sha256(item.source):
            plan.append(PlanItem(item, "keep", "local file already matches target"))
        else:
            clean, _ = merge_clean(local, base, item.source)
            if clean:
                plan.append(PlanItem(item, "merge", "three-way merge"))
                continue
            local_text = local.read_text(encoding="utf-8")
            base_text = base.read_text(encoding="utf-8")
            template_text = item.source.read_text(encoding="utf-8")
            if item.target == Path("CLAUDE.md") and agents_pointer_satisfies_claude(
                project_root, framework_root, mode, template_text, local_text
            ):
                plan.append(
                    PlanItem(
                        item,
                        "pointer-verified",
                        "project declares CLAUDE.md as an AGENTS.md pointer; all shared markers are current in AGENTS.md",
                    )
                )
                continue
            capability_ids = capability_ids_in_template(item.source)
            marker_append = append_only_new_markers(local_text, base_text, template_text)
            if marker_append is not None:
                local_by_name = dict(marker_pairs(local_text))
                added = [
                    capability
                    for capability, version in marker_pairs(template_text)
                    if capability not in local_by_name
                ]
                superseded = [
                    f"{capability} v{local_by_name[capability]}->v{version}"
                    for capability, version in marker_pairs(template_text)
                    if capability in local_by_name and version > local_by_name[capability]
                ]
                detail = "three-way merge conflicted, but existing protected markers are intact; "
                parts = []
                if added:
                    parts.append(f"add new marker block(s) ({', '.join(added)})")
                if superseded:
                    parts.append(f"replace superseded block(s) in place ({', '.join(superseded)})")
                detail += " and ".join(parts) + " without touching other local text"
                plan.append(
                    PlanItem(
                        item,
                        "append-markers",
                        detail,
                    )
                )
                continue
            normalized_markers = reflowed_marker_normalization(local_text, template_text)
            if normalized_markers is not None:
                plan.append(
                    PlanItem(
                        item,
                        "normalize-markers",
                        "three-way merge conflicted, but protected marker content differs only by prose line wrapping; normalize to the current canonical block",
                    )
                )
                continue
            removals = removals_for_managed_file(framework_root, pending_migrations, item.target)
            retirement_conflict = False
            if removals:
                removal_pairs = [(capability, version) for capability, version, _superseded_by in removals]
                retired = remove_retired_markers(local_text, base_text, removal_pairs)
                if retired is not None and retired != local_text:
                    labels = [
                        f"{capability} -> {superseded_by}" if superseded_by else capability
                        for capability, _version, superseded_by in removals
                    ]
                    plan.append(
                        PlanItem(
                            item,
                            "retire-markers",
                            "three-way merge conflicted, but the retired capability block(s) "
                            f"({', '.join(labels)}) still matched the installed baseline and were "
                            "removed in place",
                        )
                    )
                    continue
                # A locally modified block awaiting retirement must never be
                # silently downgraded to VERIFIED below: `capability_ids`
                # comes from the *current* template, which by definition no
                # longer carries a capability this migration just retired, so
                # that check alone is blind to this exact conflict.
                retirement_conflict = retired is None
            satisfied_here = (
                not retirement_conflict
                and capability_ids
                and all(
                    extract_marker_block(local_text, capability_id, requirements[capability_id][0])
                    is not None
                    and extract_marker_block(local_text, capability_id, requirements[capability_id][0])
                    == extract_marker_block(template_text, capability_id, requirements[capability_id][0])
                    for capability_id in capability_ids
                )
            )
            if satisfied_here:
                plan.append(
                    PlanItem(
                        item,
                        "verified",
                        "three-way merge conflicted, but this file's own capability marker(s) "
                        f"({', '.join(sorted(capability_ids))}) already satisfy the required version — "
                        "left untouched",
                    )
                )
            else:
                plan.append(PlanItem(item, "conflict", "three-way merge"))
    return manifest, plan


def plan_upgrade(project_root: Path, framework_root: Path) -> tuple[dict[str, object], list[PlanItem]]:
    manifest = load_manifest(project_root)
    installed_version = str(manifest.get("frameworkVersion", ""))
    return plan_from_baseline(
        project_root,
        framework_root,
        str(manifest.get("mode", "")),
        installed_version,
        project_root / BASELINES_PATH / installed_version,
        list(manifest.get("appliedMigrations", [])),
    )


def print_plan(manifest: dict[str, object], framework_root: Path, plan: list[PlanItem]) -> None:
    target_version = read_version(framework_root)
    print(
        f"Meridian {manifest['frameworkVersion']} -> {target_version} "
        f"({manifest['mode']})"
    )
    applied = {str(item) for item in manifest.get("appliedMigrations", [])}
    pending = [
        migration
        for migration in migration_ids(
            framework_root, str(manifest["frameworkVersion"]), target_version
        )
        if migration not in applied
    ]
    for migration in pending:
        print(f"MIGRATION {migration}")
    for item in plan:
        print(f"{item.action.upper():8} {item.file.target} — {item.detail}")
    conflicts = sum(item.action == "conflict" for item in plan)
    if conflicts:
        print(f"BLOCKED: {conflicts} conflict(s); no files were changed.")


def apply_plan(
    project_root: Path,
    framework_root: Path,
    manifest: dict[str, object],
    plan: list[PlanItem],
    baseline_root: Path,
    owner_reconciled: bool = False,
) -> None:
    print_plan(manifest, framework_root, plan)
    conflicts = any(item.action == "conflict" for item in plan)
    if conflicts and not owner_reconciled:
        raise MeridianError("upgrade has conflicts")

    installed_version = str(manifest["frameworkVersion"])
    target_version = read_version(framework_root)
    if owner_reconciled:
        print(
            "Owner-reconciled upgrade: skipped automatic file changes for every managed "
            "file, trusting that local content was already brought to the target version "
            "by hand outside the three-way merge."
        )
    else:
        applied = {str(migration) for migration in manifest.get("appliedMigrations", [])}
        pending_migrations = [
            migration
            for migration in migration_ids(framework_root, installed_version, target_version)
            if migration not in applied
        ]
        for item in plan:
            local = project_root / item.file.target
            if item.action == "replace" or item.action == "add":
                local.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item.file.source, local)
            elif item.action == "merge":
                _, merged = merge_clean(local, baseline_root / item.file.target, item.file.source)
                local.write_bytes(merged)
            elif item.action == "append-markers":
                base = baseline_root / item.file.target
                appended = append_only_new_markers(
                    local.read_text(encoding="utf-8"),
                    base.read_text(encoding="utf-8"),
                    item.file.source.read_text(encoding="utf-8"),
                )
                if appended is None:
                    raise MeridianError(
                        f"marker-aware insertion is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(appended, encoding="utf-8")
            elif item.action == "normalize-markers":
                normalized = reflowed_marker_normalization(
                    local.read_text(encoding="utf-8"), item.file.source.read_text(encoding="utf-8")
                )
                if normalized is None:
                    raise MeridianError(
                        f"marker normalization is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(normalized, encoding="utf-8")
            elif item.action == "retire-markers":
                base = baseline_root / item.file.target
                removals = removals_for_managed_file(framework_root, pending_migrations, item.file.target)
                removal_pairs = [(capability, version) for capability, version, _superseded_by in removals]
                local_text = local.read_text(encoding="utf-8")
                retired = remove_retired_markers(local_text, base.read_text(encoding="utf-8"), removal_pairs)
                if retired is None or retired == local_text:
                    raise MeridianError(
                        f"marker retirement is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(retired, encoding="utf-8")

    copy_baseline(project_root, framework_root, str(manifest["mode"]), target_version)
    prune_stale_baselines(project_root, target_version)
    manifest["frameworkVersion"] = target_version
    manifest["protocolVersion"] = PROTOCOL_VERSION
    manifest["managedFiles"] = {
        str(item.target): sha256(item.source)
        for item in managed_files(framework_root, str(manifest["mode"]))
    }
    prior = {str(item) for item in manifest.get("appliedMigrations", [])}
    prior.update(migration_ids(framework_root, installed_version, target_version))
    manifest["appliedMigrations"] = sorted(prior)
    write_manifest(project_root, manifest)
    print("Upgrade applied. Review the diff, run project checks, then commit it.")


def apply_upgrade(project_root: Path, framework_root: Path, owner_reconciled: bool = False) -> None:
    manifest, plan = plan_upgrade(project_root, framework_root)
    apply_plan(
        project_root,
        framework_root,
        manifest,
        plan,
        project_root / BASELINES_PATH / str(manifest["frameworkVersion"]),
        owner_reconciled=owner_reconciled,
    )


def copy_adoption_baseline(
    project_root: Path, snapshot_workflow: Path, mode: str, version: str
) -> None:
    destination_root = project_root / BASELINES_PATH / version
    for item in managed_files_for_workflow(snapshot_workflow, mode):
        destination = destination_root / item.target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item.source, destination)


def adopt_project(
    project_root: Path, framework_root: Path, mode: str, source_version: str, apply: bool
) -> int:
    if (project_root / MANIFEST_PATH).exists():
        raise MeridianError("project already has a manifest; use `meridian upgrade` instead")
    snapshot_workflow = (
        framework_root
        / "release-baselines"
        / source_version
        / "templates"
        / "workflows"
        / mode
    )
    if not snapshot_workflow.is_dir():
        raise MeridianError(
            f"no packaged baseline for {mode} {source_version}; adoption cannot infer it safely"
        )
    baseline_root = project_root / BASELINES_PATH / source_version
    if baseline_root.exists():
        raise MeridianError(f"adoption baseline already exists: {baseline_root}")
    manifest, plan = plan_from_baseline(
        project_root,
        framework_root,
        mode,
        source_version,
        snapshot_workflow,
        [],
    )
    print_plan(manifest, framework_root, plan)
    if not apply:
        return 2 if any(item.action == "conflict" for item in plan) else 0
    if any(item.action == "conflict" for item in plan):
        raise MeridianError("adoption has conflicts")
    copy_adoption_baseline(project_root, snapshot_workflow, mode, source_version)
    apply_plan(project_root, framework_root, manifest, plan, baseline_root)
    return 0


def finalize_adoption(
    project_root: Path, framework_root: Path, mode: str, owner_accepted: bool = False
) -> None:
    if (project_root / MANIFEST_PATH).exists():
        raise MeridianError("project already has a manifest; use `meridian upgrade` instead")
    missing = [
        capability.migration
        for capability in detect_capabilities(project_root, mode, framework_root)
        if not capability.present
    ]
    if missing:
        raise MeridianError("adoption capabilities are still missing: " + ", ".join(missing))

    if mode == "governed-sdd" and not owner_accepted:
        review = parse_adoption_review(project_root)
        if review is None:
            raise MeridianError(
                "no independent review record found at "
                f"{project_root / ADOPTION_REVIEW_PATH}; run `meridian adopt --assisted --check` "
                "for the reviewer prompt, or pass --owner-accepted after personally reviewing it"
            )
        if review.verdict != "APPROVE" or review.unchecked:
            raise MeridianError(
                "adoption review record does not record an unconditional APPROVE "
                f"(verdict={review.verdict}, unchecked findings={review.unchecked})"
            )

    lock_project(project_root, framework_root, mode)
    if owner_accepted:
        print("Owner-accepted finalize: skipped the independent-review gate.")
    print("Adoption finalized. Review the migration diff and commit the project baseline.")


BUDGET_PATH = Path(".meridian/budget.json")
BUDGET_KINDS = ("diagnostic", "captures", "expansions", "investigations")
EVIDENCE_EVENT_KINDS = ("diagnostic", "captures", "expansions")
BUDGET_DEFAULT_CAPS = {"diagnostic": 3, "captures": 2, "expansions": 2, "investigations": 2}
BUDGET_FIELD_NAMES = {
    "diagnostic": "Diagnostic attempts",
    "captures": "Evidence captures",
    "expansions": "Context expansions",
    "investigations": "Investigation scope",
}


def load_budget_state(project_root: Path) -> dict[str, object]:
    path = project_root / BUDGET_PATH
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"invalid budget state: {path}") from error


def write_budget_state(project_root: Path, state: dict[str, object]) -> None:
    path = project_root / BUDGET_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_task_field(text: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip()


def profile_cap(project_root: Path, kind: str) -> int:
    """Read the project's declared budget default, retaining framework defaults
    only for pre-profile projects.

    The profile is prose by design, but each shipped default has a stable
    backticked field name followed by its numeric cap.  Keeping this lookup
    here prevents the CLI's default silently drifting from project policy.
    """
    profile = project_root / "docs" / "EXECUTION_EVIDENCE_PROFILE.md"
    if not profile.is_file():
        return BUDGET_DEFAULT_CAPS[kind]
    field = re.escape(BUDGET_FIELD_NAMES[kind])
    match = re.search(rf"`{field}`:\s*(\d+)", profile.read_text(encoding="utf-8"))
    return int(match.group(1)) if match else BUDGET_DEFAULT_CAPS[kind]


def profile_digest(project_root: Path) -> str:
    profile = project_root / "docs" / "EXECUTION_EVIDENCE_PROFILE.md"
    if not profile.is_file():
        raise MeridianError("execution contract BLOCKED: missing docs/EXECUTION_EVIDENCE_PROFILE.md")
    return hashlib.sha256(profile.read_bytes()).hexdigest()


def execution_contract(project_root: Path, task_id: str) -> str:
    """Render the profile-derived execution block placed in a task at design time."""
    task = find_task_file(project_root, task_id)
    text = task.read_text(encoding="utf-8")
    commands = ", ".join(validation_commands(text)) or "none"
    caps = ", ".join(f"{BUDGET_FIELD_NAMES[kind]}: {task_cap(project_root, text, kind)}" for kind in BUDGET_KINDS)
    return "\n".join((
        "## Execution contract — resolved",
        "",
        "- Profile source: `docs/EXECUTION_EVIDENCE_PROFILE.md`",
        f"- Profile revision: `sha256:{profile_digest(project_root)}`",
        f"- Budgets: {caps}",
        f"- Validation IDs: {commands}",
        "- Execution commands: `required via meridian execution`",
    ))


def contract_digest(text: str) -> str | None:
    match = re.search(r"^- Profile revision: `sha256:([0-9a-f]{64})`$", text, re.MULTILINE)
    return match.group(1) if match else None


def contract_requires_execution_commands(text: str) -> bool:
    return "- Execution commands: `required via meridian execution`" in text


def resolve_project_locations(project_root: Path) -> ProjectLocations:
    """Resolve project customizations declared after execution-assets.

    The same resolver backs the CLI and the hook, avoiding separate default
    paths for a project's queue and its nested task records.
    """
    workflow = project_root / "PROJECT_WORKFLOW.md"
    zone = ""
    if workflow.is_file():
        match = re.search(
            r"<!-- MERIDIAN:BEGIN capability=execution-assets .*?<!-- MERIDIAN:END -->\s*(.*?)(?=^## |\Z)",
            workflow.read_text(encoding="utf-8"), re.MULTILINE | re.DOTALL,
        )
        zone = match.group(1) if match else ""
    queue_matches = re.findall(r"`([^`]*queue[^`]*\.md)`", zone, re.IGNORECASE)
    queues = [Path(path) for path in dict.fromkeys(path for path in queue_matches if "archive" not in path.lower())]
    queue = queues[0] if len(queues) == 1 else Path("tasks/QUEUE.md")
    roots = [Path("tasks")]
    for raw in re.findall(r"task files live under\s+`?([^`\s<]+)(?:/<[^>]+>)?/?`?", zone, re.IGNORECASE):
        root = Path(raw.rstrip("/"))
        if root not in roots:
            roots.append(root)
    return ProjectLocations(queue=queue, task_roots=tuple(roots))


def task_cap(project_root: Path, text: str, kind: str) -> int:
    raw = read_task_field(text, BUDGET_FIELD_NAMES[kind])
    if raw and raw.isdigit():
        return int(raw)
    return profile_cap(project_root, kind)


def find_task_file(project_root: Path, task_id: str) -> Path:
    """Locate a task in either the framework default or a project-declared tree.

    The common `docs/tasks/<milestone>/<TASK-ID>.md` layout is deliberately
    supported without forcing a mature project to migrate its task archive.
    Ambiguity is an error: a budget attached to the wrong task is worse than
    no budget at all.
    """
    candidates: list[Path] = []
    for root in resolve_project_locations(project_root).task_roots:
        absolute = project_root / root
        candidates.append(absolute / f"{task_id}.md")
        if absolute.is_dir():
            # Review records deliberately share a task ID with their task, but
            # are not task contracts.  Do not let the conventional nested
            # review-record directory turn an otherwise unambiguous task into
            # an ambiguity.
            candidates.extend(
                path
                for path in absolute.rglob(f"{task_id}.md")
                if "reviews" not in path.relative_to(absolute).parts
            )
    existing = list(dict.fromkeys(path for path in candidates if path.is_file()))
    if len(existing) != 1:
        raise MeridianError(f"unknown task or ambiguous task path: {task_id}")
    return existing[0]


def resolve_budget_key(project_root: Path, state: dict[str, object], task_id: str) -> tuple[str, str]:
    """Return the qualified `<TASK-ID>:<attempt>` state key and the task file's
    text, bumping `state`'s attempt bookkeeping in place when the task file
    shows a fresh READY_FOR_REVIEW -> IN_PROGRESS transition (a new
    remediation attempt) since the last time this was resolved.
    """
    task_file = find_task_file(project_root, task_id)
    text = task_file.read_text(encoding="utf-8")
    status = read_task_field(text, "Status") or "UNKNOWN"
    meta = dict(state.get(task_id) or {"attempt": 1, "lastStatus": None})
    if meta.get("lastStatus") == "READY_FOR_REVIEW" and status == "IN_PROGRESS":
        meta["attempt"] = int(meta.get("attempt", 1)) + 1
    meta["lastStatus"] = status
    state[task_id] = meta
    return f"{task_id}:{meta['attempt']}", text


def budget_show(project_root: Path, task_id: str) -> str:
    state = load_budget_state(project_root)
    key, text = resolve_budget_key(project_root, state, task_id)
    write_budget_state(project_root, state)
    counters = state.get(key, {})
    parts = []
    for kind, label in (
        ("diagnostic", "Diagnostics"),
        ("captures", "Captures"),
        ("expansions", "Expansions"),
        ("investigations", "Investigations"),
    ):
        cap = task_cap(project_root, text, kind)
        if kind == "captures":
            scoped = sorted((key.removeprefix("captures:"), value) for key, value in counters.items() if key.startswith("captures:"))
            if scoped:
                parts.append(f"{label} " + ", ".join(f"{criterion} {int(count)}/{cap}" for criterion, count in scoped))
                continue
        parts.append(f"{label} {int(counters.get(kind, 0))}/{cap}")
    return " · ".join(parts)


def budget_spend(
    project_root: Path, task_id: str, kind: str, scope: str | None = None, amount: int = 1
) -> tuple[int, int]:
    if amount < 1:
        raise MeridianError("budget spend BLOCKED: amount must be at least 1")
    state = load_budget_state(project_root)
    key, text = resolve_budget_key(project_root, state, task_id)
    counters = dict(state.get(key, {}))
    counter_key = f"{kind}:{scope}" if kind == "captures" and scope else kind
    count = int(counters.get(counter_key, 0)) + amount
    counters[counter_key] = count
    state[key] = counters
    write_budget_state(project_root, state)
    cap = task_cap(project_root, text, kind)
    if count >= cap:
        raise MeridianError(
            f"{BUDGET_FIELD_NAMES[kind]} exhausted for {task_id} ({count}/{cap}); "
            "return BLOCKED, do not raise the cap"
        )
    return count, cap


PREFLIGHT_HEADINGS = ("Authority", "Expected code surface", "Validation")
HANDOFF_FIELDS = (
    "Files changed",
    "Validation",
    "Manual verification",
    "Acceptance criteria",
    "Budget usage",
    "Isolated exploration",
    "Blockers/deviations",
)
EXECUTION_EVIDENCE_PATH = Path(".meridian/execution-evidence.json")


def execution_preflight(project_root: Path, task_id: str) -> str:
    """Validate the minimum durable execution contract before implementation.

    This intentionally does not inspect a chat's reasoning setting: that is a
    host concern and is outside this command's authority.
    """
    task_file = find_task_file(project_root, task_id)
    text = task_file.read_text(encoding="utf-8")
    expected_digest = profile_digest(project_root)
    recorded_digest = contract_digest(text)
    if recorded_digest is None:
        raise MeridianError("execution preflight BLOCKED: task is missing a resolved execution contract")
    if recorded_digest != expected_digest:
        raise MeridianError("execution preflight BLOCKED: resolved execution contract is stale; re-resolve the task")
    if not contract_requires_execution_commands(text):
        raise MeridianError(
            "execution preflight BLOCKED: task execution contract predates the execution-command gate; "
            "run meridian execution reconcile <TASK-ID> --apply --project ."
        )
    missing = [heading for heading in PREFLIGHT_HEADINGS if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)]
    if missing:
        raise MeridianError(
            "execution preflight BLOCKED: task is missing " + ", ".join(f"## {heading}" for heading in missing)
        )
    status = read_task_field(text, "Status")
    if status not in ("QUEUED", "IN_PROGRESS"):
        raise MeridianError(f"execution preflight BLOCKED: {task_id} status is {status or 'missing'}")
    queue = project_root / resolve_project_locations(project_root).queue
    if queue.is_file():
        header = next((line for line in queue.read_text(encoding="utf-8").splitlines() if line.startswith("| Order |")), "")
        columns = [value.strip() for value in header.strip("|").split("|")]
        if "ID" in columns and "Status" in columns:
            for line in queue.read_text(encoding="utf-8").splitlines():
                if not re.match(r"^\|\s*\d+\s*\|", line):
                    continue
                values = [value.strip() for value in line.strip("|").split("|")]
                if len(values) == len(columns) and values[columns.index("ID")] == task_id:
                    queued_status = values[columns.index("Status")]
                    if queued_status != status:
                        raise MeridianError(
                            f"execution preflight BLOCKED: task status {status} disagrees with queue status {queued_status}"
                        )
                    break
    caps = ", ".join(
        f"{BUDGET_FIELD_NAMES[kind]}={task_cap(project_root, text, kind)}" for kind in BUDGET_KINDS
    )
    return f"Execution contract: {task_file.relative_to(project_root)} · {caps}"


def reconcile_execution_contract(project_root: Path, task_id: str, apply: bool) -> str:
    """Refresh only a nonterminal task's generated execution-contract block."""
    task_file = find_task_file(project_root, task_id)
    text = task_file.read_text(encoding="utf-8")
    status = read_task_field(text, "Status") or "missing"
    if status in ("ACCEPTED", "ANSWERED", "INCONCLUSIVE"):
        return f"Execution reconciliation skipped for terminal task {task_id} ({status})"
    if status not in ("QUEUED", "IN_PROGRESS"):
        raise MeridianError(f"execution reconcile BLOCKED: {task_id} status is {status}")
    generated = execution_contract(project_root, task_id)
    section = re.compile(
        r"^## Execution contract — resolved\s*$\n.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    replacement = generated + "\n\n"
    if section.search(text):
        reconciled = section.sub(replacement, text, count=1)
    elif re.search(r"^## Completion\s*$", text, re.MULTILINE):
        reconciled = re.sub(r"^## Completion\s*$", replacement + "## Completion", text, count=1, flags=re.MULTILINE)
    else:
        reconciled = text.rstrip() + "\n\n" + generated + "\n"
    if reconciled == text:
        return f"Execution reconciliation already current for {task_id}: {task_file.relative_to(project_root)}"
    if not apply:
        return f"Execution reconciliation required for {task_id}: {task_file.relative_to(project_root)} (rerun with --apply)"
    task_file.write_text(reconciled, encoding="utf-8")
    return f"Execution reconciliation applied for {task_id}: {task_file.relative_to(project_root)}"


def execution_entries(project_root: Path, task_id: str) -> list[dict[str, object]]:
    path = project_root / EXECUTION_EVIDENCE_PATH
    if not path.is_file():
        return []
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"invalid execution evidence state: {path}") from error
    entries = state.get(task_id, [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise MeridianError(f"invalid execution evidence entries for {task_id}: {path}")
    return entries


def verify_execution_evidence(project_root: Path, task_id: str, report_text: str) -> None:
    """Require report claims to be backed by durable, task-declared evidence."""
    task_text = find_task_file(project_root, task_id).read_text(encoding="utf-8")
    entries = execution_entries(project_root, task_id)
    commands = validation_commands(task_text)
    missing_validations = [
        command_id for command_id, command in commands.items()
        if not any(
            entry.get("id") == command_id
            and entry.get("command") == command
            and entry.get("exitStatus") == 0
            for entry in entries
        )
    ]
    if missing_validations:
        raise MeridianError(
            "handoff check BLOCKED: successful durable validation is missing for: "
            + ", ".join(missing_validations)
        )

    investigations = [entry for entry in entries if entry.get("kind") == "investigation"]
    reported = re.search(r"^- Isolated exploration:\s*(.+)$", report_text, re.MULTILINE)
    assert reported is not None  # HANDOFF_FIELDS has already checked its presence.
    value = reported.group(1).strip()
    if not investigations:
        if value.lower() != "none":
            raise MeridianError(
                "handoff check BLOCKED: report declares isolated exploration without a durable record"
            )
        return
    if value.lower() == "none":
        raise MeridianError(
            "handoff check BLOCKED: report says no isolated exploration but durable records exist"
        )
    missing_summaries = [
        str(entry.get("question", ""))
        for entry in investigations
        if str(entry.get("question", "")) not in report_text
        or str(entry.get("finding", "")) not in report_text
    ]
    if missing_summaries:
        raise MeridianError(
            "handoff check BLOCKED: report omits a recorded exploration question or finding: "
            + "; ".join(missing_summaries)
        )


def check_handoff(project_root: Path, task_id: str, report: Path) -> str:
    """Reject incomplete completion evidence before it can be used as a handoff."""
    if not report.is_file():
        raise MeridianError(f"handoff check BLOCKED: report is missing: {report}")
    text = report.read_text(encoding="utf-8")
    missing = [field for field in HANDOFF_FIELDS if not re.search(rf"^- {re.escape(field)}:\s*\S+", text, re.MULTILINE)]
    if missing:
        raise MeridianError("handoff check BLOCKED: missing required fields: " + ", ".join(missing))
    if f"Completion Report — {task_id}" not in text:
        raise MeridianError(f"handoff check BLOCKED: report does not identify {task_id}")
    verify_execution_evidence(project_root, task_id, text)
    return f"Handoff evidence complete for {task_id}: {report}"


def default_handoff_path(project_root: Path, task_id: str) -> Path:
    workflow = project_root / "PROJECT_WORKFLOW.md"
    if workflow.is_file():
        match = re.search(
            r"[Cc]ompletion handoffs live at `([^`]+)/<TASK-ID>\.md`",
            workflow.read_text(encoding="utf-8"),
        )
        if match:
            return project_root / match.group(1) / f"{task_id}.md"
    return project_root / "tasks" / "handoffs" / f"{task_id}.md"


def readiness_check(project_root: Path, task_id: str, report: Path) -> str:
    """Combine execution and handoff gates before a task enters review."""
    execution_preflight(project_root, task_id)
    check_handoff(project_root, task_id, report)
    return f"READY_FOR_REVIEW gate passed for {task_id}"


def validation_commands(text: str) -> dict[str, str]:
    """Read named, literal validation commands from one task's Validation block."""
    section = re.search(r"^## Validation\s*$\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if section is None:
        return {}
    commands: dict[str, str] = {}
    for match in re.finditer(r"^- `([^`]+)`: `([^`]+)`\s*$", section.group(1), re.MULTILINE):
        command_id, command = match.groups()
        commands[command_id] = command
    return commands


def record_validation(project_root: Path, task_id: str, command_id: str, command: str, status: int) -> None:
    path = project_root / EXECUTION_EVIDENCE_PATH
    state: dict[str, object] = {}
    if path.is_file():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MeridianError(f"invalid execution evidence state: {path}") from error
    entries = list(state.get(task_id, []))
    entries.append({"id": command_id, "command": command, "exitStatus": status})
    state[task_id] = entries
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_validation(project_root: Path, task_id: str, command_id: str) -> int:
    """Execute only the task-declared literal command and retain its outcome."""
    execution_preflight(project_root, task_id)
    text = find_task_file(project_root, task_id).read_text(encoding="utf-8")
    commands = validation_commands(text)
    if command_id not in commands:
        available = ", ".join(sorted(commands)) or "none"
        raise MeridianError(
            f"validation BLOCKED: {command_id!r} is not a declared validation ID for {task_id} (available: {available})"
        )
    command = commands[command_id]
    completed = subprocess.run(command, shell=True, executable="/bin/bash", cwd=project_root, check=False)
    record_validation(project_root, task_id, command_id, command, completed.returncode)
    print(f"Validation {task_id}/{command_id}: exit {completed.returncode}")
    return completed.returncode


def record_execution_event(
    project_root: Path,
    task_id: str,
    kind: str,
    gap: str,
    criterion: str | None,
    artifact: str | None,
) -> str:
    """Spend a semantic budget only alongside the evidence that justifies it."""
    if not gap.strip():
        raise MeridianError("execution evidence BLOCKED: --gap is required")
    if kind == "captures" and (not criterion or not artifact):
        raise MeridianError("execution evidence BLOCKED: captures require --criterion and --artifact")
    count, cap = budget_spend(project_root, task_id, kind, criterion if kind == "captures" else None)
    path = project_root / EXECUTION_EVIDENCE_PATH
    state: dict[str, object] = {}
    if path.is_file():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MeridianError(f"invalid execution evidence state: {path}") from error
    events = list(state.get(task_id, []))
    event: dict[str, object] = {"kind": kind, "gap": gap, "count": count, "cap": cap}
    if criterion:
        event["criterion"] = criterion
    if artifact:
        event["artifact"] = artifact
    events.append(event)
    state[task_id] = events
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f"Evidence {task_id}: {kind} {count}/{cap} recorded"


def record_investigation(
    project_root: Path,
    task_id: str,
    question: str,
    scope: int,
    sources: list[str],
    finding: str,
) -> str:
    """Record a bounded exploration without making a host or worker normative."""
    if not question.strip() or not finding.strip() or not sources:
        raise MeridianError("investigation BLOCKED: --question, --source, and --finding are required")
    execution_preflight(project_root, task_id)
    count, cap = budget_spend(project_root, task_id, "investigations", amount=scope)
    path = project_root / EXECUTION_EVIDENCE_PATH
    state: dict[str, object] = {}
    if path.is_file():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MeridianError(f"invalid execution evidence state: {path}") from error
    events = list(state.get(task_id, []))
    events.append({
        "kind": "investigation",
        "question": question,
        "scope": scope,
        "sources": sources,
        "finding": finding,
        "count": count,
        "cap": cap,
    })
    state[task_id] = events
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f"Investigation {task_id}: {count}/{cap} recorded"


# `CLAUDE.md` is Claude Code's own instructions file; it cannot be reduced to a
# bare pointer, since a Claude Code session never reads `AGENTS.md` itself. So
# each workflow's `CLAUDE.md` keeps a hand-authored preamble (title, pointer
# paragraph, any Claude-Code-specific sections) up to this anchor heading, and
# everything from the anchor onward — the actual shared rule content, capability
# markers included — is generated verbatim from `AGENTS.md`, which stays the
# single source of truth for that text. The anchor is matched by heading text,
# not position, per this repo's own role-scoped-agent-rules precedent: it must
# be a heading that both files currently carry.
CLAUDE_MD_SHARED_ANCHOR = {
    "governed-sdd": "## Code organization",
    "lean-delivery": "## Command triggers",
}


def generate_claude_md(mode: str, agents_text: str, existing_claude_text: str) -> str:
    anchor = CLAUDE_MD_SHARED_ANCHOR[mode]
    pattern = re.compile(rf"^{re.escape(anchor)}$", re.MULTILINE)
    agents_match = pattern.search(agents_text)
    if agents_match is None:
        raise MeridianError(f"AGENTS.md ({mode}) is missing the expected anchor heading {anchor!r}")
    claude_match = pattern.search(existing_claude_text)
    if claude_match is None:
        raise MeridianError(f"CLAUDE.md ({mode}) is missing the expected anchor heading {anchor!r}")
    preamble = existing_claude_text[: claude_match.start()]
    shared_body = agents_text[agents_match.start() :]

    # A capability marker's content is versioned; changing it without bumping
    # the version is exactly the defect this generator must never reproduce
    # (see tasks/014-generator-altered-protected-blocks.md). So the shared
    # body is copied from AGENTS.md everywhere *except* inside a marker: there,
    # CLAUDE.md's own existing block for that same capability+version wins
    # verbatim, byte for byte, if one is already present. A capability with no
    # prior block in CLAUDE.md (a brand-new marker) has nothing to preserve,
    # so it is copied from AGENTS.md like the rest of the shared body.
    def preserve_existing_marker(match: re.Match[str]) -> str:
        capability, version = match.group(1), int(match.group(2))
        existing_block = extract_marked_block(existing_claude_text, capability, version)
        return existing_block if existing_block is not None else match.group(0)

    shared_body = MARKED_BLOCK.sub(preserve_existing_marker, shared_body)
    return preamble + shared_body


def main() -> int:
    parser = argparse.ArgumentParser(prog="meridian")
    parser.add_argument(
        "--framework-root",
        type=Path,
        default=Path(os.environ.get("MERIDIAN_ROOT", Path(__file__).resolve().parents[1])),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    lock = subparsers.add_parser("lock", help="register a newly initialized project for deterministic upgrades")
    lock.add_argument("--project", type=Path, default=Path.cwd())
    lock.add_argument("--mode", choices=("lean-delivery", "governed-sdd"), required=True)

    upgrade = subparsers.add_parser("upgrade", help="plan or apply a framework upgrade")
    upgrade.add_argument("--project", type=Path, default=Path.cwd())
    group = upgrade.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--apply", action="store_true")
    upgrade.add_argument(
        "--owner-reconciled",
        action="store_true",
        help="register the target version and baseline without touching any managed file, "
        "for a project too customized for the automatic three-way merge whose developer has "
        "already reconciled every managed file by hand outside this command; --apply only",
    )

    adopt = subparsers.add_parser("adopt", help="migrate an untracked project from a packaged baseline")
    adopt.add_argument("--project", type=Path, default=Path.cwd())
    adopt.add_argument(
        "--mode",
        choices=("lean-delivery", "governed-sdd"),
        help="detected from the project's PROJECT_WORKFLOW.md mode lock when omitted",
    )
    adopt.add_argument(
        "--from",
        dest="source_version",
        help="detected when exactly one packaged baseline is available for the mode",
    )
    adopt_group = adopt.add_mutually_exclusive_group(required=True)
    adopt_group.add_argument("--check", action="store_true")
    adopt_group.add_argument("--apply", action="store_true")
    adopt.add_argument(
        "--assisted",
        action="store_true",
        help="produce a capability-aware plan for an agent instead of generic template merging",
    )
    adopt.add_argument(
        "--emit",
        choices=("implementer", "reviewer", "orchestrator"),
        help="print only the named prompt block, with --assisted --check, for a host or operator to relay directly",
    )

    finalize = subparsers.add_parser(
        "finalize-adoption",
        help="write a manifest after an assisted migration has been reviewed",
    )
    finalize.add_argument("--project", type=Path, default=Path.cwd())
    finalize.add_argument(
        "--mode",
        choices=("lean-delivery", "governed-sdd"),
        help="detected from the project's PROJECT_WORKFLOW.md mode lock when omitted",
    )
    finalize.add_argument(
        "--owner-accepted",
        action="store_true",
        help="skip the independent-review gate after the developer personally reviewed the migration, "
        "mirroring the `Accept <TASK-ID>` owner-acceptance path",
    )

    audit = subparsers.add_parser(
        "audit",
        help="verify protected capability-marker regions were not edited outside meridian upgrade",
    )
    audit.add_argument("--project", type=Path, default=Path.cwd())
    audit.add_argument(
        "--mode",
        choices=("lean-delivery", "governed-sdd"),
        help="detected from the project's PROJECT_WORKFLOW.md mode lock when omitted",
    )

    locations = subparsers.add_parser("locations", help="print resolved project queue and task locations")
    locations.add_argument("--project", type=Path, default=Path.cwd())
    locations.add_argument("--field", choices=("queue", "task-roots"))

    budget = subparsers.add_parser(
        "budget",
        help="track a governed-SDD task's diagnostic/evidence/context-expansion/investigation caps",
    )
    budget_sub = budget.add_subparsers(dest="budget_command", required=True)

    budget_show_parser = budget_sub.add_parser("show", help="print the active attempt's budget state")
    budget_show_parser.add_argument("task_id")
    budget_show_parser.add_argument("--project", type=Path, default=Path.cwd())

    budget_spend_parser = budget_sub.add_parser(
        "spend", help="record one diagnostic/evidence/context use and check the declared cap"
    )
    budget_spend_parser.add_argument("task_id")
    budget_spend_parser.add_argument("kind", choices=BUDGET_KINDS)
    budget_spend_parser.add_argument("--project", type=Path, default=Path.cwd())

    execution = subparsers.add_parser("execution", help="validate a governed task's durable execution evidence")
    execution_sub = execution.add_subparsers(dest="execution_command", required=True)
    preflight = execution_sub.add_parser("preflight", help="check the task contract before implementation")
    preflight.add_argument("task_id")
    preflight.add_argument("--project", type=Path, default=Path.cwd())
    contract = execution_sub.add_parser("contract", help="print the profile-resolved execution contract for a task")
    contract.add_argument("task_id")
    contract.add_argument("--project", type=Path, default=Path.cwd())
    reconcile = execution_sub.add_parser(
        "reconcile", help="refresh a nonterminal task's generated execution contract"
    )
    reconcile.add_argument("task_id")
    reconcile.add_argument("--apply", action="store_true")
    reconcile.add_argument("--project", type=Path, default=Path.cwd())
    handoff = execution_sub.add_parser("handoff-check", help="check a structured completion handoff")
    handoff.add_argument("task_id")
    handoff.add_argument("report", type=Path, nargs="?")
    handoff.add_argument("--project", type=Path, default=Path.cwd())
    ready = execution_sub.add_parser("ready-check", help="require preflight and complete handoff before review")
    ready.add_argument("task_id")
    ready.add_argument("report", type=Path, nargs="?")
    ready.add_argument("--project", type=Path, default=Path.cwd())
    validate = execution_sub.add_parser("validate", help="run one task-declared literal validation command")
    validate.add_argument("task_id")
    validate.add_argument("validation_id")
    validate.add_argument("--project", type=Path, default=Path.cwd())
    evidence = execution_sub.add_parser("evidence", help="record the gap and one budgeted diagnostic, capture, or expansion")
    evidence.add_argument("task_id")
    evidence.add_argument("kind", choices=EVIDENCE_EVENT_KINDS)
    evidence.add_argument("--gap", required=True)
    evidence.add_argument("--criterion")
    evidence.add_argument("--artifact")
    evidence.add_argument("--project", type=Path, default=Path.cwd())
    investigate = execution_sub.add_parser(
        "investigate", help="record a bounded, isolated exploration and its distilled finding"
    )
    investigate.add_argument("task_id")
    investigate.add_argument("--question", required=True)
    investigate.add_argument("--scope", required=True, type=int)
    investigate.add_argument("--source", action="append", required=True)
    investigate.add_argument("--finding", required=True)
    investigate.add_argument("--project", type=Path, default=Path.cwd())

    generate_claude = subparsers.add_parser(
        "generate-claude-md",
        help="regenerate a workflow template's CLAUDE.md shared body from its AGENTS.md (framework-internal)",
    )
    generate_claude.add_argument("--mode", choices=tuple(CLAUDE_MD_SHARED_ANCHOR), required=True)
    generate_group = generate_claude.add_mutually_exclusive_group(required=True)
    generate_group.add_argument("--check", action="store_true", help="exit non-zero if CLAUDE.md is stale")
    generate_group.add_argument("--write", action="store_true", help="regenerate CLAUDE.md in place")

    arguments = parser.parse_args()
    framework_root = arguments.framework_root.resolve()
    project_root = arguments.project.resolve() if hasattr(arguments, "project") else None
    try:
        if arguments.command == "lock":
            lock_project(project_root, framework_root, arguments.mode)
        elif arguments.command == "adopt":
            if arguments.emit and not (arguments.assisted and arguments.check):
                raise MeridianError("--emit requires --assisted --check")
            mode = arguments.mode or detect_mode(project_root)
            source_version = arguments.source_version or detect_source_version(framework_root, mode)
            if arguments.assisted:
                if arguments.apply:
                    raise MeridianError("assisted adoption has no --apply; implement and review the plan, then finalize-adoption")
                return print_assisted_adoption_plan(
                    project_root,
                    framework_root,
                    mode,
                    source_version,
                    arguments.emit,
                )
            return adopt_project(
                project_root,
                framework_root,
                mode,
                source_version,
                arguments.apply,
            )
        elif arguments.command == "finalize-adoption":
            mode = arguments.mode or detect_mode(project_root)
            finalize_adoption(project_root, framework_root, mode, arguments.owner_accepted)
        elif arguments.command == "audit":
            mode = arguments.mode or detect_mode(project_root)
            return run_audit(project_root, framework_root, mode)
        elif arguments.command == "locations":
            locations = resolve_project_locations(project_root)
            if arguments.field == "queue":
                print(locations.queue)
            elif arguments.field == "task-roots":
                print("\n".join(str(root) for root in locations.task_roots))
            else:
                print(json.dumps({"queue": str(locations.queue), "taskRoots": [str(root) for root in locations.task_roots]}))
        elif arguments.command == "budget":
            if arguments.budget_command == "show":
                print(budget_show(project_root, arguments.task_id))
            else:
                count, cap = budget_spend(project_root, arguments.task_id, arguments.kind)
                print(f"{arguments.task_id}: {arguments.kind} {count}/{cap}")
        elif arguments.command == "execution":
            if arguments.execution_command == "contract":
                print(execution_contract(project_root, arguments.task_id))
            elif arguments.execution_command == "reconcile":
                print(reconcile_execution_contract(project_root, arguments.task_id, arguments.apply))
            elif arguments.execution_command == "preflight":
                print(execution_preflight(project_root, arguments.task_id))
            elif arguments.execution_command == "validate":
                return run_validation(project_root, arguments.task_id, arguments.validation_id)
            elif arguments.execution_command == "evidence":
                print(record_execution_event(
                    project_root, arguments.task_id, arguments.kind, arguments.gap,
                    arguments.criterion, arguments.artifact,
                ))
            elif arguments.execution_command == "investigate":
                print(record_investigation(
                    project_root, arguments.task_id, arguments.question, arguments.scope,
                    arguments.source, arguments.finding,
                ))
            elif arguments.execution_command == "ready-check":
                print(readiness_check(project_root, arguments.task_id, arguments.report or default_handoff_path(project_root, arguments.task_id)))
            else:
                print(check_handoff(project_root, arguments.task_id, arguments.report or default_handoff_path(project_root, arguments.task_id)))
        elif arguments.command == "generate-claude-md":
            workflow = framework_root / "templates" / "workflows" / arguments.mode
            agents_path = workflow / "AGENTS.md"
            claude_path = workflow / "CLAUDE.md"
            agents_text = agents_path.read_text(encoding="utf-8")
            claude_text = claude_path.read_text(encoding="utf-8")
            generated = generate_claude_md(arguments.mode, agents_text, claude_text)
            if arguments.check:
                if generated == claude_text:
                    print(f"CLAUDE.md ({arguments.mode}) matches the generator's output.")
                else:
                    print(f"STALE {claude_path}: does not match AGENTS.md-generated output.", file=sys.stderr)
                    return 2
            else:
                claude_path.write_text(generated, encoding="utf-8")
                print(f"Regenerated {claude_path}.")
        elif arguments.check:
            if arguments.owner_reconciled:
                raise MeridianError("--owner-reconciled only applies to --apply")
            manifest, plan = plan_upgrade(project_root, framework_root)
            print_plan(manifest, framework_root, plan)
            if any(item.action == "conflict" for item in plan):
                return 2
        else:
            apply_upgrade(project_root, framework_root, arguments.owner_reconciled)
    except MeridianError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
