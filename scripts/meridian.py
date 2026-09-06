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


def capability_requirements(framework_root: Path) -> dict[str, tuple[int, str]]:
    """Map capability id -> (required version, the migration id that requires it).

    Built from every migration record that declares a `capability` field. When
    more than one migration touches the same capability, the highest declared
    `capabilityVersion` wins — that is the version currently required.
    """
    requirements: dict[str, tuple[int, str]] = {}
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        capability = data.get("capability")
        if not capability:
            continue
        version = int(data["capabilityVersion"])
        current = requirements.get(capability)
        if current is None or version > current[0]:
            requirements[capability] = (version, str(data["id"]))
    return requirements


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


def capability_ids_for_file(framework_root: Path, target: Path) -> list[str]:
    """Capability ids of every migration that declares one and manages `target`."""
    ids = []
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        capability = data.get("capability")
        if capability and str(target) in data.get("managedPaths", []):
            ids.append(capability)
    return ids


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
    question for this audit).
    """
    if mode != "governed-sdd":
        return []
    results: list[tuple[str, str]] = []
    for item in managed_files(framework_root, mode):
        local = project_root / item.target
        if not local.is_file():
            continue
        local_text = local.read_text(encoding="utf-8")
        for capability, version_text in CAPABILITY_MARKER.findall(local_text):
            version = int(version_text)
            local_block = extract_marker_block(local_text, capability, version)
            template_text = item.source.read_text(encoding="utf-8")
            template_block = extract_marker_block(template_text, capability, version)
            if template_block is None:
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


def run_audit(project_root: Path, framework_root: Path, mode: str) -> int:
    results = audit_capability_markers(project_root, framework_root, mode)
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
            "Read the local LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md,",
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
            "Read the local LANGUAGE_POLICY.md, PROJECT_WORKFLOW.md, AGENTS.md, CLAUDE.md,",
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
            capability_ids = capability_ids_for_file(framework_root, item.target)
            local_text = local.read_text(encoding="utf-8")
            satisfied_here = capability_ids and all(
                (find_capability_marker_version(local_text, capability_id) or 0) >= requirements[capability_id][0]
                for capability_id in capability_ids
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
        for item in plan:
            local = project_root / item.file.target
            if item.action == "replace" or item.action == "add":
                local.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item.file.source, local)
            elif item.action == "merge":
                _, merged = merge_clean(local, baseline_root / item.file.target, item.file.source)
                local.write_bytes(merged)

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

    arguments = parser.parse_args()
    framework_root = arguments.framework_root.resolve()
    project_root = arguments.project.resolve()
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
