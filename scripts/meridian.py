#!/usr/bin/env python3
"""Versioned, deterministic upgrades for Meridian-generated projects."""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


# `bin/meridian` dispatches this file through runpy, which retains bin/ rather
# than scripts/ on sys.path. Host hook adapters live beside this entry point.
SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from console_workflow import latest_review_verdict  # noqa: E402 (needs SCRIPTS_ROOT on sys.path)


MANIFEST_PATH = Path(".meridian/manifest.json")
VALIDATION_EVIDENCE_SCHEMA_PATH = Path("schemas/validation-evidence-v1.schema.json")
VALIDATION_EXIT_PASSED = 0
VALIDATION_EXIT_PENDING = 1
VALIDATION_EXIT_FAILED = 2
CAPABILITY_CATALOG_VERSION = 1
CAPABILITY_CATALOG_PATH = Path("capabilities/catalog-v1.json")
BASELINES_PATH = Path(".meridian/baselines")
ADOPTION_REVIEW_PATH = Path(".meridian/adoption-review.md")
# Bump only when the manifest's shape or semantics change in a way that an
# older CLI cannot safely read. Add backward-compatible fields without a bump.
PROTOCOL_VERSION = 2
LEGACY_PROTOCOL_VERSION = 1
WORKFLOW_MODES = ("lean-delivery", "governed-sdd")
INSTALLATION_FORMS = ("managed-copy", "shared-source", "declaration-only")
INSTALLATION_STATES = ("INSTALLED", "MISSING", "DRIFTED", "NOT_APPLICABLE")
HOST_ACTIVATION_STATES = ("ENFORCED", "ADVISORY", "UNSUPPORTED", "UNVERIFIED", "NOT_APPLICABLE")
VERIFICATION_STATES = ("PASS", "ADVISORY", "UNVERIFIED", "NOT_APPLICABLE", "FAIL")
AUDIT_STATES = VERIFICATION_STATES
LATEST_RELEASE_URL = "https://api.github.com/repos/biagiolibe/meridian/releases/latest"
LATEST_RELEASE_TIMEOUT_SECONDS = 3.0
LATEST_RELEASE_RESPONSE_LIMIT = 1024 * 1024
SELF_CHECK_UPDATE_AVAILABLE = 10
SELF_CHECK_UNKNOWN = 11
# Protocol v2 introduces capability declarations but keeps them optional for
# legacy locked projects. A future protocol can make the declaration explicit
# by advancing this boundary without changing the compatibility result below.
CAPABILITY_DECLARATION_REQUIRED_PROTOCOL = 3
ADOPTION_VERDICTS = ("APPROVE", "CHANGES_REQUESTED", "BLOCKED")
ADOPTION_RETRY_LIMIT = 2
CAPABILITY_MARKER = re.compile(r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->")
MARKED_BLOCK = re.compile(
    r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->\n?.*?<!-- MERIDIAN:END -->",
    re.DOTALL,
)
ENTRY_ROUTER_PATH = Path("docs/workflows/ENTRY_ROUTER.md")
ENTRY_ROUTER_MAP_PATH = Path("docs/workflows/ENTRY_ROUTER_MAP.json")
ENTRY_ROUTER_OVERLAYS = {
    "AGENTS.md": Path("docs/workflows/ENTRY_ROUTER.AGENTS.overlay.md"),
    "CLAUDE.md": Path("docs/workflows/ENTRY_ROUTER.CLAUDE.overlay.md"),
}
ENTRY_ROUTER_BUDGET_BYTES = 2048
ENTRY_ROUTER_ROUTES = {
    "status-design": "docs/workflows/STATUS_DESIGN.md",
    "proceed": "docs/workflows/IMPLEMENTATION.md",
    "review": "docs/workflows/REVIEW.md",
    "address-review": "docs/workflows/REMEDIATION.md",
    "lifecycle-accept": "docs/workflows/LIFECYCLE.md",
    "audit": "docs/AUDIT_PROMPT_READ_ONLY.md",
}
ENTRY_ROUTER_SAFEGUARDS = {
    "status-design": ("status",),
    "proceed": ("git status --short", "validation"),
    "review": ("approve", "changes_requested"),
    "address-review": ("changes_requested", "in_progress"),
    "lifecycle-accept": ("lifecycle", "accept"),
    "audit": ("audit",),
}


class MeridianError(RuntimeError):
    """Raised when an upgrade cannot be safely planned or applied."""


CODEX_PERMISSION_PROFILE = "meridian-worktrees"
CODEX_MANAGED_BEGIN = "# MERIDIAN:BEGIN worktree-permissions v1"
CODEX_MANAGED_END = "# MERIDIAN:END worktree-permissions"
SAFE_PATH_COMPONENT = re.compile(r"[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?")
TASK_IDENTITY_PATH = Path(".meridian/task-identity.json")
WORKTREE_STATE_DIRECTORY = "meridian-worktrees"
INTEGRATION_LEASE_NAME = "meridian-integration.lock"
INTEGRATION_STATE_NAME = "meridian-integration.json"
STRUCTURED_TASK_ID = re.compile(
    r"M(?P<milestone>[1-9][0-9]*)-(?P<workstream>[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)-"
    r"(?P<ordinal>00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})"
)
NUMERIC_TASK_ALIAS = re.compile(r"(?:task-)?([0-9]+)", re.IGNORECASE)


@dataclass(frozen=True)
class RepositoryIdentity:
    remote_host: str
    owner: str
    repository: str


@dataclass(frozen=True)
class TaskIdentityPolicy:
    version: int
    mode: str


@dataclass(frozen=True)
class ResolvedTaskIdentity:
    policy_version: int
    mode: str
    kind: str
    canonical_id: str
    branch_name: str
    artifact_stem: str
    semantic_tuple: dict[str, object] | None
    task_path: Path
    queue_path: Path
    handoff_path: Path
    review_path: Path

    def budget_key(self, attempt: int) -> str:
        if attempt < 1:
            raise MeridianError("budget attempt must be positive")
        return f"{self.canonical_id}:{attempt}"

    def as_json(self, project_root: Path, attempt: int = 1) -> dict[str, object]:
        project_root = project_root.resolve()

        def display(path: Path) -> str:
            try:
                return str(path.relative_to(project_root))
            except ValueError:
                return str(path)

        return {
            "policy_version": self.policy_version,
            "mode": self.mode,
            "kind": self.kind,
            "canonical_id": self.canonical_id,
            "branch_name": self.branch_name,
            "artifact_stem": self.artifact_stem,
            "semantic_tuple": self.semantic_tuple,
            "task_path": display(self.task_path),
            "queue_path": display(self.queue_path),
            "handoff_path": display(self.handoff_path),
            "review_path": display(self.review_path),
            "budget_key": self.budget_key(attempt),
        }


@dataclass(frozen=True)
class ResolvedWorktreeRoot:
    path: Path
    source: str
    config_path: Path


@dataclass(frozen=True)
class CodexConfigurationPlan:
    status: str
    config_path: Path
    worktree_root: Path
    current_model: str
    proposed_text: str | None
    detail: str
    current_text: str | None = None


@dataclass(frozen=True)
class ClaudeConfigurationPlan:
    status: str
    settings_path: Path
    proposed_settings: dict[str, object] | None
    detail: str
    current_text: str | None = None


@dataclass(frozen=True)
class SetupPlan:
    resolution: ResolvedWorktreeRoot
    codex_config: Path
    directory_state: str
    codex_state: str
    codex_plan: CodexConfigurationPlan | None
    codex_detail: str
    claude_state: str
    claude_plan: ClaudeConfigurationPlan | None
    claude_detail: str
    config_action: str
    framework_root: Path
    skill_links: tuple[tuple[str, Path, str, str], ...]
    skill_links_state: str
    meridian_root_state: str
    changes: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSurface:
    path: str
    forms: tuple[str, ...]


@dataclass(frozen=True)
class CatalogCapability:
    capability_id: str
    version: int
    workflow_modes: tuple[str, ...]
    self_hosting_eligible: bool
    host_profiles: tuple[tuple[str, str], ...]
    installation_forms: tuple[str, ...]
    managed_surfaces: tuple[CatalogSurface, ...]
    evidence_requirements: tuple[tuple[str, tuple[str, ...]], ...]
    dependencies: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class CatalogProfile:
    profile_id: str
    version: int
    capabilities: tuple[tuple[str, int], ...]
    verification_probe: str
    host_probes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CapabilityCatalog:
    catalog_version: int
    capabilities: tuple[CatalogCapability, ...]
    profiles: tuple[CatalogProfile, ...]

    def capability(self, capability_id: str) -> CatalogCapability | None:
        return next(
            (item for item in self.capabilities if item.capability_id == capability_id),
            None,
        )

    def profile(self, profile_id: str) -> CatalogProfile | None:
        return next((item for item in self.profiles if item.profile_id == profile_id), None)


@dataclass(frozen=True)
class EvidenceSnapshot:
    state: str
    evidence: tuple[str, ...]
    not_applicable_rationale: str | None
    verified_at: str | None = None
    verifier_version: str | None = None


@dataclass(frozen=True)
class DeclaredSurface:
    path: str
    form: str


@dataclass(frozen=True)
class CapabilityDeclaration:
    capability_id: str
    required_version: int
    managed_surface: tuple[DeclaredSurface, ...]
    installation: EvidenceSnapshot
    host_activation: tuple[tuple[str, EvidenceSnapshot], ...]
    verification: EvidenceSnapshot


@dataclass(frozen=True)
class CapabilityProfileDeclaration:
    profile_id: str
    profile_version: int
    capabilities: tuple[CapabilityDeclaration, ...]


@dataclass(frozen=True)
class AuditResult:
    status: str
    identity: str
    detail: str


def _safe_component(value: str, label: str) -> str:
    """Return one unambiguous, portable path component."""
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    if not normalized or normalized in {".", ".."}:
        raise MeridianError(f"{label} is empty or traversing")
    if normalized != value.strip().lower() or not SAFE_PATH_COMPONENT.fullmatch(normalized):
        raise MeridianError(f"{label} is not an unambiguous portable path component: {value!r}")
    return normalized


def _normalized_local_repository_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    if not normalized:
        raise MeridianError("local repository name cannot be normalized safely")
    return normalized


def canonical_task_id(value: str) -> str:
    normalized = value.strip().lower()
    match = re.fullmatch(r"(?:task-)?([0-9]+)", normalized)
    if match is None:
        raise MeridianError(f"invalid task ID: {value!r}")
    number = match.group(1)
    if int(number) <= 0 or number != str(int(number)).zfill(len(number)):
        raise MeridianError(f"ambiguous task ID: {value!r}")
    return f"task-{number}"


def git_output(project_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise MeridianError(completed.stderr.strip() or f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def canonical_git_common_dir(project_root: Path) -> Path:
    common = Path(git_output(project_root, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = project_root / common
    return common.resolve()


def repository_identity(project_root: Path, remote_url: str | None = None) -> RepositoryIdentity:
    """Derive a repository-qualified namespace without machine-specific state."""
    if remote_url is None:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "config", "--get", "remote.origin.url"],
            text=True,
            capture_output=True,
            check=False,
        )
        remote_url = completed.stdout.strip() if completed.returncode == 0 else ""
    if remote_url:
        candidate = remote_url.strip()
        if "://" not in candidate and re.match(r"^[^/@:]+@[^/:]+:.+$", candidate):
            user_host, remote_path = candidate.split(":", 1)
            host = user_host.rsplit("@", 1)[-1]
            parts = [part for part in remote_path.strip("/").split("/") if part]
        else:
            parsed = urlparse(candidate)
            host = parsed.hostname or ""
            parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) >= 2 and host:
            repository = parts[-1][:-4] if parts[-1].endswith(".git") else parts[-1]
            owner_parts = [_safe_component(part, "remote owner") for part in parts[:-1]]
            if any("--" in part for part in owner_parts):
                raise MeridianError("remote owner contains an ambiguous namespace separator")
            owner = "--".join(owner_parts)
            return RepositoryIdentity(
                _safe_component(host, "remote host"),
                owner,
                _safe_component(repository, "repository name"),
            )

    common = canonical_git_common_dir(project_root)
    try:
        repository_name = git_output(project_root, "rev-parse", "--show-toplevel").split("/")[-1]
    except MeridianError:
        repository_name = project_root.resolve().name
    repository = _normalized_local_repository_name(repository_name)
    digest = hashlib.sha256(os.fsencode(common)).hexdigest()[:12]
    return RepositoryIdentity("local", "repositories", f"{repository}-{digest}")


def _task_worktree_path_for_identity(
    project_root: Path,
    worktree_root: Path,
    identity: ResolvedTaskIdentity,
) -> Path:
    root = worktree_root.expanduser().resolve()
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise MeridianError("worktree root must be a dedicated directory, not the filesystem root or home")
    repository = repository_identity(project_root)
    result = (
        root
        / repository.remote_host
        / repository.owner
        / repository.repository
        / identity.branch_name
    )
    if root not in result.parents:
        raise MeridianError("derived worktree path escapes the configured root")
    resolved_result = result.resolve()
    if root not in resolved_result.parents:
        raise MeridianError("derived worktree path escapes the configured root through a symlink")
    return result


def handoff_worktree_value(worktree_root: Path, path: Path) -> str:
    """Machine-independent handoff value: the path relative to the worktree root."""
    return path.relative_to(worktree_root.expanduser().resolve()).as_posix()


def task_worktree_path(project_root: Path, worktree_root: Path | None, task_id: str) -> Path:
    """Compatibility derivation for callers that may be planning a new task."""
    return _task_worktree_path_for_identity(
        project_root,
        _effective_worktree_root(worktree_root),
        resolve_task_identity(project_root, task_id, "new"),
    )


def validate_worktree_collision(project_root: Path, path: Path, task_id: str) -> None:
    """Reject an existing path unless it is the exact expected linked worktree."""
    if not path.exists():
        return
    expected_common = canonical_git_common_dir(project_root)
    try:
        actual_common = canonical_git_common_dir(path)
        branch = git_output(path, "branch", "--show-current")
    except MeridianError as error:
        raise MeridianError(f"worktree path collision at {path}: {error}") from error
    try:
        expected_branch = resolve_task_identity(project_root, task_id, "existing").branch_name
    except MeridianError:
        expected_branch = resolve_task_identity(project_root, task_id, "new").branch_name
    if actual_common != expected_common or branch != expected_branch:
        raise MeridianError(
            f"worktree path collision at {path}: expected {expected_common} on {expected_branch}, "
            f"found {actual_common} on {branch or 'detached HEAD'}"
        )


def _run_git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )


def _validation_reason(reasons: list[str], condition: bool, reason: str) -> None:
    if not condition:
        reasons.append(reason)


def validation_evidence_reasons(record: object) -> list[str]:
    """Return schema-shaped errors without running a project command."""
    if not isinstance(record, dict):
        return ["record: must be an object"]
    reasons: list[str] = []
    required = ("version", "task_id", "status", "level", "commit", "tree", "command", "tests_run", "produced_at")
    for field in required:
        _validation_reason(reasons, field in record, f"{field}: is required")
    _validation_reason(reasons, record.get("version") == 1, "version: must be 1")
    _validation_reason(reasons, isinstance(record.get("task_id"), str) and bool(record.get("task_id")), "task_id: must be a non-empty string")
    _validation_reason(reasons, record.get("status") in {"running", "unavailable", "failed", "passed"}, "status: unknown value")
    _validation_reason(reasons, record.get("level") in {"T1_CI", "T2_SHARDED", "T3_ATTESTED"}, "level: unknown value")
    for field in ("commit", "tree", "produced_at"):
        _validation_reason(reasons, isinstance(record.get(field), str) and bool(record.get(field)), f"{field}: must be a non-empty string")
    _validation_reason(reasons, isinstance(record.get("command"), list) and all(isinstance(item, str) and item for item in record.get("command", [])), "command: must be an array of non-empty strings")
    _validation_reason(reasons, isinstance(record.get("tests_run"), int) and not isinstance(record.get("tests_run"), bool), "tests_run: must be an integer")
    status = record.get("status")
    if status == "running":
        for field in ("started_at", "log"):
            _validation_reason(reasons, isinstance(record.get(field), str) and bool(record.get(field)), f"{field}: is required for running")
    elif status == "unavailable":
        _validation_reason(reasons, isinstance(record.get("reason"), str) and bool(record.get("reason")), "reason: is required for unavailable")
    elif status in {"failed", "passed"}:
        _validation_reason(reasons, isinstance(record.get("exit_code"), int) and not isinstance(record.get("exit_code"), bool), f"exit_code: is required for {status}")
    level = record.get("level")
    if level == "T1_CI":
        ci = record.get("ci")
        _validation_reason(reasons, isinstance(ci, dict), "ci: is required for T1_CI")
        if isinstance(ci, dict):
            for field in ("run_id", "run_url", "workflow", "conclusion", "head_sha"):
                _validation_reason(reasons, isinstance(ci.get(field), str) and bool(ci.get(field)), f"ci.{field}: is required for T1_CI")
    elif level == "T2_SHARDED":
        shards = record.get("shards")
        _validation_reason(reasons, isinstance(shards, list) and bool(shards), "shards: is required for T2_SHARDED")
        for field in ("total", "digest"):
            _validation_reason(reasons, field in record, f"{field}: is required for T2_SHARDED")
        if isinstance(shards, list):
            for number, shard in enumerate(shards, 1):
                _validation_reason(reasons, isinstance(shard, dict), f"shards[{number}]: must be an object")
                if isinstance(shard, dict):
                    for field in ("index", "count", "exit_code", "tests_run", "digest", "total"):
                        _validation_reason(reasons, field in shard, f"shards[{number}].{field}: is required")
    elif level == "T3_ATTESTED":
        _validation_reason(reasons, record.get("attested_by") == "developer", "attested_by: must be developer for T3_ATTESTED")
        _validation_reason(reasons, isinstance(record.get("attested_on"), str) and bool(record.get("attested_on")), "attested_on: is required for T3_ATTESTED")
        _validation_reason(reasons, isinstance(record.get("statement"), str) and bool(record.get("statement").strip()), "statement: is required for T3_ATTESTED")
    return reasons


def check_validation_evidence(record_path: Path, project_root: Path, expected_commit: str | None) -> tuple[dict[str, object], int]:
    """Read an external validation attestation using Git plumbing only."""
    reasons: list[str] = []
    try:
        schema = json.loads((Path(__file__).resolve().parents[1] / VALIDATION_EVIDENCE_SCHEMA_PATH).read_text(encoding="utf-8"))
        if not isinstance(schema, dict) or schema.get("$id") != "https://meridian.local/schemas/validation-evidence-v1.schema.json":
            reasons.append("schema: validation-evidence-v1 is invalid")
    except (OSError, json.JSONDecodeError) as error:
        reasons.append(f"schema: {error}")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        record = None
        reasons.append(f"record: {error}")
    reasons.extend(validation_evidence_reasons(record))
    if not isinstance(record, dict):
        return {"status": "VALIDATION_FAILED", "level": None, "reasons": reasons}, VALIDATION_EXIT_FAILED
    status, level = record.get("status"), record.get("level")
    if status == "running" and not reasons:
        return {"status": "VALIDATION_RUNNING", "level": level, "reasons": []}, VALIDATION_EXIT_PENDING
    if status == "unavailable" and not reasons:
        return {"status": "VALIDATION_UNAVAILABLE", "level": level, "reasons": []}, VALIDATION_EXIT_PENDING
    if status != "passed":
        reasons.append("status: is not passed")
    try:
        branch = resolve_task_identity(project_root, str(record.get("task_id", "")), "existing").branch_name
        target = expected_commit or git_output(project_root, "rev-parse", branch)
        resolved = git_output(project_root, "rev-parse", f"{record.get('commit', '')}^{{commit}}")
        _validation_reason(reasons, resolved == target, "commit: does not equal the expected commit")
        _validation_reason(reasons, git_output(project_root, "rev-parse", f"{resolved}^{{tree}}") == record.get("tree"), "tree: does not equal commit tree")
    except MeridianError as error:
        reasons.append(f"commit: {error}")
    _validation_reason(reasons, record.get("exit_code") == 0, "exit_code: must be 0")
    _validation_reason(reasons, isinstance(record.get("tests_run"), int) and record.get("tests_run", 0) > 0, "tests_run: must be above 0")
    if level == "T1_CI" and isinstance(record.get("ci"), dict):
        ci = record["ci"]
        _validation_reason(reasons, ci.get("conclusion") == "success", "ci.conclusion: must be success")
        _validation_reason(reasons, ci.get("head_sha") == record.get("commit"), "ci.head_sha: must equal commit")
    elif level == "T2_SHARDED" and isinstance(record.get("shards"), list):
        shards = record["shards"]
        counts = {shard.get("count") for shard in shards if isinstance(shard, dict)}
        count = next(iter(counts)) if len(counts) == 1 else None
        indexes = [shard.get("index") for shard in shards if isinstance(shard, dict)]
        _validation_reason(reasons, isinstance(count, int) and sorted(indexes) == list(range(1, count + 1)), "shards.index: must contain 1..count exactly once")
        _validation_reason(reasons, all(isinstance(shard, dict) and shard.get("exit_code") == 0 for shard in shards), "shards.exit_code: every shard must be 0")
        _validation_reason(reasons, sum(shard.get("tests_run", 0) for shard in shards if isinstance(shard, dict)) == record.get("total"), "total: must equal shard tests_run sum")
        _validation_reason(reasons, all(isinstance(shard, dict) and shard.get("digest") == record.get("digest") and shard.get("total") == record.get("total") for shard in shards), "shards.digest: every shard must carry the record digest and total")
    report_status = "VALIDATION_PASSED" if not reasons else "VALIDATION_FAILED"
    return {"status": report_status, "level": level, "reasons": reasons}, VALIDATION_EXIT_PASSED if not reasons else VALIDATION_EXIT_FAILED


def _git_worktrees(project_root: Path) -> list[dict[str, str]]:
    output = git_output(project_root, "worktree", "list", "--porcelain")
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in output.splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return records


def canonical_project_root(path: Path) -> Path:
    """Return the first registered worktree, which is Meridian's primary checkout."""
    candidate = path.expanduser().resolve()
    records = _git_worktrees(candidate)
    if not records or "worktree" not in records[0]:
        raise MeridianError(f"cannot identify the primary checkout from {candidate}")
    return Path(records[0]["worktree"]).resolve()


def _verified_lifecycle_project(supplied_project: Path | None = None) -> Path:
    current_project = canonical_project_root(Path.cwd())
    if supplied_project is not None:
        supplied = supplied_project.expanduser().resolve()
        supplied_primary = canonical_project_root(supplied)
        if supplied != supplied_primary or supplied_primary != current_project:
            raise MeridianError(
                f"--project must name the canonical current project {current_project}, found {supplied}"
            )
    return current_project


def user_configuration_path(
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    values = os.environ if environment is None else environment
    user_home = (home or Path.home()).expanduser().resolve()
    configured = values.get("XDG_CONFIG_HOME")
    base = Path(configured).expanduser().resolve() if configured else user_home / ".config"
    return base / "meridian/config.json"


def _read_user_configuration(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    value = _read_json_object(path, "Meridian user configuration")
    if set(value) != {"version", "worktreeRoot"} or value.get("version") != 1:
        raise MeridianError(
            f"Meridian user configuration must contain only version 1 and worktreeRoot: {path}"
        )
    root = value.get("worktreeRoot")
    if not isinstance(root, str) or not root.strip():
        raise MeridianError(f"Meridian user configuration worktreeRoot must be a non-empty string: {path}")
    if not Path(root).expanduser().is_absolute():
        raise MeridianError(f"Meridian user configuration worktreeRoot must be absolute: {path}")
    return value


def resolve_worktree_root(
    explicit: Path | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    config_path: Path | None = None,
) -> ResolvedWorktreeRoot:
    values = os.environ if environment is None else environment
    user_home = (home or Path.home()).expanduser().resolve()
    selected_config = config_path or user_configuration_path(values, user_home)
    explicit_path = explicit.expanduser().resolve() if explicit is not None else None
    environment_value = values.get("MERIDIAN_WORKTREE_ROOT")
    environment_path = (
        Path(environment_value).expanduser().resolve() if environment_value else None
    )
    if explicit_path is not None and environment_path is not None and explicit_path != environment_path:
        raise MeridianError(
            "conflicting worktree roots: --worktree-root supplied "
            f"{explicit_path}; MERIDIAN_WORKTREE_ROOT supplied {environment_path}"
        )
    if explicit_path is not None:
        root, source = explicit_path, "--worktree-root"
    elif environment_path is not None:
        root, source = environment_path, "MERIDIAN_WORKTREE_ROOT"
    else:
        configuration = _read_user_configuration(selected_config)
        if configuration is not None:
            root = Path(str(configuration["worktreeRoot"])).expanduser().resolve()
            source = "user-config"
        else:
            root = user_home / ".meridian/worktrees"
            source = "default"
    if root in {Path(root.anchor), user_home}:
        raise MeridianError(
            f"worktree root from {source} must be a dedicated directory, not the filesystem root or home: {root}"
        )
    return ResolvedWorktreeRoot(root, source, selected_config)


def _effective_worktree_root(worktree_root: Path | None = None) -> Path:
    return resolve_worktree_root(worktree_root).path


def _lifecycle_paths(project_root: Path, identity: ResolvedTaskIdentity) -> tuple[Path, Path, Path]:
    common = canonical_git_common_dir(project_root)
    state = common / WORKTREE_STATE_DIRECTORY / f"{identity.artifact_stem}.json"
    return state, common / INTEGRATION_LEASE_NAME, common / INTEGRATION_STATE_NAME


def _merge_head_path(project_root: Path) -> Path:
    return Path(git_output(project_root, "rev-parse", "--git-path", "MERGE_HEAD")).resolve()


def _write_json_atomic(path: Path, value: dict[str, object], *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if exclusive:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
        return
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MeridianError(f"cannot read {label} at {path}: {error}") from error
    if not isinstance(value, dict):
        raise MeridianError(f"{label} must be a JSON object: {path}")
    return value


def _branch_commit(project_root: Path, branch: str) -> str | None:
    result = _run_git(project_root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise MeridianError(result.stderr.strip() or f"cannot inspect branch {branch}")
    return result.stdout.strip()


def lifecycle_started_at(task_id: str, supplied_project: Path | None = None) -> str | None:
    """Return a valid preparation timestamp, preserving legacy state as unavailable."""
    project_root = _verified_lifecycle_project(supplied_project)
    identity = resolve_task_identity(project_root, task_id, "existing")
    state_path, _lease, _integration = _lifecycle_paths(project_root, identity)
    state = _read_json_object(state_path, "worktree lifecycle state")
    value = state.get("started_at")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if parsed.tzinfo is not None else None


def prepare_task_worktree(
    task_id: str,
    worktree_root: Path | None,
    supplied_project: Path | None = None,
    base: str = "main",
) -> dict[str, object]:
    if base != "main":
        raise MeridianError("worktree prepare permits only the main base")
    project_root = _verified_lifecycle_project(supplied_project)
    root = _effective_worktree_root(worktree_root)
    identity = resolve_task_identity(project_root, task_id, "existing")
    path = _task_worktree_path_for_identity(project_root, root, identity)
    state_path, _lease, _integration = _lifecycle_paths(project_root, identity)
    records = _git_worktrees(project_root)
    registered = next((item for item in records if Path(item["worktree"]).resolve() == path), None)
    branch_commit = _branch_commit(project_root, identity.branch_name)
    if (registered is None) != (branch_commit is None):
        raise MeridianError(
            f"partial task state retained for {identity.canonical_id}; branch and canonical worktree must both exist or both be absent"
        )
    base_commit = git_output(project_root, "rev-parse", "--verify", f"{base}^{{commit}}")
    created = False
    prior: dict[str, object] = {}
    if registered is None:
        if path.exists():
            raise MeridianError(f"worktree path collision at {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        added = _run_git(project_root, "worktree", "add", "-b", identity.branch_name, str(path), base_commit)
        if added.returncode != 0:
            raise MeridianError(added.stderr.strip() or "git worktree add failed")
        branch_commit = base_commit
        created = True
    else:
        expected_ref = f"refs/heads/{identity.branch_name}"
        if registered.get("branch") != expected_ref or registered.get("HEAD") != branch_commit:
            raise MeridianError(
                f"canonical worktree mismatch retained at {path}: expected {expected_ref} at {branch_commit}"
            )
        if git_output(path, "status", "--porcelain"):
            raise MeridianError(f"existing task worktree is dirty and was retained: {path}")
        if state_path.is_file():
            prior = _read_json_object(state_path, "worktree lifecycle state")
            if prior.get("worktree") != str(path) or prior.get("branch") != identity.branch_name:
                raise MeridianError(f"lifecycle state mismatch retained at {state_path}")
            base_commit = str(prior.get("base_commit", base_commit))
    state = {
        "version": 1,
        "task_id": identity.canonical_id,
        "branch": identity.branch_name,
        "worktree": str(path),
        "worktree_root": str(root),
        "project": str(project_root),
        "git_common_dir": str(canonical_git_common_dir(project_root)),
        "base_commit": base_commit,
        "task_commit": branch_commit,
        "handoff": str(identity.handoff_path),
    }
    if created:
        state["started_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    elif "started_at" in prior:
        # Keep a pre-existing value byte-for-byte; malformed values are handled
        # as unavailable by the read-only console rather than rewritten.
        state["started_at"] = prior["started_at"]
    _write_json_atomic(state_path, state)
    return {
        **state,
        "handoff_worktree": handoff_worktree_value(root, path),
        "created": created,
        "next_action": "check",
    }


def inspect_task_worktree(
    task_id: str,
    worktree_root: Path | None,
    supplied_project: Path | None = None,
    *,
    require_effective_worktree: bool = True,
) -> tuple[dict[str, object], bool]:
    project_root = _verified_lifecycle_project(supplied_project)
    root = _effective_worktree_root(worktree_root)
    identity = resolve_task_identity(project_root, task_id, "existing")
    expected = _task_worktree_path_for_identity(project_root, root, identity)
    state_path, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    errors: list[str] = []
    state: dict[str, object] = {}
    if state_path.is_file():
        state = _read_json_object(state_path, "worktree lifecycle state")
    else:
        errors.append("missing-state")
    records = _git_worktrees(project_root)
    registered = next((item for item in records if Path(item["worktree"]).resolve() == expected), None)
    current = Path.cwd().resolve()
    if require_effective_worktree and current != expected:
        errors.append("wrong-worktree")
    if registered is None:
        errors.append("unregistered-worktree")
        head = ""
        branch = ""
        clean = False
    else:
        head = registered.get("HEAD", "")
        branch = registered.get("branch", "").removeprefix("refs/heads/")
        if branch != identity.branch_name:
            errors.append("branch-mismatch")
        status = _run_git(expected, "status", "--porcelain")
        clean = status.returncode == 0 and not status.stdout
        if not clean:
            errors.append("dirty-worktree")
    if state:
        if state.get("task_id") != identity.canonical_id:
            errors.append("state-task-mismatch")
        if state.get("project") != str(project_root) or state.get("worktree") != str(expected):
            errors.append("state-path-mismatch")
        if state.get("branch") != identity.branch_name:
            errors.append("state-branch-mismatch")
        if state.get("worktree_root") != str(root):
            errors.append("state-root-mismatch")
        if state.get("git_common_dir") != str(canonical_git_common_dir(project_root)):
            errors.append("state-common-dir-mismatch")
        base_commit = state.get("base_commit")
        if not isinstance(base_commit, str) or _run_git(
            project_root, "cat-file", "-e", f"{base_commit}^{{commit}}"
        ).returncode != 0:
            errors.append("base-commit-mismatch")
    handoff_consistent = bool(state) and not any(item.startswith("state-") for item in errors)
    if identity.handoff_path.is_file():
        handoff_text = identity.handoff_path.read_text(encoding="utf-8")
        expected_fields = {
            "Branch": identity.branch_name,
            "Worktree": (handoff_worktree_value(root, expected), str(expected)),
            "Base `main` commit": (str(state.get("base_commit", "")),),
        }
        for label, accepted in expected_fields.items():
            match = re.search(rf"^- {re.escape(label)}:\s*`([^`]+)`", handoff_text, re.MULTILINE)
            if match is not None and match.group(1) not in accepted:
                errors.append("handoff-mismatch")
                handoff_consistent = False
                break
    result = {
        "version": 1,
        "status": "ready" if not errors else "blocked",
        "task_id": identity.canonical_id,
        "branch": branch or identity.branch_name,
        "worktree": str(expected),
        "git_common_dir": str(canonical_git_common_dir(project_root)),
        "canonical_prepared_path": str(expected),
        "handoff_worktree": handoff_worktree_value(root, expected),
        "effective_worker_path": str(current),
        "base_commit": state.get("base_commit", ""),
        "task_commit": head,
        "clean": clean,
        "handoff_consistent": handoff_consistent,
        "integration_active": lease_path.exists() or integration_path.exists(),
        "errors": errors,
        "next_action": "implement" if not errors else "repair-or-abort",
    }
    return result, not errors


def closure_status(
    task_id: str,
    worktree_root: Path | None,
    supplied_project: Path | None = None,
) -> tuple[dict[str, object], bool]:
    """Report the next closure step without changing Git or lifecycle state."""
    project_root = _verified_lifecycle_project(supplied_project)
    root = _effective_worktree_root(worktree_root)
    identity = resolve_task_identity(project_root, task_id, "existing")
    expected = _task_worktree_path_for_identity(project_root, root, identity)
    state_path, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    records = _git_worktrees(project_root)
    registered = next((item for item in records if Path(item["worktree"]).resolve() == expected), None)
    branch_commit = _branch_commit(project_root, identity.branch_name)
    project = str(project_root)

    def report(step: str, stop_reason: str | None, resume: str | None) -> tuple[dict[str, object], bool]:
        return ({
            "version": 1,
            "task_id": identity.canonical_id,
            "step": step,
            "stop_reason": stop_reason,
            "resume": resume,
        }, stop_reason is None)

    if not state_path.is_file() or registered is None or branch_commit is None:
        if identity.handoff_path.is_file() and registered is None and branch_commit is None:
            return report("C10", None, None)
        return report(
            "C4",
            "WRONG_WORKTREE",
            f"meridian worktree prepare {identity.canonical_id} --project {project} --format json",
        )

    if lease_path.exists() and not integration_path.exists():
        return report(
            "C6",
            "LEASE_HELD",
            f"meridian worktree integrate abort {identity.canonical_id} --project {project} --format json",
        )
    if integration_path.exists():
        return report("C7", None, "run the selected candidate validation")

    state = _read_json_object(state_path, "worktree lifecycle state")
    if state.get("base_commit") == branch_commit:
        return report("C1", "ACCEPTANCE_UNMET", "complete the task and rerun task validation")

    if _run_git(project_root, "merge-base", "--is-ancestor", branch_commit, "main").returncode == 0:
        origin = _run_git(project_root, "remote", "get-url", "origin")
        remote_main = _run_git(project_root, "rev-parse", "--verify", "refs/remotes/origin/main")
        if origin.returncode != 0 or (
            remote_main.returncode == 0
            and _run_git(project_root, "merge-base", "--is-ancestor", "main", "refs/remotes/origin/main").returncode == 0
        ):
            return report(
                "C10",
                None,
                f"meridian worktree cleanup {identity.canonical_id} --project {project} --format json",
            )
        return report(
            "C9",
            "PUSH_PENDING" if remote_main.returncode == 0 and _run_git(
                project_root, "merge-base", "--is-ancestor", "refs/remotes/origin/main", "main"
            ).returncode == 0 else None,
            "git push origin main",
        )

    if git_output(project_root, "status", "--porcelain"):
        return report(
            "C6",
            "PRIMARY_DIRTY",
            "clean the primary checkout and run integration stage",
        )
    evidence_path = state_path.with_suffix(".evidence.json")
    if evidence_path.is_file():
        try:
            evidence = _integration_evidence(evidence_path)
        except MeridianError:
            evidence = None
        if (
            evidence is not None
            and evidence["accepted"] is True
            and evidence["validation_passed"] is True
            and evidence["validated_task_commit"] == branch_commit
        ):
            return report(
                "C6",
                None,
                f"meridian worktree integrate stage {identity.canonical_id} --project {project} "
                f"--evidence {evidence_path} --format json",
            )
    return report("C5", "EVIDENCE_INCOMPLETE", "record machine evidence")


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise MeridianError(f"integration evidence field {label!r} must be an array of non-empty strings")
    return tuple(value)


def _bool_field(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise MeridianError(f"integration evidence field {label!r} must be boolean")
    return value


def _integration_evidence(path: Path) -> dict[str, object]:
    evidence = _read_json_object(path.expanduser().resolve(), "integration evidence")
    required = {
        "accepted",
        "validation_passed",
        "validated_task_commit",
        "validated_base_commit",
        "full_validation_required",
        "interaction_assessment_complete",
        "task_paths",
        "task_dependencies",
        "task_behavioral_surfaces",
        "main_advanced_dependencies",
        "main_advanced_behavioral_surfaces",
    }
    missing = sorted(required - evidence.keys())
    if missing:
        raise MeridianError(f"integration evidence is incomplete; missing: {', '.join(missing)}")
    for field in ("accepted", "validation_passed", "full_validation_required", "interaction_assessment_complete"):
        _bool_field(evidence[field], field)
    for field in (
        "task_paths",
        "task_dependencies",
        "task_behavioral_surfaces",
        "main_advanced_dependencies",
        "main_advanced_behavioral_surfaces",
    ):
        _string_tuple(evidence[field], field)
    for field in ("validated_task_commit", "validated_base_commit"):
        if not isinstance(evidence[field], str) or not re.fullmatch(r"[0-9a-f]{40}", evidence[field]):
            raise MeridianError(f"integration evidence field {field!r} must be a full Git object ID")
    return evidence


def record_task_evidence(
    task_id: str,
    worktree_root: Path | None,
    validation_commands: list[str],
    validation_exit_codes: list[int],
    *,
    accepted: bool,
    task_dependencies: list[str],
    task_behavioral_surfaces: list[str],
    main_advanced_dependencies: list[str],
    main_advanced_behavioral_surfaces: list[str],
    full_validation_required: bool,
    supplied_project: Path | None = None,
) -> dict[str, object]:
    """Record Git-derived task-validation facts without running validation."""
    if len(validation_commands) != len(validation_exit_codes):
        raise MeridianError("each --validation-command requires one --validation-exit-code")
    if not validation_commands or any(not command.strip() for command in validation_commands):
        raise MeridianError("at least one non-empty --validation-command is required")
    project_root = _verified_lifecycle_project(supplied_project)
    identity = resolve_task_identity(project_root, task_id, "existing")
    inspection, ready = inspect_task_worktree(
        identity.canonical_id, worktree_root, project_root
    )
    if not ready:
        raise MeridianError(f"task worktree is not ready: {', '.join(inspection['errors'])}")
    state_path, _lease, _integration = _lifecycle_paths(project_root, identity)
    state = _read_json_object(state_path, "worktree lifecycle state")
    task_commit = str(inspection["task_commit"])
    base_commit = str(state["base_commit"])
    task_paths = tuple(filter(None, git_output(
        project_root, "diff", "--name-only", base_commit, task_commit
    ).splitlines()))
    evidence_path = state_path.with_suffix(".evidence.json")
    evidence = {
        "accepted": accepted,
        "validation_passed": all(code == 0 for code in validation_exit_codes),
        "validated_task_commit": task_commit,
        "validated_base_commit": base_commit,
        "full_validation_required": full_validation_required,
        "interaction_assessment_complete": True,
        "task_paths": list(task_paths),
        "task_dependencies": task_dependencies,
        "task_behavioral_surfaces": task_behavioral_surfaces,
        "main_advanced_dependencies": main_advanced_dependencies,
        "main_advanced_behavioral_surfaces": main_advanced_behavioral_surfaces,
        "validation_commands": validation_commands,
        "validation_exit_codes": validation_exit_codes,
    }
    _write_json_atomic(evidence_path, evidence)
    return {
        "version": 1,
        "task_id": identity.canonical_id,
        "evidence": str(evidence_path),
        "validated_task_commit": task_commit,
        "validated_base_commit": base_commit,
        "task_paths": list(task_paths),
        "validation_passed": evidence["validation_passed"],
    }


def _remove_owned_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _lifecycle_changes_after_validation(
    project_root: Path,
    identity: ResolvedTaskIdentity,
    validated_task: str,
    task_commit: str,
) -> tuple[bool, tuple[str, ...]]:
    """Accept only lifecycle-only changes, including one exact task archive rename."""
    project_root = project_root.resolve()
    active_record = identity.task_path.relative_to(project_root)
    if active_record.parts[:2] == ("tasks", "done"):
        active_record = Path("tasks") / active_record.name
    archive_record = Path("tasks") / "done" / active_record.name
    allowed = {
        str(active_record),
        str(archive_record),
        str(identity.queue_path.relative_to(project_root)),
        str(identity.handoff_path.relative_to(project_root)),
        str(identity.review_path.relative_to(project_root)),
        "PROJECT_PLAN.md",
        "tasks/QUEUE_ARCHIVE.md",
    }
    output = _run_git(
        project_root,
        "diff",
        "--name-status",
        "-z",
        "--find-renames=100%",
        validated_task,
        task_commit,
    ).stdout
    fields = output.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    offending: set[str] = set()
    validated_is_archived = _run_git(
        project_root, "cat-file", "-e", f"{validated_task}:{archive_record}"
    ).returncode == 0
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                raise MeridianError("invalid rename-aware Git diff output")
            old_path, new_path = fields[index], fields[index + 1]
            index += 2
            if status != "R100" or old_path != str(active_record) or new_path != str(archive_record):
                offending.update((old_path, new_path))
            continue
        if index >= len(fields):
            raise MeridianError("invalid rename-aware Git diff output")
        path = fields[index]
        index += 1
        if path not in allowed:
            offending.add(path)
        elif path == str(archive_record):
            offending.add(path)
        elif path == str(active_record) and (status != "M" or validated_is_archived):
            offending.add(path)
    return not offending, tuple(sorted(offending))


def _completed_task_row(contents: str, task_id: str, path: Path, pattern: str) -> str:
    """Return one known task row with its status set to complete."""
    matches = list(re.finditer(pattern, contents, flags=re.MULTILINE))
    if len(matches) != 1:
        raise MeridianError(
            f"unrecognized completion row for task {task_id} in {path}"
        )
    match = matches[0]
    return f"{contents[:match.start(1)]}[x]{contents[match.end(1):]}"


_QUEUE_SECTION_HEADING = re.compile(r"^### .+\n?$", re.MULTILINE)
_QUEUE_TABLE_DIVIDER = re.compile(r"^\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
_QUEUE_TASK_ROW = re.compile(r"^\| `(?P<status>\[[ /x]\])` \| [^|]+ \|.*$")
_QUEUE_ARCHIVE_HEADER = (
    "# Task Execution Queue — Archive\n\n"
    "Closed phases and sections moved out of `tasks/QUEUE.md` once every row in them is\n"
    "`[x]`, to keep that file's reading cost low. Mirrors `QUEUE.md`'s own table\n"
    "structure.\n"
)
_GOVERNED_QUEUE_ARCHIVE_HEADER = (
    "# Task Execution Queue — Archive\n\n"
    "Accepted tasks moved out of `tasks/QUEUE.md`. Mirrors `QUEUE.md`'s own table\n"
    "structure.\n"
)
_GOVERNED_QUEUE_TASK_ROW = re.compile(
    r"^\| (?P<order>[^|]+) \| (?P<id>[^|]+) \| (?P<priority>[^|]+) \| "
    r"(?P<status>QUEUED|IN_PROGRESS|CHANGES_REQUESTED|READY_FOR_REVIEW|ACCEPTED) \| "
    r"(?P<review>REQUIRED|NOT_REQUIRED) \| (?P<dependencies>[^|]*) \| (?P<task_file>[^|]*) \|$",
    re.MULTILINE,
)


def _governed_completion_row(
    contents: str, identity: ResolvedTaskIdentity, path: Path
) -> tuple[str, bool, str]:
    """Return a recognized Governed queue row and whether it may be accepted."""
    matches = [
        match for match in _GOVERNED_QUEUE_TASK_ROW.finditer(contents)
        if match.group("id").strip().strip("`") == identity.canonical_id
    ]
    if len(matches) != 1:
        raise MeridianError(f"unrecognized completion row for task {identity.canonical_id} in {path}")
    match = matches[0]
    if match.group("review") == "REQUIRED":
        review_path = identity.review_path
        verdict = latest_review_verdict(
            review_path.read_text(encoding="utf-8") if review_path.is_file() else None
        )
        if verdict != "APPROVE":
            reason = "review record is missing or malformed" if verdict is None else f"latest review verdict is {verdict}"
            return contents, False, reason
    return (
        f"{contents[:match.start('status')]}ACCEPTED{contents[match.end('status'):]}",
        True,
        "review not required" if match.group("review") == "NOT_REQUIRED" else "latest review verdict is APPROVE",
    )


def _archive_completed_queue_sections(
    queue_contents: str, queue_path: Path, archive_path: Path, mode: str = "lean-delivery"
) -> tuple[str, str | None]:
    """Move fully complete, recognized queue sections to the archive in memory."""
    headings = list(_QUEUE_SECTION_HEADING.finditer(queue_contents))
    completed_sections: list[tuple[int, int, str]] = []
    for index, heading in enumerate(headings):
        section_end = headings[index + 1].start() if index + 1 < len(headings) else len(queue_contents)
        section = queue_contents[heading.start():section_end]
        lines = section.splitlines(keepends=True)
        table_index = next((
            line_index for line_index, line in enumerate(lines)
            if line.rstrip("\n").startswith("| Status |")
            or (mode == "governed-sdd" and line.rstrip("\n").startswith("| Order | ID | Priority | Status | Review |"))
        ), None)
        if table_index is None:
            continue
        if table_index + 2 >= len(lines) or not _QUEUE_TABLE_DIVIDER.fullmatch(lines[table_index + 1].rstrip("\n")):
            raise MeridianError(f"unrecognized queue section shape in {queue_path}: {lines[0].strip()}")
        task_rows: list[str] = []
        for line in lines[table_index + 2:]:
            if not line.startswith("|"):
                break
            task_rows.append(line)
        row_pattern = _GOVERNED_QUEUE_TASK_ROW if mode == "governed-sdd" else _QUEUE_TASK_ROW
        if not task_rows or any(row_pattern.fullmatch(row.rstrip("\n")) is None for row in task_rows):
            raise MeridianError(f"unrecognized queue section shape in {queue_path}: {lines[0].strip()}")
        completed_status = "ACCEPTED" if mode == "governed-sdd" else "[x]"
        if all(row_pattern.fullmatch(row.rstrip("\n")).group("status") == completed_status for row in task_rows):
            completed_sections.append((heading.start(), section_end, section))
    if not completed_sections:
        return queue_contents, None
    archived = "".join(section.rstrip("\n") + "\n" for _, _, section in completed_sections)
    retained: list[str] = []
    cursor = 0
    for start, end, _section in completed_sections:
        retained.append(queue_contents[cursor:start])
        cursor = end
    retained.append(queue_contents[cursor:])
    updated_queue = "".join(retained).rstrip("\n") + "\n"
    default_header = _GOVERNED_QUEUE_ARCHIVE_HEADER if mode == "governed-sdd" else _QUEUE_ARCHIVE_HEADER
    archive_contents = archive_path.read_text(encoding="utf-8") if archive_path.exists() else default_header
    return updated_queue, archive_contents.rstrip("\n") + "\n\n" + archived


def _relink_archived_task_row(contents: str, queue_path: Path, identity: ResolvedTaskIdentity) -> str:
    """Point the task's queue row at its record when the merge archived it under done/."""
    active_record = identity.task_path
    archive_record = active_record.parent / "done" / active_record.name
    if not active_record.exists() and not archive_record.is_file():
        return contents
    row = re.search(
        rf"^\| (?:`\[[ /x]\]`|[^|]+) \| \[?{re.escape(identity.canonical_id)}\b.*$",
        contents,
        flags=re.MULTILINE,
    )
    if row is None:
        return contents
    target_record = archive_record if archive_record.is_file() else active_record
    new_target = Path(os.path.relpath(target_record, queue_path.parent)).as_posix()

    def retarget(link: re.Match[str]) -> str:
        target = link.group(1)
        if "://" in target or target.startswith("#"):
            return link.group(0)
        linked_record = (queue_path.parent / target.split("#", 1)[0]).resolve()
        if linked_record not in (active_record, archive_record):
            return link.group(0)
        return f"]({new_target})"

    relinked = re.sub(r"\]\(([^)]*)\)", retarget, row.group(0))
    return f"{contents[:row.start()]}{relinked}{contents[row.end():]}"


def _apply_task_completion_rows(project_root: Path, identity: ResolvedTaskIdentity) -> dict[str, str]:
    """Set known completion rows and archive fully complete queue sections."""
    queue_path = identity.queue_path
    archive_path = queue_path.with_name("QUEUE_ARCHIVE.md")
    task_id = identity.canonical_id
    queue_contents = queue_path.read_text(encoding="utf-8")
    mode = detect_mode(project_root)
    if mode == "governed-sdd":
        queue_completed, accepted, reason = _governed_completion_row(queue_contents, identity, queue_path)
        queue_completed = _relink_archived_task_row(queue_completed, queue_path, identity)
        if not accepted:
            if queue_completed != queue_contents:
                queue_path.write_text(queue_completed, encoding="utf-8")
            return {"status": "REVIEW_PENDING", "reason": reason}
        archived_queue, archive_contents = _archive_completed_queue_sections(
            queue_completed, queue_path, archive_path, mode
        )
        if archived_queue != queue_contents:
            queue_path.write_text(archived_queue, encoding="utf-8")
        if archive_contents is not None:
            archive_path.write_text(archive_contents, encoding="utf-8")
        return {"status": "COMPLETED", "reason": reason}
    plan_path = project_root / "PROJECT_PLAN.md"
    plan_contents = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""
    queue_completed = _completed_task_row(
        queue_contents,
        task_id,
        queue_path,
        rf"^\| `(?P<status>\[[ /x]\])` \| {re.escape(task_id)} \|.*$",
    )
    plan_completed = _completed_task_row(
        plan_contents,
        task_id,
        plan_path,
        rf"^- `(?P<status>\[[ /x]\])` {re.escape(task_id)} — .*$",
    )
    queue_completed = _relink_archived_task_row(queue_completed, queue_path, identity)
    archived_queue, archive_contents = _archive_completed_queue_sections(
        queue_completed, queue_path, archive_path, mode
    )
    if archived_queue != queue_contents:
        queue_path.write_text(archived_queue, encoding="utf-8")
    if plan_completed != plan_contents:
        plan_path.write_text(plan_completed, encoding="utf-8")
    if archive_contents is not None:
        archive_path.write_text(archive_contents, encoding="utf-8")
    return {"status": "COMPLETED", "reason": "lean completion rows updated"}


def stage_task_integration(
    task_id: str,
    worktree_root: Path | None,
    evidence_path: Path,
    supplied_project: Path | None = None,
) -> dict[str, object]:
    project_root = _verified_lifecycle_project(supplied_project)
    if Path.cwd().resolve() != project_root:
        raise MeridianError("integration stage must run from the canonical primary checkout")
    identity = resolve_task_identity(project_root, task_id, "existing")
    _state_path, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    if integration_path.exists():
        prior = _read_json_object(integration_path, "staged integration state")
        lease_matches = lease_path.is_file() and _read_json_object(
            lease_path, "integration lease"
        ).get("task_id") == identity.canonical_id
        candidate_matches = prior.get("candidate_tree") == git_output(project_root, "write-tree")
        merge_matches = _merge_head_path(project_root).is_file() and git_output(
            project_root, "rev-parse", "HEAD"
        ) == prior.get("main_commit")
        if (
            prior.get("task_id") == identity.canonical_id
            and lease_matches
            and candidate_matches
            and merge_matches
        ):
            return prior
        raise MeridianError(f"staged integration state is mismatched or stale at {integration_path}")
    if lease_path.exists():
        raise MeridianError(
            f"an interrupted integration lease is retained at {lease_path}; use `meridian worktree integrate abort`"
        )
    inspection, ready = inspect_task_worktree(
        identity.canonical_id,
        worktree_root,
        project_root,
        require_effective_worktree=False,
    )
    if not ready:
        raise MeridianError(f"task worktree is not ready: {', '.join(inspection['errors'])}")
    if git_output(project_root, "branch", "--show-current") != "main":
        raise MeridianError("primary checkout must be on main")
    if git_output(project_root, "status", "--porcelain"):
        raise MeridianError("primary checkout must be clean")
    origin = _run_git(project_root, "remote", "get-url", "origin")
    remote_main = _run_git(project_root, "rev-parse", "--verify", "refs/remotes/origin/main")
    if (
        origin.returncode == 0
        and remote_main.returncode == 0
        and _run_git(
            project_root, "merge-base", "--is-ancestor", "main", "refs/remotes/origin/main"
        ).returncode == 0
        and git_output(project_root, "rev-parse", "main") != git_output(
            project_root, "rev-parse", "refs/remotes/origin/main"
        )
    ):
        raise MeridianError(
            "MAIN_BEHIND_ORIGIN: local main lacks commits from the already fetched origin/main"
        )
    evidence = _integration_evidence(evidence_path)
    if not evidence["accepted"] or not evidence["validation_passed"]:
        raise MeridianError("accepted, successful task validation evidence is required")
    task_commit = str(inspection["task_commit"])
    validated_task = str(evidence["validated_task_commit"])
    validated_base = str(evidence["validated_base_commit"])
    base_is_ancestor = _run_git(
        project_root, "merge-base", "--is-ancestor", validated_base, validated_task
    ).returncode == 0
    validated_is_ancestor = _run_git(
        project_root, "merge-base", "--is-ancestor", validated_task, task_commit
    ).returncode == 0
    relevant_unchanged = validated_task == task_commit
    if validated_is_ancestor and not relevant_unchanged:
        relevant_unchanged, offending = _lifecycle_changes_after_validation(
            project_root, identity, validated_task, task_commit
        )
        if offending:
            raise MeridianError(f"paths changed after validation: {', '.join(offending)}")
    current_main = git_output(project_root, "rev-parse", "main")
    task_paths = tuple(filter(None, git_output(
        project_root, "diff", "--name-only", validated_base, validated_task
    ).splitlines()))
    main_paths = tuple(
        filter(None, git_output(project_root, "diff", "--name-only", validated_base, current_main).splitlines())
    ) if current_main != validated_base else ()
    decision = decide_integration_validation(
        evidence_complete=True,
        validated_task_commit=validated_task,
        current_task_commit=task_commit,
        validated_base_commit=validated_base,
        current_main_commit=current_main,
        validated_base_is_task_ancestor=base_is_ancestor,
        full_validation_required=bool(evidence["full_validation_required"]),
        validated_task_is_current_ancestor=validated_is_ancestor,
        relevant_tree_unchanged_after_validation=relevant_unchanged,
        interaction_assessment_complete=bool(evidence["interaction_assessment_complete"]),
        task_paths=tuple(sorted(set(task_paths) | set(_string_tuple(evidence["task_paths"], "task_paths")))),
        main_advanced_paths=main_paths,
        task_dependencies=_string_tuple(evidence["task_dependencies"], "task_dependencies"),
        main_advanced_dependencies=_string_tuple(evidence["main_advanced_dependencies"], "main_advanced_dependencies"),
        task_behavioral_surfaces=_string_tuple(evidence["task_behavioral_surfaces"], "task_behavioral_surfaces"),
        main_advanced_behavioral_surfaces=_string_tuple(
            evidence["main_advanced_behavioral_surfaces"], "main_advanced_behavioral_surfaces"
        ),
    )
    if decision.outcome == IntegrationValidationOutcome.BLOCKED:
        raise MeridianError(decision.reason)
    lease = {
        "version": 1,
        "task_id": identity.canonical_id,
        "branch": identity.branch_name,
        "project": str(project_root),
        "main_commit": current_main,
    }
    try:
        _write_json_atomic(lease_path, lease, exclusive=True)
    except FileExistsError as error:
        raise MeridianError(f"integration lease already exists: {lease_path}") from error
    merged = _run_git(project_root, "merge", "--no-ff", "--no-commit", identity.branch_name)
    if merged.returncode != 0:
        aborted = _run_git(project_root, "merge", "--abort")
        if aborted.returncode == 0:
            _remove_owned_file(lease_path)
        raise MeridianError("integration conflict was aborted; task branch and worktree were retained")
    try:
        completion = _apply_task_completion_rows(project_root, identity)
        lifecycle_paths = [str(identity.queue_path.relative_to(project_root))]
        if detect_mode(project_root) == "lean-delivery":
            lifecycle_paths.append("PROJECT_PLAN.md")
        archive_path = identity.queue_path.with_name("QUEUE_ARCHIVE.md")
        if archive_path.exists():
            lifecycle_paths.append(str(archive_path.relative_to(project_root)))
        staged_rows = _run_git(
            project_root,
            "add",
            "--",
            *lifecycle_paths,
        )
        if staged_rows.returncode != 0:
            raise MeridianError(staged_rows.stderr.strip() or "could not stage completion rows")
    except (OSError, MeridianError) as error:
        aborted = _run_git(project_root, "merge", "--abort")
        if aborted.returncode == 0:
            _remove_owned_file(lease_path)
        raise MeridianError(str(error)) from error
    candidate_tree = git_output(project_root, "write-tree")
    staged = {
        **lease,
        "task_commit": task_commit,
        "validated_task_commit": validated_task,
        "validated_base_commit": validated_base,
        "task_paths": list(task_paths),
        "main_advanced_paths": list(main_paths),
        "decision": decision.outcome.value,
        "reason": decision.reason,
        "candidate_tree": candidate_tree,
        "next_action": "validate-candidate",
        "completion": completion,
    }
    _write_json_atomic(integration_path, staged, exclusive=True)
    return staged


def finalize_task_integration(
    task_id: str,
    validation_path: Path,
    supplied_project: Path | None = None,
) -> dict[str, object]:
    project_root = _verified_lifecycle_project(supplied_project)
    if Path.cwd().resolve() != project_root:
        raise MeridianError("integration finalize must run from the canonical primary checkout")
    identity = resolve_task_identity(project_root, task_id, "existing")
    _task_state, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    lease = _read_json_object(lease_path, "integration lease")
    staged = _read_json_object(integration_path, "staged integration state")
    if lease.get("task_id") != identity.canonical_id or staged.get("task_id") != identity.canonical_id:
        raise MeridianError("integration ownership does not match the requested task")
    if not _merge_head_path(project_root).is_file() or git_output(
        project_root, "rev-parse", "HEAD"
    ) != staged.get("main_commit"):
        raise MeridianError("the owned staged merge state is missing or its main commit changed")
    if git_output(project_root, "write-tree") != staged.get("candidate_tree"):
        raise MeridianError("staged candidate tree changed after integration stage")
    validation = _read_json_object(validation_path.expanduser().resolve(), "candidate validation evidence")
    if validation.get("candidate_tree") != staged.get("candidate_tree") or validation.get("passed") is not True:
        raise MeridianError("candidate validation evidence is stale, mismatched, or failed")
    required_scope = "full" if staged.get("decision") == "FULL" else "bounded"
    if validation.get("scope") != required_scope:
        raise MeridianError(f"candidate validation scope must be {required_scope!r}")
    commands = validation.get("commands")
    if not isinstance(commands, list) or not commands or not all(isinstance(item, str) and item for item in commands):
        raise MeridianError("candidate validation evidence must name successful commands")
    committed = _run_git(project_root, "commit", "-m", f"Integrate {identity.canonical_id}")
    if committed.returncode != 0:
        raise MeridianError(committed.stderr.strip() or "integration commit failed; staged state was retained")
    merge_commit = git_output(project_root, "rev-parse", "HEAD")
    _remove_owned_file(integration_path)
    _remove_owned_file(lease_path)
    return {
        "version": 1,
        "task_id": identity.canonical_id,
        "merge_commit": merge_commit,
        "candidate_tree": staged["candidate_tree"],
        "decision": staged["decision"],
        "next_action": "push-or-cleanup",
    }


def abort_task_integration(task_id: str, supplied_project: Path | None = None) -> dict[str, object]:
    project_root = _verified_lifecycle_project(supplied_project)
    if Path.cwd().resolve() != project_root:
        raise MeridianError("integration abort must run from the canonical primary checkout")
    # Abort must stay possible when the queue link is stale, so it skips link checks.
    identity = resolve_task_identity(project_root, task_id, "existing", check_queue_links=False)
    _task_state, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    lease = _read_json_object(lease_path, "integration lease")
    staged = _read_json_object(integration_path, "staged integration state") if integration_path.is_file() else None
    if lease.get("task_id") != identity.canonical_id or (
        staged is not None and staged.get("task_id") != identity.canonical_id
    ):
        raise MeridianError("integration ownership does not match the requested task")
    merge_head = _merge_head_path(project_root)
    if merge_head.exists():
        aborted = _run_git(project_root, "merge", "--abort")
        if aborted.returncode != 0:
            raise MeridianError(aborted.stderr.strip() or "cannot abort the owned staged integration")
    _remove_owned_file(integration_path)
    _remove_owned_file(lease_path)
    return {"version": 1, "task_id": identity.canonical_id, "status": "aborted", "next_action": "inspect"}


def cleanup_task_worktree(
    task_id: str,
    worktree_root: Path | None,
    supplied_project: Path | None = None,
) -> dict[str, object]:
    project_root = _verified_lifecycle_project(supplied_project)
    if Path.cwd().resolve() != project_root:
        raise MeridianError("worktree cleanup must run from the canonical primary checkout")
    identity = resolve_task_identity(project_root, task_id, "existing")
    root = _effective_worktree_root(worktree_root)
    expected = _task_worktree_path_for_identity(project_root, root, identity)
    state_path, lease_path, integration_path = _lifecycle_paths(project_root, identity)
    registered_paths = {Path(item["worktree"]).resolve() for item in _git_worktrees(project_root)}
    if (
        expected not in registered_paths
        and not expected.exists()
        and _branch_commit(project_root, identity.branch_name) is None
        and not state_path.exists()
    ):
        return {"version": 1, "task_id": identity.canonical_id, "status": "cleaned", "already_cleaned": True}
    inspection, ready = inspect_task_worktree(
        identity.canonical_id,
        worktree_root,
        project_root,
        require_effective_worktree=False,
    )
    if lease_path.exists() or integration_path.exists():
        raise MeridianError("cleanup is blocked while an integration lease or staged merge is active")
    if not ready:
        raise MeridianError(f"cleanup preflight failed: {', '.join(inspection['errors'])}")
    if git_output(project_root, "status", "--porcelain"):
        raise MeridianError("primary checkout must be clean")
    task_commit = str(inspection["task_commit"])
    if _run_git(project_root, "merge-base", "--is-ancestor", task_commit, "main").returncode != 0:
        raise MeridianError("task commit is not integrated into main")
    origin = _run_git(project_root, "remote", "get-url", "origin")
    if origin.returncode == 0:
        remote_main = _run_git(project_root, "rev-parse", "--verify", "refs/remotes/origin/main")
        if remote_main.returncode != 0 or _run_git(
            project_root, "merge-base", "--is-ancestor", "main", "refs/remotes/origin/main"
        ).returncode != 0:
            raise MeridianError("local main is not proven pushed to origin/main")
    removed = _run_git(project_root, "worktree", "remove", str(inspection["worktree"]))
    if removed.returncode != 0:
        raise MeridianError(removed.stderr.strip() or "worktree removal failed; branch was retained")
    deleted = _run_git(project_root, "branch", "-d", identity.branch_name)
    if deleted.returncode != 0:
        raise MeridianError(deleted.stderr.strip() or "non-force branch deletion failed")
    _remove_owned_file(state_path)
    return {"version": 1, "task_id": identity.canonical_id, "status": "cleaned"}


def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _codex_managed_block(worktree_root: Path) -> str:
    root = str(worktree_root.expanduser().resolve())
    return "\n".join(
        [
            CODEX_MANAGED_BEGIN,
            f'default_permissions = "{CODEX_PERMISSION_PROFILE}"',
            "",
            f"[permissions.{CODEX_PERMISSION_PROFILE}]",
            'description = "Workspace access plus Meridian-managed task worktrees."',
            'extends = ":workspace"',
            "",
            f"[permissions.{CODEX_PERMISSION_PROFILE}.workspace_roots]",
            f"{_toml_quote(root)} = true",
            CODEX_MANAGED_END,
        ]
    )


def _replace_codex_managed_block(text: str, block: str) -> str:
    start = text.find(CODEX_MANAGED_BEGIN)
    if start >= 0:
        end = text.find(CODEX_MANAGED_END, start) + len(CODEX_MANAGED_END)
        text = text[:start] + text[end:]

    table = re.search(r"(?m)^\s*\[", text)
    insertion = table.start() if table is not None else len(text)
    prefix = text[:insertion].rstrip("\n")
    suffix = text[insertion:].strip("\n")
    parts = [part for part in (prefix, block, suffix) if part]
    return "\n\n".join(parts) + "\n"


def _without_top_level_default_permissions(text: str) -> str:
    """Remove the root selection while leaving comments and profile tables intact."""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            break
        if re.match(r"^\s*default_permissions\s*=", line):
            del lines[index]
            break
    return "".join(lines)


def _codex_expected_profile(root: Path) -> dict[str, object]:
    return {
        "description": "Workspace access plus Meridian-managed task worktrees.",
        "extends": ":workspace",
        "workspace_roots": {str(root): True},
    }


def _codex_profile_divergence(parsed: dict[str, object], root: Path) -> list[str]:
    """Name every field where the parsed profile differs from the one expected profile."""
    permissions = parsed.get("permissions")
    profile = permissions.get(CODEX_PERMISSION_PROFILE) if isinstance(permissions, dict) else None
    if not isinstance(profile, dict):
        return ["profile shape"]
    expected = _codex_expected_profile(root)
    differences = [
        key for key in sorted(set(profile) | set(expected)) if profile.get(key) != expected.get(key)
    ]
    if parsed.get("default_permissions") != CODEX_PERMISSION_PROFILE:
        differences.append("default_permissions")
    return differences


def _codex_header_patterns() -> tuple[re.Pattern[str], re.Pattern[str]]:
    name = re.escape(CODEX_PERMISSION_PROFILE)
    quoted = rf'(?:{name}|"{name}")'
    return (
        re.compile(rf"^\s*\[\s*permissions\s*\.\s*{quoted}\s*\]\s*(?:#.*)?$"),
        re.compile(rf"^\s*\[\s*permissions\s*\.\s*{quoted}\s*\.\s*workspace_roots\s*\]\s*(?:#.*)?$"),
    )


def _codex_markers_intact(text: str) -> bool:
    """Return whether one ordered marker pair encloses every managed piece present.

    The root selection, the profile table, and its workspace_roots table must each
    be inside the span or absent; a piece left outside means the host moved part of
    the block and ownership can only be recovered semantically.
    """
    if text.count(CODEX_MANAGED_BEGIN) != 1 or text.count(CODEX_MANAGED_END) != 1:
        return False
    start = text.index(CODEX_MANAGED_BEGIN)
    end = text.index(CODEX_MANAGED_END)
    if start >= end:
        return False
    profile_header, roots_header = _codex_header_patterns()
    selection = re.compile(r"^\s*default_permissions\s*=")
    offset = 0
    in_table = False
    inside_profile = False
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        within = start <= offset < end
        if bare.lstrip().startswith("["):
            in_table = True
            if (profile_header.match(bare) or roots_header.match(bare)) and not within:
                return False
            inside_profile = inside_profile or (within and bool(profile_header.match(bare)))
        elif not in_table and selection.match(bare) and not within:
            return False
        offset += len(line)
    return inside_profile


def _without_codex_profile_text(text: str) -> str:
    """Remove ownership markers, the root selection, and the managed profile tables.

    Raises MeridianError unless each managed table header appears exactly once as a
    plain table header, so unusual serializations are never edited heuristically.
    """
    profile_header, roots_header = _codex_header_patterns()
    marker = re.compile(r"^\s*#\s*MERIDIAN:(?:BEGIN|END)\s+worktree-permissions\b.*$")
    lines = text.splitlines(keepends=True)
    if sum(1 for line in lines if profile_header.match(line.rstrip("\r\n"))) != 1 or sum(
        1 for line in lines if roots_header.match(line.rstrip("\r\n"))
    ) != 1:
        raise MeridianError(
            f"Codex permission profile {CODEX_PERMISSION_PROFILE!r} is not serialized as exactly one plain "
            "profile table and one workspace_roots table; reconcile it manually"
        )
    kept: list[str] = []
    skipping = False
    for line in lines:
        bare = line.rstrip("\r\n")
        if bare.lstrip().startswith("["):
            skipping = bool(profile_header.match(bare) or roots_header.match(bare))
            if skipping:
                continue
        if skipping or marker.match(bare):
            continue
        kept.append(line)
    return _without_top_level_default_permissions("".join(kept))


def _plan_codex_ownership_repair(
    config_path: Path, text: str, parsed: dict[str, object], root: Path
) -> CodexConfigurationPlan:
    """Plan an ownership-metadata repair, or raise unless the profile is an exact semantic match."""
    differences = _codex_profile_divergence(parsed, root)
    if differences:
        raise MeridianError(
            f"Codex permission profile {CODEX_PERMISSION_PROFILE!r} exists without intact Meridian ownership "
            f"markers and differs from the expected profile in: {', '.join(differences)}; reconcile it manually"
        )
    stripped = _without_codex_profile_text(text)
    proposed = _replace_codex_managed_block(stripped, _codex_managed_block(root))
    try:
        reparsed = tomllib.loads(proposed)
    except tomllib.TOMLDecodeError as error:
        raise MeridianError(f"proposed Codex ownership repair would be invalid: {error}") from error
    if reparsed != parsed:
        raise MeridianError(
            "Codex ownership repair would change effective configuration beyond Meridian's markers; "
            "reconcile it manually"
        )
    return CodexConfigurationPlan(
        "repair-required",
        config_path,
        root,
        "permission-profile",
        proposed,
        "ownership-metadata-repair: the effective profile is identical; explicit --apply restores only "
        "Meridian's ownership markers and block position",
        text,
    )


def _plan_codex_ownership_repair_and_root_replacement(
    config_path: Path, text: str, parsed: dict[str, object], root: Path
) -> CodexConfigurationPlan | None:
    """Plan the one safe combined recovery, or return None for a normal refusal.

    Lost comments are not ownership evidence.  The profile's exact Meridian
    shape is, but only when it contains one enabled root that differs from the
    requested root.  Keep this predicate deliberately narrower than parsed
    divergence so foreign grants and unusual shapes cannot be adopted.
    """
    permissions = parsed.get("permissions")
    profile = permissions.get(CODEX_PERMISSION_PROFILE) if isinstance(permissions, dict) else None
    expected = _codex_expected_profile(root)
    if (
        parsed.get("default_permissions") != CODEX_PERMISSION_PROFILE
        or not isinstance(profile, dict)
        or set(profile) != set(expected)
        or profile.get("description") != expected["description"]
        or profile.get("extends") != expected["extends"]
    ):
        return None
    roots = profile.get("workspace_roots")
    if not isinstance(roots, dict) or len(roots) != 1 or list(roots.values()) != [True]:
        return None
    if roots == expected["workspace_roots"]:
        return None

    stripped = _without_codex_profile_text(text)
    proposed = _replace_codex_managed_block(stripped, _codex_managed_block(root))
    try:
        reparsed = tomllib.loads(proposed)
    except tomllib.TOMLDecodeError as error:
        raise MeridianError(f"proposed Codex repair and root replacement would be invalid: {error}") from error
    expected_parsed = copy.deepcopy(parsed)
    expected_parsed["permissions"][CODEX_PERMISSION_PROFILE]["workspace_roots"] = expected["workspace_roots"]  # type: ignore[index]
    if reparsed != expected_parsed:
        raise MeridianError(
            "Codex repair and root replacement would change effective configuration beyond the one root value; "
            "reconcile it manually"
        )
    return CodexConfigurationPlan(
        "repair-and-replace-required",
        config_path,
        root,
        "permission-profile",
        proposed,
        "ownership-metadata-repair-and-root-replacement: explicit --apply restores Meridian's ownership "
        "metadata and replaces the one configured worktree root",
        text,
    )


def plan_codex_configuration(
    config_path: Path,
    worktree_root: Path,
    requirements_path: Path | None = None,
) -> CodexConfigurationPlan:
    root = worktree_root.expanduser().resolve()
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise MeridianError("worktree root must not authorize the filesystem root or the user's home")
    text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise MeridianError(f"malformed Codex TOML at {config_path}: {error}") from error
    if "sandbox_mode" in parsed or "sandbox_workspace_write" in parsed:
        raise MeridianError("legacy Codex sandbox settings conflict with permission profiles")
    if requirements_path is not None and requirements_path.is_file():
        try:
            requirements = tomllib.loads(requirements_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as error:
            raise MeridianError(f"malformed managed Codex requirements at {requirements_path}: {error}") from error
        allowed = requirements.get("allowed_permission_profiles")
        if isinstance(allowed, dict) and allowed.get(CODEX_PERMISSION_PROFILE) is not True:
            raise MeridianError(
                f"managed Codex requirements do not allow permission profile {CODEX_PERMISSION_PROFILE!r}"
            )
    existing_profile = parsed.get("permissions", {}).get(CODEX_PERMISSION_PROFILE)
    managed_present = CODEX_MANAGED_BEGIN in text or CODEX_MANAGED_END in text
    if existing_profile is not None and not _codex_markers_intact(text):
        replacement = _plan_codex_ownership_repair_and_root_replacement(config_path, text, parsed, root)
        if replacement is not None:
            return replacement
        return _plan_codex_ownership_repair(config_path, text, parsed, root)
    if managed_present and not _codex_markers_intact(text):
        raise MeridianError("Codex configuration contains an incomplete or damaged Meridian-managed block")
    base_text = text
    if "default_permissions" in parsed and not managed_present:
        base_text = _without_top_level_default_permissions(text)
    proposed = _replace_codex_managed_block(base_text, _codex_managed_block(root))
    try:
        tomllib.loads(proposed)
    except tomllib.TOMLDecodeError as error:
        raise MeridianError(f"proposed Codex configuration would be invalid: {error}") from error
    current_model = "permission-profile" if "default_permissions" in parsed or "permissions" in parsed else "unconfigured"
    if proposed == text:
        return CodexConfigurationPlan("ready", config_path, root, current_model, None, "requested profile is already effective")
    return CodexConfigurationPlan("approval-required", config_path, root, current_model, proposed, "explicit --apply is required", text)


def print_codex_configuration_plan(plan: CodexConfigurationPlan) -> None:
    print(f"status: {plan.status}")
    print(f"config: {plan.config_path}")
    print(f"permission-model: {plan.current_model}")
    print(f"worktree-root: {plan.worktree_root}")
    print(f"detail: {plan.detail}")
    if plan.status in ("repair-required", "repair-and-replace-required") and plan.proposed_text is not None and plan.current_text is not None:
        suffix = "effective configuration is unchanged" if plan.status == "repair-required" else "repairs ownership metadata and replaces the worktree root"
        print(f"proposed-change (unified diff; {suffix}):")
        print(
            "".join(
                difflib.unified_diff(
                    plan.current_text.splitlines(keepends=True),
                    plan.proposed_text.splitlines(keepends=True),
                    fromfile=f"{plan.config_path.name} (current)",
                    tofile=f"{plan.config_path.name} (repaired)",
                )
            ),
            end="",
        )
    elif plan.proposed_text is not None:
        print("proposed-change:")
        print(_codex_managed_block(plan.worktree_root))


def _write_exclusive_backup(path: Path, backup: Path) -> None:
    """Copy the current bytes to a new owner-only file, never replacing an existing backup."""
    descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(path.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            backup.unlink()
        except OSError:
            pass
        raise


def _unused_repair_backup(path: Path) -> Path:
    candidate = path.with_name(path.name + ".meridian-repair.bak")
    index = 0
    while candidate.exists() or candidate.is_symlink():
        index += 1
        candidate = path.with_name(f"{path.name}.meridian-repair.{index}.bak")
    return candidate


def apply_codex_configuration(plan: CodexConfigurationPlan) -> bool:
    if plan.proposed_text is None:
        return False
    path = plan.config_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if plan.status in ("repair-required", "repair-and-replace-required"):
        if not path.is_file() or path.read_text(encoding="utf-8") != plan.current_text:
            raise MeridianError("Codex configuration changed since it was planned; rerun --check")
        _write_exclusive_backup(path, _unused_repair_backup(path))
    else:
        backup = path.with_name(path.name + ".meridian.bak")
        if path.exists() and not backup.exists():
            _write_exclusive_backup(path, backup)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(plan.proposed_text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return True


def _directory_setup_state(root: Path) -> tuple[str, str]:
    if not root.exists():
        return "missing", f"create {root} with mode 0700"
    if not root.is_dir():
        return "blocked", f"worktree root exists but is not a directory: {root}"
    details = root.stat()
    if hasattr(os, "getuid") and details.st_uid != os.getuid():
        return "blocked", f"worktree root is not owned by the current user: {root}"
    mode = stat.S_IMODE(details.st_mode)
    if mode != 0o700:
        return "repair-required", f"set mode 0700 on {root} (currently {mode:04o})"
    return "ready", "no directory change"


CODEX_SKILL_NAMES = ("meridian-lean-delivery", "meridian-governed-sdd")


def _framework_skill_links(framework_root: Path, home: Path) -> tuple[tuple[str, Path, str, str], ...]:
    target_root = (framework_root / "skills").resolve()
    checkout = _run_git(framework_root, "rev-parse", "--show-toplevel")
    if checkout.returncode != 0 or Path(checkout.stdout.strip()).resolve() != framework_root.resolve():
        reason = "framework root is not the root of a Git checkout"
        return tuple((name, home / ".agents/skills" / name, "skipped", reason) for name in CODEX_SKILL_NAMES)
    missing_assets = [name for name in CODEX_SKILL_NAMES if not (target_root / name / "SKILL.md").is_file()]
    if missing_assets:
        reason = "framework checkout does not contain " + ", ".join(
            f"skills/{name}/SKILL.md" for name in missing_assets
        )
        return tuple((name, home / ".agents/skills" / name, "skipped", reason) for name in CODEX_SKILL_NAMES)
    links: list[tuple[str, Path, str, str]] = []
    for name in CODEX_SKILL_NAMES:
        path = home / ".agents/skills" / name
        target = target_root / name
        if path.is_symlink():
            observed = os.readlink(path)
            state = "ready" if path.resolve() == target else "conflict"
            detail = str(target) if state == "ready" else f"points to {observed} (expected {target})"
        elif path.exists():
            state = "blocked"
            detail = f"path exists as {('directory' if path.is_dir() else 'regular file')}"
        else:
            state = "missing"
            detail = f"create symlink to {target}"
        links.append((name, path, state, detail))
    return tuple(links)


def _aggregate_skill_state(links: tuple[tuple[str, Path, str, str], ...]) -> str:
    states = {state for _, _, state, _ in links}
    if "blocked" in states:
        return "blocked"
    if "conflict" in states:
        return "conflict"
    if states == {"skipped"}:
        return "skipped"
    if "missing" in states:
        return "missing"
    return "ready"


def _stale_codex_skill_warnings(home: Path) -> list[str]:
    return [
        f"stale Codex skill copy: {path}"
        for path in sorted((home / ".codex/skills").glob("meridian-*"))
    ]


def _setup_codex_state(plan: CodexConfigurationPlan) -> str:
    if plan.status in ("ready", "repair-required", "repair-and-replace-required"):
        return plan.status
    text = plan.current_text or ""
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return "blocked"
    permissions = parsed.get("permissions")
    existing = permissions.get(CODEX_PERMISSION_PROFILE) if isinstance(permissions, dict) else None
    if isinstance(existing, dict) and _codex_markers_intact(text):
        expected = _codex_expected_profile(plan.worktree_root)
        differing = [key for key in sorted(set(existing) | set(expected)) if existing.get(key) != expected.get(key)]
        roots = existing.get("workspace_roots")
        enabled_roots = (
            [value for value, allowed in roots.items() if allowed is True]
            if isinstance(roots, dict)
            else []
        )
        if differing == ["workspace_roots"] and len(enabled_roots) == 1:
            return "different-root"
        return "blocked"
    return "unconfigured"


def codex_profile_root_mismatch(config_path: Path, resolved_root: Path) -> str | None:
    if not config_path.is_file():
        return None
    try:
        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    permissions = parsed.get("permissions")
    profile = permissions.get(CODEX_PERMISSION_PROFILE) if isinstance(permissions, dict) else None
    roots = profile.get("workspace_roots") if isinstance(profile, dict) else None
    if not isinstance(roots, dict):
        return None
    enabled = [Path(value).expanduser().resolve() for value, allowed in roots.items() if allowed is True]
    if len(enabled) == 1 and enabled[0] != resolved_root:
        return f"profile={enabled[0]} resolved={resolved_root}"
    return None


CLAUDE_PROJECT_ALLOWLIST = (
    "Bash(git status:*)",
    "Bash(git diff:*)",
    "Bash(git log:*)",
    "Bash(git show:*)",
    "Bash(git rev-parse:*)",
    "Bash(git merge-base:*)",
    "Bash(git branch --show-current)",
    "Bash(git add:*)",
    "Bash(git switch:*)",
    "Bash(git commit -m:*)",
    "Bash(git merge --ff-only:*)",
    "Bash(git push origin main)",
    "Bash(git worktree list:*)",
    "Bash(meridian worktree path:*)",
    "Bash(meridian worktree prepare:*)",
    "Bash(meridian worktree check:*)",
    "Bash(meridian worktree evidence:*)",
    "Bash(meridian worktree closure-status:*)",
    "Bash(meridian worktree cleanup:*)",
    "Bash(meridian worktree integrate stage:*)",
    "Bash(meridian worktree integrate finalize:*)",
    "Bash(meridian worktree integrate abort:*)",
    "Bash(python3 scripts/meridian.py worktree path:*)",
    "Bash(python3 scripts/meridian.py worktree prepare:*)",
    "Bash(python3 scripts/meridian.py worktree check:*)",
    "Bash(python3 scripts/meridian.py worktree evidence:*)",
    "Bash(python3 scripts/meridian.py worktree closure-status:*)",
    "Bash(python3 scripts/meridian.py worktree cleanup:*)",
    "Bash(python3 scripts/meridian.py worktree integrate stage:*)",
    "Bash(python3 scripts/meridian.py worktree integrate finalize:*)",
    "Bash(python3 scripts/meridian.py worktree integrate abort:*)",
    "Bash(python3 scripts/check_repository.py)",
    "Bash(python3 -m unittest discover -s tests)",
)


def plan_claude_project_allowlist(project_root: Path) -> ClaudeConfigurationPlan:
    """Plan one explicit, project-local Claude Code command allowlist update."""
    settings_path = project_root.expanduser().resolve() / ".claude/settings.local.json"
    if settings_path.exists() and not settings_path.is_file():
        return ClaudeConfigurationPlan(
            "blocked", settings_path, None, "Claude settings path is not a regular file"
        )
    current_text = settings_path.read_text(encoding="utf-8") if settings_path.is_file() else ""
    try:
        settings = json.loads(current_text) if current_text else {}
    except json.JSONDecodeError as error:
        return ClaudeConfigurationPlan(
            "blocked", settings_path, None, f"malformed Claude settings: {error}", current_text
        )
    if not isinstance(settings, dict):
        return ClaudeConfigurationPlan(
            "blocked", settings_path, None, "Claude settings must contain a JSON object", current_text
        )
    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        return ClaudeConfigurationPlan(
            "blocked", settings_path, None, "Claude settings permissions must contain an object", current_text
        )
    allow = permissions.get("allow", [])
    if not isinstance(allow, list) or not all(isinstance(item, str) for item in allow):
        return ClaudeConfigurationPlan(
            "blocked", settings_path, None, "Claude settings permissions.allow must contain strings", current_text
        )
    missing = [item for item in CLAUDE_PROJECT_ALLOWLIST if item not in allow]
    if not missing:
        return ClaudeConfigurationPlan(
            "ready", settings_path, None, "project command allowlist is already effective", current_text
        )
    proposed = copy.deepcopy(settings)
    proposed_permissions = copy.deepcopy(permissions)
    proposed_permissions["allow"] = [*allow, *missing]
    proposed["permissions"] = proposed_permissions
    return ClaudeConfigurationPlan(
        "approval-required",
        settings_path,
        proposed,
        "explicit --apply adds the missing project command allowlist entries",
        current_text,
    )


def apply_claude_project_allowlist(plan: ClaudeConfigurationPlan) -> bool:
    if plan.status == "blocked":
        raise MeridianError(f"Claude project allowlist is blocked: {plan.detail}")
    if plan.proposed_settings is None:
        return False
    current_text = plan.settings_path.read_text(encoding="utf-8") if plan.settings_path.is_file() else ""
    if current_text != plan.current_text:
        raise MeridianError("Claude settings changed since they were planned; rerun --check")
    _write_json_atomic(plan.settings_path, plan.proposed_settings)
    return True


def plan_setup(
    worktree_root: Path | None,
    codex_config: Path,
    *,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    user_config: Path | None = None,
    framework_root: Path | None = None,
    project_root: Path | None = None,
) -> SetupPlan:
    home = (home or Path.home()).expanduser().resolve()
    framework_root = (framework_root or Path(__file__).resolve().parents[1]).expanduser().resolve()
    project_root = (project_root or Path.cwd()).expanduser().resolve()
    environment = environment or os.environ
    resolution = resolve_worktree_root(
        worktree_root,
        environment=environment,
        home=home,
        config_path=user_config,
    )
    # Applying with a higher-precedence source must never overwrite malformed
    # lower-precedence user state without first reporting it.
    existing_config = _read_user_configuration(resolution.config_path)
    default_root = home / ".meridian/worktrees"
    expected_config = {"version": 1, "worktreeRoot": str(resolution.path)}
    if resolution.path == default_root:
        config_action = "remove" if existing_config is not None else "none"
    elif existing_config == expected_config:
        config_action = "none"
    else:
        config_action = "write"

    directory_state, directory_change = _directory_setup_state(resolution.path)
    codex_plan: CodexConfigurationPlan | None = None
    try:
        codex_plan = plan_codex_configuration(codex_config, resolution.path)
        codex_state = _setup_codex_state(codex_plan)
        if codex_state == "blocked":
            parsed = tomllib.loads(codex_plan.current_text or "")
            differences = _codex_profile_divergence(parsed, resolution.path)
            codex_detail = (
                "owned Codex profile has unexpected divergence in: "
                + ", ".join(differences)
            )
        else:
            codex_detail = codex_plan.detail
    except MeridianError as error:
        codex_state = "blocked"
        codex_detail = str(error)

    claude_plan = plan_claude_project_allowlist(project_root)
    claude_state = claude_plan.status
    claude_detail = claude_plan.detail

    changes: list[str] = []
    if directory_state != "ready":
        changes.append(directory_change)
    if config_action == "write":
        changes.append(f"write {resolution.config_path} with version 1 and worktreeRoot {resolution.path}")
    elif config_action == "remove":
        changes.append(f"remove {resolution.config_path} because the built-in default needs no configuration")
    if codex_plan is not None and codex_plan.proposed_text is not None:
        verb = "repair" if codex_state in ("repair-required", "repair-and-replace-required") else "configure"
        changes.append(f"{verb} Codex permission profile in {codex_config} for {resolution.path}")
    if claude_plan.proposed_settings is not None:
        changes.append(f"add project Claude Code command allowlist in {claude_plan.settings_path}")
    if directory_state == "blocked" or codex_state == "blocked" or claude_state == "blocked":
        changes = ["none; setup is blocked before mutation"]
    elif not changes:
        changes.append("none")
    warnings: list[str] = []
    skill_links = _framework_skill_links(framework_root, home)
    skill_links_state = _aggregate_skill_state(skill_links)
    if skill_links_state in ("blocked", "conflict"):
        changes = ["none; setup is blocked before mutation"]
    elif skill_links_state == "missing" and changes != ["none; setup is blocked before mutation"]:
        changes.append(f"create missing Codex skill links in {home / '.agents/skills'}")
    meridian_root_value = environment.get("MERIDIAN_ROOT")
    meridian_root_state = (
        "unset"
        if meridian_root_value is None
        else "ready"
        if Path(meridian_root_value).expanduser().resolve() == framework_root
        else "mismatch"
    )
    if meridian_root_state == "mismatch":
        warnings.append(f"MERIDIAN_ROOT differs from framework root: {meridian_root_value}")
    warnings.extend(_stale_codex_skill_warnings(home))
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if resolution.path == temporary_root or temporary_root in resolution.path.parents:
        warnings.append("resolved root is under a temporary directory and is unsuitable for persistent setup")
    probe_path = resolution.path
    while not probe_path.exists() and probe_path != probe_path.parent:
        probe_path = probe_path.parent
    if not probe_path.is_dir():
        probe_path = probe_path.parent
    repository_probe = _run_git(probe_path, "rev-parse", "--show-toplevel")
    if repository_probe.returncode == 0:
        repository_root = Path(repository_probe.stdout.strip()).resolve()
        if resolution.path == repository_root or repository_root in resolution.path.parents:
            warnings.append("resolved root is inside the current repository and is unsuitable for machine setup")
    return SetupPlan(
        resolution,
        codex_config,
        directory_state,
        codex_state,
        codex_plan,
        codex_detail,
        claude_state,
        claude_plan,
        claude_detail,
        config_action,
        framework_root,
        skill_links,
        skill_links_state,
        meridian_root_state,
        tuple(changes),
        tuple(warnings),
    )


def print_setup_plan(plan: SetupPlan) -> None:
    print(f"worktree-root: {plan.resolution.path}")
    print(f"worktree-root-source: {plan.resolution.source}")
    print(f"directory-exists: {'no' if plan.directory_state == 'missing' else 'yes'}")
    print(f"directory-owner-only: {'yes' if plan.directory_state == 'ready' else 'no'}")
    print(f"directory: {plan.directory_state}")
    print(f"codex-profile: {plan.codex_state}")
    print(f"codex-detail: {plan.codex_detail}")
    print(f"claude-project-allowlist: {plan.claude_state}")
    print(f"claude-detail: {plan.claude_detail}")
    mismatch = codex_profile_root_mismatch(
        plan.codex_config,
        plan.resolution.path,
    )
    if mismatch:
        print(f"codex-root-mismatch: {mismatch}")
    print(f"codex-skill-links: {plan.skill_links_state}")
    for name, path, state, detail in plan.skill_links:
        print(f"codex-skill-{name}: {state} ({path}; {detail})")
    print(f"MERIDIAN_ROOT: {plan.meridian_root_state}")
    print(f"shell-profile-MERIDIAN_ROOT: export MERIDIAN_ROOT={plan.framework_root}")
    print('shell-profile-PATH: export PATH="$MERIDIAN_ROOT/bin:$PATH"')
    for warning in plan.warnings:
        print(f"warning: {warning}")
    print("changes:")
    for change in plan.changes:
        print(f"- {change}")


def apply_setup(plan: SetupPlan) -> bool:
    if (
        plan.directory_state == "blocked"
        or plan.codex_state == "blocked"
        or plan.claude_state == "blocked"
        or plan.skill_links_state in ("blocked", "conflict")
        or plan.codex_plan is None
    ):
        detail = (
            next(detail for _, _, state, detail in plan.skill_links if state in ("blocked", "conflict"))
            if plan.skill_links_state in ("blocked", "conflict")
            else plan.codex_detail
            if plan.codex_state == "blocked"
            else plan.claude_detail
            if plan.claude_state == "blocked"
            else _directory_setup_state(plan.resolution.path)[1]
        )
        raise MeridianError(f"setup is blocked: {detail}")
    changed = False
    root = plan.resolution.path
    if plan.directory_state == "missing":
        root.mkdir(parents=True, mode=0o700)
        os.chmod(root, 0o700)
        changed = True
    elif plan.directory_state == "repair-required":
        os.chmod(root, 0o700)
        changed = True
    if plan.config_action == "write":
        _write_json_atomic(
            plan.resolution.config_path,
            {"version": 1, "worktreeRoot": str(root)},
        )
        changed = True
    elif plan.config_action == "remove":
        plan.resolution.config_path.unlink()
        changed = True
    changed = apply_codex_configuration(plan.codex_plan) or changed
    changed = apply_claude_project_allowlist(plan.claude_plan) or changed
    missing_links = [
        (path, plan.framework_root / "skills" / name)
        for name, path, state, _ in plan.skill_links
        if state == "missing"
    ]
    if missing_links:
        skills_root = missing_links[0][0].parent
        if not skills_root.exists():
            skills_root.mkdir(parents=True, mode=0o700)
            os.chmod(skills_root, 0o700)
            changed = True
        for path, target in missing_links:
            path.symlink_to(target)
            changed = True
    return changed


def codex_doctor(
    project_root: Path,
    config_path: Path,
    worktree_root: Path,
    *,
    framework_root: Path | None = None,
    home: Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        plan = plan_codex_configuration(config_path, worktree_root)
        result["permission-model"] = plan.status
        result["profile-ownership"] = (
            "ready"
            if plan.status == "ready"
            else plan.status
            if plan.status in ("repair-required", "repair-and-replace-required")
            else "not-applicable"
        )
    except MeridianError:
        result["permission-model"] = "blocked"
        result["profile-ownership"] = "blocked"
    mismatch = codex_profile_root_mismatch(config_path, worktree_root)
    if mismatch:
        result["codex-root-mismatch"] = mismatch
    text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        parsed = {}
    trusted = any(
        isinstance(settings, dict)
        and settings.get("trust_level") == "trusted"
        and Path(path).expanduser().resolve() == project_root.resolve()
        for path, settings in parsed.get("projects", {}).items()
    )
    result["project-trust"] = "ready" if trusted else "approval-required"
    rules = project_root / ".codex/rules/meridian.rules"
    result["command-policy"] = "ready" if rules.is_file() and trusted else ("approval-required" if rules.is_file() else "blocked")
    claude_plan = plan_claude_project_allowlist(project_root)
    result["claude-project-allowlist"] = claude_plan.status
    lifecycle_policy = "approval-required"
    codex_executable = shutil.which("codex")
    if result["command-policy"] == "ready" and codex_executable:
        probes = (
            ("path", "TASK-1", "--worktree-root", str(worktree_root)),
            ("prepare", "TASK-1", "--worktree-root", str(worktree_root), "--format", "json"),
            ("check", "TASK-1", "--worktree-root", str(worktree_root), "--format", "json"),
            ("integrate", "stage", "TASK-1", "--worktree-root", str(worktree_root), "--evidence", "handoff.json", "--format", "json"),
            ("integrate", "finalize", "TASK-1", "--evidence", "candidate.json", "--format", "json"),
            ("integrate", "abort", "TASK-1", "--format", "json"),
            ("cleanup", "TASK-1", "--worktree-root", str(worktree_root), "--format", "json"),
        )
        decisions: list[str | None] = []
        for probe in probes:
            checked = subprocess.run(
                [codex_executable, "execpolicy", "check", "--rules", str(rules), "--", "meridian", "worktree", *probe],
                text=True,
                capture_output=True,
                check=False,
            )
            try:
                decisions.append(json.loads(checked.stdout).get("decision") if checked.returncode == 0 else None)
            except json.JSONDecodeError:
                decisions.append(None)
        lifecycle_policy = "ready" if decisions and all(item == "allow" for item in decisions) else "blocked"
    elif result["command-policy"] == "blocked":
        lifecycle_policy = "blocked"
    result["lifecycle-command-policy"] = lifecycle_policy
    root_write = "approval-required"
    if result["permission-model"] in ("ready", "repair-required", "repair-and-replace-required") and worktree_root.is_dir():
        try:
            descriptor, probe_name = tempfile.mkstemp(prefix=".meridian-codex-probe-", dir=worktree_root)
            os.close(descriptor)
            Path(probe_name).unlink()
            root_write = "ready"
        except OSError:
            root_write = "blocked"
    result["worktree-root-write"] = root_write
    result["git-metadata"] = "ready" if lifecycle_policy == "ready" else "approval-required"
    home = (home or Path.home()).expanduser().resolve()
    framework_root = (framework_root or Path(__file__).resolve().parents[1]).expanduser().resolve()
    result["skill-links"] = _aggregate_skill_state(_framework_skill_links(framework_root, home))
    meridian_root_value = (environment or os.environ).get("MERIDIAN_ROOT")
    result["MERIDIAN_ROOT"] = (
        "unset"
        if meridian_root_value is None
        else "ready"
        if Path(meridian_root_value).expanduser().resolve() == framework_root
        else "mismatch"
    )
    return result


class IntegrationValidationOutcome(str, Enum):
    """Validation scope selected for a serialized task-worktree integration."""

    REUSE = "REUSE"
    BOUNDED = "BOUNDED"
    FULL = "FULL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class IntegrationValidationDecision:
    outcome: IntegrationValidationOutcome
    reason: str


def _paths_interact(left: str, right: str) -> bool:
    """Return whether normalized repository paths are equal or nested."""
    left_parts = Path(left).parts
    right_parts = Path(right).parts
    shortest = min(len(left_parts), len(right_parts))
    return left_parts[:shortest] == right_parts[:shortest]


def decide_integration_validation(
    *,
    evidence_complete: bool,
    validated_task_commit: str,
    current_task_commit: str,
    validated_base_commit: str,
    current_main_commit: str,
    validated_base_is_task_ancestor: bool,
    full_validation_required: bool,
    validated_task_is_current_ancestor: bool = False,
    relevant_tree_unchanged_after_validation: bool = False,
    interaction_assessment_complete: bool = False,
    task_paths: tuple[str, ...] = (),
    main_advanced_paths: tuple[str, ...] = (),
    task_dependencies: tuple[str, ...] = (),
    main_advanced_dependencies: tuple[str, ...] = (),
    task_behavioral_surfaces: tuple[str, ...] = (),
    main_advanced_behavioral_surfaces: tuple[str, ...] = (),
) -> IntegrationValidationDecision:
    """Choose the integration validation scope from durable evidence.

    ``REUSE`` and ``BOUNDED`` both require the mandatory bounded gate after the
    no-commit merge. ``REUSE`` means current ``main`` is the validated base;
    ``BOUNDED`` records a deterministic independent-change comparison.
    """
    if not evidence_complete:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.BLOCKED,
            "validation evidence is missing or incomplete",
        )
    if validated_task_commit != current_task_commit and not (
        validated_task_is_current_ancestor and relevant_tree_unchanged_after_validation
    ):
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.BLOCKED,
            "the task-relevant tree changed or cannot be proven unchanged after validation",
        )
    if not validated_base_is_task_ancestor:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.BLOCKED,
            "the validated base is not an ancestor of the task commit",
        )
    if full_validation_required:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.FULL,
            "the task explicitly requires full combined-tree validation",
        )
    if current_main_commit == validated_base_commit:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.REUSE,
            "current main equals the validated base",
        )
    if not interaction_assessment_complete:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.BLOCKED,
            "independence from advanced main cannot be established",
        )

    path_interaction = any(
        _paths_interact(task_path, main_path)
        for task_path in task_paths
        for main_path in main_advanced_paths
    )
    dependency_interaction = bool(set(task_dependencies) & set(main_advanced_dependencies))
    behavioral_interaction = bool(
        set(task_behavioral_surfaces) & set(main_advanced_behavioral_surfaces)
    )
    if path_interaction or dependency_interaction or behavioral_interaction:
        return IntegrationValidationDecision(
            IntegrationValidationOutcome.FULL,
            "advanced main materially interacts with the declared task surface",
        )
    return IntegrationValidationDecision(
        IntegrationValidationOutcome.BOUNDED,
        "advanced main is independent of the declared task surface",
    )


@dataclass(frozen=True)
class ManagedFile:
    source: Path
    target: Path


@dataclass(frozen=True)
class PlanItem:
    file: ManagedFile
    action: str
    detail: str
    problems: tuple[str, ...] = ()


@dataclass(frozen=True)
class Capability:
    migration: str
    present: bool
    evidence: str


@dataclass(frozen=True)
class CapabilityMove:
    """One declared relocation of an exact protected marker block."""

    stage: str
    source_path: Path
    source_capability: str
    source_version: int
    source_sha256: str
    target_path: Path
    target_capability: str
    target_version: int
    target_sha256: str
    migration: str


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
    adr_log: Path
    handoff_root: Path
    review_root: Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    def __str__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            text += f"-{self.prerelease}"
        if self.build:
            text += f"+{self.build}"
        return text


_SEMVER_IDENTIFIER = r"[0-9A-Za-z-]+"
_SEMVER_PATTERN = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    rf"(?:-({_SEMVER_IDENTIFIER}(?:\.{_SEMVER_IDENTIFIER})*))?"
    rf"(?:\+({_SEMVER_IDENTIFIER}(?:\.{_SEMVER_IDENTIFIER})*))?"
)


def parse_semver(value: str) -> SemVer:
    """Parse `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`.

    Used only for display and the persist-time guard; `version_key()` remains the
    comparator for upgrade planning.
    """
    match = _SEMVER_PATTERN.fullmatch(value)
    if match is None:
        raise MeridianError(f"invalid framework version: {value}")
    major, minor, patch, prerelease, build = match.groups()
    return SemVer(int(major), int(minor), int(patch), prerelease or "", build or "")


def read_raw_version(framework_root: Path) -> str:
    version_file = framework_root / "VERSION"
    if not version_file.is_file():
        raise MeridianError(f"framework VERSION file is missing: {version_file}")
    return version_file.read_text(encoding="utf-8").strip()


def require_release_version(framework_root: Path) -> None:
    """Reject a prerelease framework VERSION before it can become durable."""
    version = parse_semver(read_raw_version(framework_root))
    if version.prerelease:
        raise MeridianError(
            f"framework VERSION {version} is a prerelease; a prerelease version cannot be "
            "persisted into a manifest, migration, or release record"
        )


def read_version(framework_root: Path) -> str:
    """Return the framework version without build metadata, which never becomes durable."""
    raw = read_raw_version(framework_root)
    match = _SEMVER_PATTERN.fullmatch(raw)
    if match is not None and match.group(5):
        return raw.split("+", 1)[0]
    return raw


def version_key(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError as error:
        raise MeridianError(f"invalid framework version: {value}") from error


def semver_precedence_key(version: SemVer) -> tuple[object, ...]:
    """Return a SemVer precedence key; build metadata is intentionally ignored."""
    prerelease: tuple[tuple[int, object], ...]
    if version.prerelease:
        prerelease = tuple(
            (0, int(identifier)) if identifier.isdigit() else (1, identifier)
            for identifier in version.prerelease.split(".")
        )
        release_rank = 0
    else:
        prerelease = ()
        release_rank = 1
    return (version.major, version.minor, version.patch, release_rank, prerelease)


def release_kind_from_body(body: str) -> str:
    first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    if first_line.startswith("CLI-only release:"):
        return "CLI-only"
    if first_line.startswith("Template-changing release:"):
        return "template-changing"
    raise ValueError("release body has no recognized kind line")


def fetch_latest_release(
    installed_version: str,
    *,
    urlopen_fn=None,
) -> tuple[str, str]:
    """Return the latest release version and kind from GitHub's public API."""
    request = Request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"meridian/{installed_version}",
        },
    )
    opener = urlopen if urlopen_fn is None else urlopen_fn
    with opener(request, timeout=LATEST_RELEASE_TIMEOUT_SECONDS) as response:
        payload = response.read(LATEST_RELEASE_RESPONSE_LIMIT + 1)
    if len(payload) > LATEST_RELEASE_RESPONSE_LIMIT:
        raise ValueError("response exceeds 1 MiB")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("response is not valid UTF-8 JSON") from error
    if not isinstance(document, dict):
        raise ValueError("response root is not an object")
    tag_name = document.get("tag_name")
    body = document.get("body")
    if not isinstance(tag_name, str) or not tag_name.startswith("v"):
        raise ValueError("response has no valid v-prefixed tag_name")
    if not isinstance(body, str):
        raise ValueError("response has no release body")
    latest_version = tag_name[1:]
    parse_semver(latest_version)
    return latest_version, release_kind_from_body(body)


def run_self_check(framework_root: Path, *, urlopen_fn=None) -> int:
    """Print the installed/latest comparison without mutating local state."""
    installed_version = read_raw_version(framework_root)
    installed = parse_semver(installed_version)
    print(f"Installed: {installed_version}")
    try:
        latest_version, release_kind = fetch_latest_release(
            installed_version,
            urlopen_fn=urlopen_fn,
        )
        latest = parse_semver(latest_version)
    except HTTPError as error:
        print("Status: UNKNOWN")
        print(f"Reason: GitHub returned HTTP {error.code}")
        return SELF_CHECK_UNKNOWN
    except (HTTPException, URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", error)
        print("Status: UNKNOWN")
        print(f"Reason: network error: {reason}")
        return SELF_CHECK_UNKNOWN
    except (MeridianError, ValueError) as error:
        print("Status: UNKNOWN")
        print(f"Reason: malformed response: {error}")
        return SELF_CHECK_UNKNOWN

    print(f"Latest: {latest_version}")
    print(f"Kind: {release_kind}")
    if semver_precedence_key(latest) > semver_precedence_key(installed):
        print("Status: UPDATE_AVAILABLE")
        return SELF_CHECK_UPDATE_AVAILABLE
    print("Status: UP_TO_DATE")
    return 0


def latest_migration_to(framework_root: Path, upto: str | None = None) -> str:
    """Return the newest migration baseline, or the release itself for an empty ledger."""
    limit = upto or read_version(framework_root)
    versions = [
        str(json.loads(path.read_text(encoding="utf-8"))["to"])
        for path in (framework_root / "migrations").glob("*.json")
    ]
    if not versions:
        return limit
    eligible = [version for version in versions if version_key(version) <= version_key(limit)]
    if not eligible:
        raise MeridianError(f"no migration baseline exists at or below framework version {limit}")
    return max(eligible, key=version_key)


def manifest_baseline_version(manifest: dict[str, object]) -> str:
    """Read the explicit baseline version, with compatibility for legacy manifests."""
    return str(manifest.get("workflowBaselineVersion", manifest.get("frameworkVersion", "")))


def managed_files_for_workflow(workflow: Path, mode: str) -> list[ManagedFile]:
    if not workflow.is_dir():
        raise MeridianError(f"workflow template is missing: {workflow}")

    paths = [
        Path("PROJECT_WORKFLOW.md"),
        Path("AGENTS.md"),
        Path("CLAUDE.md"),
        Path("LANGUAGE_POLICY.md"),
    ]
    if mode == "lean-delivery":
        paths.extend(
            [
                Path("docs/CONTEXT_BUDGET_POLICY.md"),
                Path("docs/EXECUTION_EVIDENCE_PROFILE.md"),
            ]
        )
    if mode == "governed-sdd":
        paths.extend(
            [
                Path("tasks/TASK_BLUEPRINT.md"),
                *[
                    item.relative_to(workflow)
                    for item in sorted((workflow / "docs").rglob("*.md"))
                ],
            ]
        )
    # Packaged legacy baselines predate Codex policy files. Include each file
    # when the particular workflow snapshot supplies it, without making a
    # historical adoption baseline claim a file it never shipped.
    for codex_path in (Path(".codex/rules/meridian.rules"), Path(".codex/hooks.json")):
        if (workflow / codex_path).is_file():
            paths.append(codex_path)

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


def marker_declaring_migrations(framework_root: Path) -> dict[tuple[str, int], str]:
    """Map every declared (capability, version) pair to the migration id that
    introduces it — via `capability`/`capabilityVersion`, a `capabilities`
    list entry, or a `capabilityMoves` source/target — so a capped upgrade can
    tell whether a marker version present in the live template belongs to an
    excluded migration. A pair declared more than once keeps its first
    (earliest) declaring migration, in file order."""
    result: dict[tuple[str, int], str] = {}

    def record(pair: tuple[str, int], migration_id: str) -> None:
        result.setdefault(pair, migration_id)

    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        migration_id = str(data["id"])
        for capability, version in migration_capability_entries(data):
            record((capability, version), migration_id)
        for move in migration_capability_moves(data):
            record((move.source_capability, move.source_version), migration_id)
            record((move.target_capability, move.target_version), migration_id)
    return result


def strip_marker_block(text: str, capability: str, version: int) -> str:
    """Remove one complete exact marker block, leaving surrounding text
    untouched. Mirrors `marker_blocks()`'s pattern; used to synthesize a
    template as it existed before an excluded migration introduced or bumped
    one of its markers."""
    pattern = re.compile(
        rf"<!-- MERIDIAN:BEGIN capability={re.escape(capability)} v{version} -->\n?.*?"
        r"<!-- MERIDIAN:END -->\n?",
        re.DOTALL,
    )
    return pattern.sub("", text, count=1)


def capped_managed_files(
    framework_root: Path,
    mode: str,
    baseline_root: Path,
    excluded_migration_ids: set[str],
    scratch_dir: Path,
) -> list[ManagedFile]:
    """`managed_files()`, substituting a synthesized capped template for any
    file that carries a marker block declared by an excluded migration, so
    the live (always-latest) template cannot leak a change gated to a
    migration a capped upgrade must stop before.

    Stripping the excluded marker straight out of the live template would
    leave a fragment missing whatever unrelated content the file already had
    at the installed baseline (the `--replace` fast path would then apply
    that fragment wholesale). Instead, build the capped content up from the
    installed baseline, splicing in only the marker adds/supersessions the
    live template declares via a *non*-excluded migration, reusing
    `append_only_new_markers`'s own add/supersede rules by treating the
    baseline as if it were both the local file and the base of a normal
    upgrade. A file with no baseline snapshot yet (a new managed file, e.g.
    one migration 037 alone introduces) is returned unchanged — its content
    already reflects only the migrations that created it."""
    declaring = marker_declaring_migrations(framework_root)
    result = []
    for item in managed_files(framework_root, mode):
        base_path = baseline_root / item.target
        if not base_path.is_file():
            result.append(item)
            continue
        target_text = item.source.read_text(encoding="utf-8")
        base_text = base_path.read_text(encoding="utf-8")
        filtered_target = target_text
        for capability, version in marker_pairs(target_text):
            if declaring.get((capability, version)) in excluded_migration_ids:
                filtered_target = strip_marker_block(filtered_target, capability, version)
        spliced = append_only_new_markers(base_text, base_text, filtered_target)
        capped_text = base_text if spliced is None else spliced
        if capped_text == target_text:
            result.append(item)
            continue
        scratch_dir.mkdir(parents=True, exist_ok=True)
        capped_path = scratch_dir / item.target
        capped_path.parent.mkdir(parents=True, exist_ok=True)
        capped_path.write_text(capped_text, encoding="utf-8")
        result.append(ManagedFile(source=capped_path, target=item.target))
    return result


def _required_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise MeridianError(f"{label} must be a JSON object")
    return value


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MeridianError(f"{label} must be a non-empty string")
    return value


def _required_positive_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise MeridianError(f"{label} must be a positive integer")
    return value


def _required_string_list(value: object, label: str, *, non_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or (non_empty and not value):
        qualifier = "a non-empty" if non_empty else "a"
        raise MeridianError(f"{label} must be {qualifier} list of strings")
    result = tuple(_required_string(item, f"{label} item") for item in value)
    if len(set(result)) != len(result):
        raise MeridianError(f"{label} must not contain duplicates")
    return result


def _repository_relative_path(value: object, label: str) -> str:
    text = _required_string(value, label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or text != path.as_posix() or text in {".", ""}:
        raise MeridianError(f"{label} must be a normalized repository-relative path")
    return text


def check_protocol_compatibility(manifest: dict[str, object]) -> int:
    protocol_version = manifest.get("protocolVersion", LEGACY_PROTOCOL_VERSION)
    if type(protocol_version) is not int:
        raise MeridianError("manifest protocolVersion must be an integer")
    if protocol_version < 1:
        raise MeridianError("manifest protocolVersion must be a positive integer")
    if protocol_version > PROTOCOL_VERSION:
        raise MeridianError(
            f"manifest protocolVersion {protocol_version} is newer than this Meridian CLI "
            f"supports ({PROTOCOL_VERSION}); update your Meridian checkout"
        )
    return protocol_version


def manifest_workflow_mode(manifest: dict[str, object]) -> str:
    """Return the canonical workflow mode without mutating a legacy manifest."""
    protocol_version = check_protocol_compatibility(manifest)
    legacy_mode = manifest.get("mode")
    workflow_mode = manifest.get("workflowMode")
    if legacy_mode is not None and workflow_mode is not None and legacy_mode != workflow_mode:
        raise MeridianError("manifest mode and workflowMode conflict")
    selected = workflow_mode if workflow_mode is not None else legacy_mode
    if selected is None:
        raise MeridianError("manifest must declare workflowMode (or legacy mode)")
    if not isinstance(selected, str) or selected not in WORKFLOW_MODES:
        raise MeridianError(
            "manifest workflowMode must be one of: " + ", ".join(WORKFLOW_MODES)
        )
    if protocol_version >= 2 and workflow_mode is None:
        raise MeridianError("manifest protocolVersion 2 requires workflowMode")
    return selected


def _parse_catalog_surface(value: object, label: str) -> CatalogSurface:
    data = _required_object(value, label)
    forms = _required_string_list(data.get("forms"), f"{label}.forms", non_empty=True)
    unsupported = sorted(set(forms) - set(INSTALLATION_FORMS))
    if unsupported:
        raise MeridianError(f"{label}.forms contains unsupported form: {unsupported[0]}")
    return CatalogSurface(
        path=_repository_relative_path(data.get("path"), f"{label}.path"),
        forms=forms,
    )


def parse_capability_catalog(value: object) -> CapabilityCatalog:
    data = _required_object(value, "capability catalog")
    catalog_version = _required_positive_integer(data.get("catalogVersion"), "catalogVersion")
    if catalog_version != CAPABILITY_CATALOG_VERSION:
        raise MeridianError(
            f"capability catalog version {catalog_version} is unsupported; "
            f"expected {CAPABILITY_CATALOG_VERSION}"
        )
    raw_capabilities = _required_object(data.get("capabilities"), "capabilities")
    raw_profiles = _required_object(data.get("profiles"), "profiles")
    capabilities: list[CatalogCapability] = []
    for capability_id, raw_capability in sorted(raw_capabilities.items()):
        if not SAFE_PATH_COMPONENT.fullmatch(capability_id):
            raise MeridianError(f"invalid capability ID: {capability_id!r}")
        label = f"capabilities.{capability_id}"
        item = _required_object(raw_capability, label)
        workflow_modes = _required_string_list(
            item.get("workflowModes"), f"{label}.workflowModes", non_empty=True
        )
        unsupported_modes = sorted(set(workflow_modes) - set(WORKFLOW_MODES))
        if unsupported_modes:
            raise MeridianError(
                f"{label}.workflowModes contains unsupported mode: {unsupported_modes[0]}"
            )
        eligible = item.get("selfHostingEligible")
        if type(eligible) is not bool:
            raise MeridianError(f"{label}.selfHostingEligible must be a boolean")
        forms = _required_string_list(
            item.get("installationForms"), f"{label}.installationForms", non_empty=True
        )
        unsupported_forms = sorted(set(forms) - set(INSTALLATION_FORMS))
        if unsupported_forms:
            raise MeridianError(
                f"{label}.installationForms contains unsupported form: {unsupported_forms[0]}"
            )
        surfaces_value = item.get("managedSurfaces")
        if not isinstance(surfaces_value, list) or not surfaces_value:
            raise MeridianError(f"{label}.managedSurfaces must be a non-empty list")
        surfaces = tuple(
            _parse_catalog_surface(surface, f"{label}.managedSurfaces[{index}]")
            for index, surface in enumerate(surfaces_value)
        )
        surface_paths = [surface.path for surface in surfaces]
        if len(set(surface_paths)) != len(surface_paths):
            raise MeridianError(f"{label}.managedSurfaces contains duplicate paths")
        for surface in surfaces:
            if not set(surface.forms) <= set(forms):
                raise MeridianError(
                    f"{label} surface {surface.path} uses a form absent from installationForms"
                )
        host_profiles = _required_object(item.get("hostProfiles"), f"{label}.hostProfiles")
        parsed_hosts = tuple(
            (
                host_id,
                _required_string(
                    _required_object(host, f"{label}.hostProfiles.{host_id}").get("evidenceKind"),
                    f"{label}.hostProfiles.{host_id}.evidenceKind",
                ),
            )
            for host_id, host in sorted(host_profiles.items())
        )
        requirements = _required_object(
            item.get("evidenceRequirements"), f"{label}.evidenceRequirements"
        )
        required_dimensions = {"installation", "hostActivation", "verification"}
        if set(requirements) != required_dimensions:
            raise MeridianError(
                f"{label}.evidenceRequirements must declare installation, hostActivation, and verification"
            )
        evidence_requirements = tuple(
            (
                dimension,
                _required_string_list(
                    requirements[dimension],
                    f"{label}.evidenceRequirements.{dimension}",
                ),
            )
            for dimension in sorted(required_dimensions)
        )
        dependencies_value = item.get("dependencies")
        if not isinstance(dependencies_value, list):
            raise MeridianError(f"{label}.dependencies must be a list")
        dependencies = tuple(
            (
                _required_string(
                    _required_object(dependency, f"{label}.dependencies[{index}]").get("id"),
                    f"{label}.dependencies[{index}].id",
                ),
                _required_positive_integer(
                    _required_object(dependency, f"{label}.dependencies[{index}]").get("version"),
                    f"{label}.dependencies[{index}].version",
                ),
            )
            for index, dependency in enumerate(dependencies_value)
        )
        capabilities.append(
            CatalogCapability(
                capability_id=capability_id,
                version=_required_positive_integer(item.get("version"), f"{label}.version"),
                workflow_modes=workflow_modes,
                self_hosting_eligible=eligible,
                host_profiles=parsed_hosts,
                installation_forms=forms,
                managed_surfaces=surfaces,
                evidence_requirements=evidence_requirements,
                dependencies=dependencies,
            )
        )
    catalog = CapabilityCatalog(catalog_version, tuple(capabilities), ())
    for capability in catalog.capabilities:
        for dependency_id, dependency_version in capability.dependencies:
            dependency = catalog.capability(dependency_id)
            if dependency is None or dependency.version != dependency_version:
                raise MeridianError(
                    f"capability {capability.capability_id} has an unresolved dependency "
                    f"{dependency_id} v{dependency_version}"
                )
    profiles: list[CatalogProfile] = []
    for profile_id, raw_profile in sorted(raw_profiles.items()):
        if not SAFE_PATH_COMPONENT.fullmatch(profile_id):
            raise MeridianError(f"invalid profile ID: {profile_id!r}")
        label = f"profiles.{profile_id}"
        profile = _required_object(raw_profile, label)
        raw_required = _required_object(profile.get("capabilities"), f"{label}.capabilities")
        required = tuple(
            (capability_id, _required_positive_integer(version, f"{label}.capabilities.{capability_id}"))
            for capability_id, version in sorted(raw_required.items())
        )
        for capability_id, version in required:
            capability = catalog.capability(capability_id)
            if capability is None or capability.version != version:
                raise MeridianError(
                    f"{label} requires unknown capability version {capability_id} v{version}"
                )
            for dependency_id, dependency_version in capability.dependencies:
                if dict(required).get(dependency_id) != dependency_version:
                    raise MeridianError(
                        f"{label} omits dependency {dependency_id} v{dependency_version} "
                        f"required by {capability_id}"
                    )
        profiles.append(
            CatalogProfile(
                profile_id=profile_id,
                version=_required_positive_integer(profile.get("version"), f"{label}.version"),
                capabilities=required,
                verification_probe=_repository_relative_path(
                    profile.get("verificationProbe"), f"{label}.verificationProbe"
                ),
                host_probes=tuple(
                    (
                        host_id,
                        _repository_relative_path(path, f"{label}.hostProbes.{host_id}"),
                    )
                    for host_id, path in sorted(
                        _required_object(profile.get("hostProbes"), f"{label}.hostProbes").items()
                    )
                ),
            )
        )
        declared_hosts = {
            host_id
            for capability_id, _version in required
            for host_id, _kind in catalog.capability(capability_id).host_profiles
        }
        if set(dict(profiles[-1].host_probes)) != declared_hosts:
            raise MeridianError(
                f"{label}.hostProbes must declare exactly: {', '.join(sorted(declared_hosts))}"
            )
    return CapabilityCatalog(catalog_version, catalog.capabilities, tuple(profiles))


def load_capability_catalog(framework_root: Path) -> CapabilityCatalog:
    path = framework_root / CAPABILITY_CATALOG_PATH
    if not path.is_file():
        raise MeridianError(f"capability catalog is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"invalid capability catalog: {path}") from error
    return parse_capability_catalog(value)


def _parse_evidence_snapshot(
    value: object,
    label: str,
    allowed_states: tuple[str, ...],
    positive_states: tuple[str, ...],
    allowed_not_applicable_rationales: tuple[str, ...],
    *,
    verification: bool = False,
) -> EvidenceSnapshot:
    data = _required_object(value, label)
    state = _required_string(data.get("state"), f"{label}.state")
    if state not in allowed_states:
        raise MeridianError(f"{label}.state is unsupported: {state}")
    evidence = _required_string_list(data.get("evidence"), f"{label}.evidence")
    rationale_value = data.get("notApplicableRationale")
    if rationale_value is not None and not isinstance(rationale_value, str):
        raise MeridianError(f"{label}.notApplicableRationale must be null or a string")
    rationale = rationale_value.strip() if isinstance(rationale_value, str) else None
    if state in positive_states and not evidence:
        raise MeridianError(f"{label} state {state} requires evidence")
    if state == "NOT_APPLICABLE":
        if not rationale or rationale not in allowed_not_applicable_rationales:
            expected = ", ".join(allowed_not_applicable_rationales) or "no catalog exclusion applies"
            raise MeridianError(
                f"{label} NOT_APPLICABLE requires a catalog-backed rationale ({expected})"
            )
    elif rationale:
        raise MeridianError(f"{label}.notApplicableRationale is only valid for NOT_APPLICABLE")
    verified_at = data.get("verifiedAt") if verification else None
    verifier_version = data.get("verifierVersion") if verification else None
    if verification:
        for field, field_value in (("verifiedAt", verified_at), ("verifierVersion", verifier_version)):
            if field_value is not None and (not isinstance(field_value, str) or not field_value.strip()):
                raise MeridianError(f"{label}.{field} must be null or a non-empty string")
    return EvidenceSnapshot(
        state=state,
        evidence=evidence,
        not_applicable_rationale=rationale,
        verified_at=verified_at if isinstance(verified_at, str) else None,
        verifier_version=verifier_version if isinstance(verifier_version, str) else None,
    )


def parse_capability_profiles(
    manifest: dict[str, object], catalog: CapabilityCatalog
) -> tuple[CapabilityProfileDeclaration, ...]:
    raw_profiles = manifest.get("capabilityProfiles", {})
    profiles = _required_object(raw_profiles, "manifest capabilityProfiles")
    workflow_mode = manifest_workflow_mode(manifest)
    parsed_profiles: list[CapabilityProfileDeclaration] = []
    for profile_id, raw_profile in sorted(profiles.items()):
        label = f"capabilityProfiles.{profile_id}"
        catalog_profile = catalog.profile(profile_id)
        if catalog_profile is None:
            raise MeridianError(f"{label} is absent from capability catalog v{catalog.catalog_version}")
        profile = _required_object(raw_profile, label)
        profile_version = _required_positive_integer(
            profile.get("profileVersion"), f"{label}.profileVersion"
        )
        if profile_version != catalog_profile.version:
            raise MeridianError(
                f"{label}.profileVersion must be {catalog_profile.version}, got {profile_version}"
            )
        raw_capabilities = _required_object(profile.get("capabilities"), f"{label}.capabilities")
        required = dict(catalog_profile.capabilities)
        if set(raw_capabilities) != set(required):
            missing = sorted(set(required) - set(raw_capabilities))
            extra = sorted(set(raw_capabilities) - set(required))
            detail = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if extra:
                detail.append("unexpected " + ", ".join(extra))
            raise MeridianError(f"{label}.capabilities is incomplete: {'; '.join(detail)}")
        declarations: list[CapabilityDeclaration] = []
        for capability_id, raw_declaration in sorted(raw_capabilities.items()):
            capability_label = f"{label}.capabilities.{capability_id}"
            capability = catalog.capability(capability_id)
            if capability is None:
                raise MeridianError(f"{capability_label} is absent from the capability catalog")
            declaration = _required_object(raw_declaration, capability_label)
            required_version = _required_positive_integer(
                declaration.get("requiredVersion"), f"{capability_label}.requiredVersion"
            )
            if required_version != required[capability_id] or required_version != capability.version:
                raise MeridianError(
                    f"{capability_label}.requiredVersion must be {required[capability_id]}"
                )
            raw_surfaces = declaration.get("managedSurface")
            if not isinstance(raw_surfaces, list) or not raw_surfaces:
                raise MeridianError(f"{capability_label}.managedSurface must be a non-empty list")
            surfaces = tuple(
                DeclaredSurface(
                    path=_repository_relative_path(
                        _required_object(surface, f"{capability_label}.managedSurface[{index}]").get("path"),
                        f"{capability_label}.managedSurface[{index}].path",
                    ),
                    form=_required_string(
                        _required_object(surface, f"{capability_label}.managedSurface[{index}]").get("form"),
                        f"{capability_label}.managedSurface[{index}].form",
                    ),
                )
                for index, surface in enumerate(raw_surfaces)
            )
            if len({surface.path for surface in surfaces}) != len(surfaces):
                raise MeridianError(f"{capability_label}.managedSurface contains duplicate paths")
            catalog_surfaces = {surface.path: surface for surface in capability.managed_surfaces}
            if {surface.path for surface in surfaces} != set(catalog_surfaces):
                raise MeridianError(
                    f"{capability_label}.managedSurface must completely match the catalog surface"
                )
            for surface in surfaces:
                if surface.form not in catalog_surfaces[surface.path].forms:
                    raise MeridianError(
                        f"{capability_label}.managedSurface form {surface.form} is not allowed for {surface.path}"
                    )
            exclusions: list[str] = []
            if workflow_mode not in capability.workflow_modes:
                exclusions.append("workflow-mode-excluded")
            if profile_id == "meridian-self-hosting" and not capability.self_hosting_eligible:
                exclusions.append("self-hosting-ineligible")
            installation = _parse_evidence_snapshot(
                declaration.get("installation"),
                f"{capability_label}.installation",
                INSTALLATION_STATES,
                ("INSTALLED",),
                tuple(exclusions),
            )
            raw_hosts = _required_object(
                declaration.get("hostActivation"), f"{capability_label}.hostActivation"
            )
            host_activation: list[tuple[str, EvidenceSnapshot]] = []
            supported_hosts = dict(capability.host_profiles)
            missing_hosts = sorted(set(supported_hosts) - set(raw_hosts))
            if missing_hosts:
                raise MeridianError(
                    f"{capability_label}.hostActivation is missing supported host profile: "
                    f"{missing_hosts[0]}"
                )
            for host_id, raw_snapshot in sorted(raw_hosts.items()):
                host_exclusions = list(exclusions)
                if host_id not in supported_hosts:
                    host_exclusions.append("host-profile-unsupported")
                host_activation.append(
                    (
                        host_id,
                        _parse_evidence_snapshot(
                            raw_snapshot,
                            f"{capability_label}.hostActivation.{host_id}",
                            HOST_ACTIVATION_STATES,
                            ("ENFORCED", "ADVISORY"),
                            tuple(host_exclusions),
                        ),
                    )
                )
            verification_snapshot = _parse_evidence_snapshot(
                declaration.get("verification"),
                f"{capability_label}.verification",
                VERIFICATION_STATES,
                ("PASS", "ADVISORY"),
                tuple(exclusions),
                verification=True,
            )
            declarations.append(
                CapabilityDeclaration(
                    capability_id=capability_id,
                    required_version=required_version,
                    managed_surface=surfaces,
                    installation=installation,
                    host_activation=tuple(host_activation),
                    verification=verification_snapshot,
                )
            )
        parsed_profiles.append(
            CapabilityProfileDeclaration(profile_id, profile_version, tuple(declarations))
        )
    return tuple(parsed_profiles)


def validate_manifest(
    manifest: dict[str, object], catalog: CapabilityCatalog | None = None
) -> tuple[CapabilityProfileDeclaration, ...]:
    manifest_workflow_mode(manifest)
    applied_migrations = manifest.get("appliedMigrations", [])
    _required_string_list(applied_migrations, "manifest appliedMigrations")
    managed_files = _required_object(manifest.get("managedFiles", {}), "manifest managedFiles")
    for path, digest in managed_files.items():
        _repository_relative_path(path, "manifest managedFiles path")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise MeridianError(f"manifest managedFiles.{path} must be a SHA-256 digest")
    if "capabilityProfiles" not in manifest:
        return ()
    if catalog is None:
        raise MeridianError("manifest capabilityProfiles require a capability catalog")
    return parse_capability_profiles(manifest, catalog)


def load_manifest(project_root: Path, framework_root: Path | None = None) -> dict[str, object]:
    manifest_path = project_root / MANIFEST_PATH
    if not manifest_path.is_file():
        raise MeridianError(
            "project is not locked; run `meridian lock --project <path> --mode <mode>` first"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"invalid manifest: {manifest_path}") from error
    if not isinstance(manifest, dict):
        raise MeridianError(f"invalid manifest: {manifest_path} must contain a JSON object")
    catalog = load_capability_catalog(framework_root) if framework_root is not None else None
    validate_manifest(manifest, catalog)
    return manifest


def canonical_manifest(manifest: dict[str, object]) -> dict[str, object]:
    """Return the current-protocol representation without changing effective state."""
    result = dict(manifest)
    result["protocolVersion"] = PROTOCOL_VERSION
    result["workflowMode"] = manifest_workflow_mode(manifest)
    result.pop("mode", None)
    return result


def write_manifest(
    project_root: Path,
    manifest: dict[str, object],
    framework_root: Path | None = None,
) -> None:
    manifest = canonical_manifest(manifest)
    catalog = load_capability_catalog(framework_root) if framework_root is not None else None
    validate_manifest(manifest, catalog)
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


def first_retirement_migration(framework_root: Path, migration_ids_to_check: list[str]) -> str | None:
    """The first migration, in order, among `migration_ids_to_check` whose
    record declares any `stage: "retirement"` capability move, or `None` if
    none of them do."""
    for path in migration_record_paths(framework_root, migration_ids_to_check):
        data = json.loads(path.read_text(encoding="utf-8"))
        if any(str(move.get("stage")) == "retirement" for move in data.get("capabilityMoves", [])):
            return str(data["id"])
    return None


def capped_target_version(framework_root: Path, installed_version: str, target_version: str) -> str:
    """The effective target version for a `--stop-before-retirement` upgrade:
    the `from` version of the first pending migration that declares a
    retirement-stage capability move, or `target_version` unchanged if none
    of the pending migrations retire anything."""
    pending = migration_ids(framework_root, installed_version, target_version)
    retirement_id = first_retirement_migration(framework_root, pending)
    if retirement_id is None:
        return target_version
    for path in migration_record_paths(framework_root, [retirement_id]):
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data["from"])
    raise MeridianError(f"migration record is missing: {retirement_id}")


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


def migration_capability_moves(data: dict[str, object]) -> list[CapabilityMove]:
    """Parse the exact-source/exact-target moves declared by one migration."""
    result = []
    for entry in data.get("capabilityMoves", []):
        source = entry["source"]
        target = entry["target"]
        result.append(
            CapabilityMove(
                stage=str(entry["stage"]),
                source_path=Path(str(source["path"])),
                source_capability=str(source["capability"]),
                source_version=int(source["capabilityVersion"]),
                source_sha256=str(source["markerSha256"]),
                target_path=Path(str(target["path"])),
                target_capability=str(target["capability"]),
                target_version=int(target["capabilityVersion"]),
                target_sha256=str(target["markerSha256"]),
                migration=str(data["id"]),
            )
        )
    return result


def marker_blocks(text: str, capability: str, version: int) -> list[str]:
    """Every complete exact marker block for one capability/version pair."""
    pattern = re.compile(
        rf"<!-- MERIDIAN:BEGIN capability={re.escape(capability)} v{version} -->\n?.*?"
        r"<!-- MERIDIAN:END -->",
        re.DOTALL,
    )
    return [match.group(0) for match in pattern.finditer(text)]


def marker_block_sha256(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def exact_marker_matches(text: str, capability: str, version: int, expected_sha256: str) -> bool:
    blocks = marker_blocks(text, capability, version)
    return len(blocks) == 1 and marker_block_sha256(blocks[0]) == expected_sha256


def declared_capability_moves(
    framework_root: Path, migration_ids_to_find: list[str] | None = None
) -> list[CapabilityMove]:
    """All, or only pending, declared capability moves in migration order."""
    wanted = set(migration_ids_to_find) if migration_ids_to_find is not None else None
    result = []
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if wanted is None or str(data["id"]) in wanted:
            result.extend(migration_capability_moves(data))
    return result


def pending_migration_establishes_move_source(
    framework_root: Path, pending_migrations: list[str], move: CapabilityMove
) -> bool:
    """Whether an earlier pending migration declares this move's source marker.

    A long-lag consumer can legitimately predate a marker that an intermediate
    migration adds and a later migration immediately relocates.  The final
    template no longer contains that transient source marker, so its presence
    cannot be inferred from the three-way merge inputs alone.  Trust this
    narrow transition only when the migration ledger explicitly establishes
    the exact capability/version on the same managed source path before the
    move that consumes it.
    """
    try:
        move_index = pending_migrations.index(move.migration)
    except ValueError:
        return False
    for path in migration_record_paths(framework_root, pending_migrations[:move_index]):
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(move.source_path) not in {str(item) for item in data.get("managedPaths", [])}:
            continue
        if (move.source_capability, move.source_version) in migration_capability_entries(data):
            return True
    return False


def validate_capability_moves(framework_root: Path, mode: str) -> list[str]:
    """Validate move declarations against the exact current release templates."""
    managed = {item.target: item.source for item in managed_files(framework_root, mode)}
    requirements = capability_requirements(framework_root)
    errors = []
    seen_sources: set[tuple[Path, str, int]] = set()
    for path in sorted((framework_root / "migrations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        moves = data.get("capabilityMoves", [])
        if not moves:
            continue
        if not isinstance(moves, list):
            errors.append(f"{path.name}: capabilityMoves must be an array")
            continue
        for index, raw in enumerate(moves):
            label = f"{path.name}: capabilityMoves[{index}]"
            if not isinstance(raw, dict) or set(raw) != {"stage", "source", "target"}:
                errors.append(f"{label} must contain exactly stage, source, and target")
                continue
            if raw["stage"] not in ("additive", "retirement"):
                errors.append(f"{label} has an unsupported stage")
                continue
            locations = []
            for side in ("source", "target"):
                value = raw[side]
                required = {"path", "capability", "capabilityVersion", "markerSha256"}
                if not isinstance(value, dict) or set(value) != required:
                    errors.append(f"{label}.{side} has an invalid shape")
                    break
                try:
                    location = (
                        Path(str(value["path"])),
                        str(value["capability"]),
                        int(value["capabilityVersion"]),
                        str(value["markerSha256"]),
                    )
                except (TypeError, ValueError):
                    errors.append(f"{label}.{side} has invalid scalar values")
                    break
                if not re.fullmatch(r"[0-9a-f]{64}", location[3]):
                    errors.append(f"{label}.{side}.markerSha256 is not a SHA-256 digest")
                    break
                if location[0] not in managed:
                    errors.append(f"{label}.{side}.path is not a managed path")
                    break
                template_text = managed[location[0]].read_text(encoding="utf-8")
                superseding_version = max(
                    (
                        int(version)
                        for capability, version in CAPABILITY_MARKER.findall(template_text)
                        if capability == location[1] and int(version) > location[2]
                    ),
                    default=None,
                )
                superseded_target = (
                    side == "target"
                    and superseding_version is not None
                    and requirements.get(location[1], (0, ""))[0] == superseding_version
                    and len(marker_blocks(template_text, location[1], superseding_version)) == 1
                )
                if not (side == "source" and not marker_blocks(template_text, location[1], location[2])) and not (raw["stage"] == "retirement" and side == "source") and not exact_marker_matches(template_text, location[1], location[2], location[3]) and not superseded_target:
                    errors.append(f"{label}.{side} does not name one exact marker in the release template")
                    break
                locations.append(location)
            if len(locations) != 2:
                continue
            source, target = locations
            if source[:3] == target[:3]:
                errors.append(f"{label} has an identical source and target location")
            if source[:3] in seen_sources and raw["stage"] != "retirement":
                errors.append(f"{label} duplicates a declared source marker")
            seen_sources.add(source[:3])
            if source[0] not in {Path(item) for item in data.get("managedPaths", [])} or target[0] not in {
                Path(item) for item in data.get("managedPaths", [])
            }:
                errors.append(f"{label} source and target must both be listed in managedPaths")
    return errors


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
    result = [
        (capability, version, superseded_by)
        for capability, version, superseded_by, managed_paths in pending_capability_removals(
            framework_root, migration_ids_to_find
        )
        if str(target) in managed_paths
    ]
    for move in declared_capability_moves(framework_root, migration_ids_to_find):
        if move.stage == "retirement" and move.source_path == target:
            result.append((move.source_capability, move.source_version, None))
    return result


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


CLAUDE_AGENTS_POINTER_MARKER = "<!-- MERIDIAN:CLAUDE-AGENTS-POINTER v1 -->"


def is_agents_pointer(text: str) -> bool:
    """Recognize a project-owned CLAUDE.md that deliberately delegates to AGENTS.

    New pointers declare a compact, versioned marker rather than depending on
    explanatory prose. The former prose signature remains a compatibility path
    for pointers created before the marker existed; neither form is safe when
    CLAUDE.md contains capability markers of its own.
    """
    legacy_pointer = (
        "`AGENTS.md`, which is authoritative" in text
        and "Every Meridian capability marker" in text
        and "lives in `AGENTS.md`, once" in text
        and "Keep this file a pointer" in text
    )
    explicit_pointer = text.count(CLAUDE_AGENTS_POINTER_MARKER) == 1
    return (explicit_pointer or legacy_pointer) and not marker_pairs(text)


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


def agents_pointer_can_follow_upgrade(
    project_root: Path,
    framework_root: Path,
    mode: str,
    baseline_root: Path,
    claude_template_text: str,
    claude_local_text: str,
) -> bool:
    """Allow a valid pointer when this same upgrade makes AGENTS current.

    The check remains marker-exact: it predicts only the narrow marker-aware
    AGENTS update, never a broad merge or replacement of project-owned text.
    """
    if not is_agents_pointer(claude_local_text):
        return False
    if agents_pointer_satisfies_claude(
        project_root, framework_root, mode, claude_template_text, claude_local_text
    ):
        return True
    agent_local = project_root / "AGENTS.md"
    agent_base = baseline_root / "AGENTS.md"
    agent_template = framework_root / "templates" / "workflows" / mode / "AGENTS.md"
    if not agent_local.is_file() or not agent_base.is_file() or not agent_template.is_file():
        return False
    reconciled = append_only_new_markers(
        agent_local.read_text(encoding="utf-8"),
        agent_base.read_text(encoding="utf-8"),
        agent_template.read_text(encoding="utf-8"),
    )
    if reconciled is None:
        return False
    return all(
        extract_marker_block(reconciled, capability, version)
        == extract_marker_block(claude_template_text, capability, version)
        for capability, version in marker_pairs(claude_template_text)
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


def deduplicate_identical_template_markers(merged_text: str, template_text: str) -> str | None:
    """Remove only duplicate copies that are byte-identical to the template.

    A line merge can independently add the same newly introduced marker on both
    sides at different locations. That is structurally invalid even though the
    textual merge has no conflict. Never choose between divergent copies here:
    only an exact duplicate of the released block is safe to collapse.
    """
    result = merged_text
    changed = False
    for capability, version in marker_pairs(template_text):
        block = extract_marked_block(template_text, capability, version)
        if block is None:
            continue
        matches = list(re.finditer(re.escape(block), result))
        if len(matches) < 2:
            continue
        for match in reversed(matches[1:]):
            start, end = match.span()
            result = result[:start] + result[end:]
        changed = True
    if not changed:
        return None
    return re.sub(r"\n{3,}", "\n\n", result).rstrip() + "\n"


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


def audit_capability_moves(project_root: Path, framework_root: Path, mode: str) -> list[tuple[str, str]]:
    """Verify that declared additive relocations retain both exact copies."""
    if mode != "governed-sdd":
        return []
    try:
        applied = {
            str(item)
            for item in load_manifest(project_root, framework_root).get("appliedMigrations", [])
        }
    except MeridianError:
        if (project_root / MANIFEST_PATH).is_file():
            raise
        return []
    results = []
    moves = [move for move in declared_capability_moves(framework_root) if move.migration in applied]
    retired_sources = {
        (move.source_path, move.source_capability, move.source_version)
        for move in moves
        if move.stage == "retirement"
    }
    for move in moves:
        if move.stage == "additive" and (move.source_path, move.source_capability, move.source_version) in retired_sources:
            continue
        source = project_root / move.source_path
        target = project_root / move.target_path
        if move.stage == "additive":
            for path, capability, version, digest, side in (
                (source, move.source_capability, move.source_version, move.source_sha256, "source"),
                (target, move.target_capability, move.target_version, move.target_sha256, "target"),
            ):
                text = path.read_text(encoding="utf-8") if path.is_file() else ""
                if side == "source" and path == project_root / "CLAUDE.md" and is_agents_pointer(text):
                    continue
                if not exact_marker_matches(text, capability, version, digest):
                    results.append(
                        (
                            "FAIL",
                            f"capability move {move.migration}: {side} {path.relative_to(project_root)} "
                            f"for capability={capability} v{version} is missing, modified, or duplicated",
                        )
                    )
        else:
            source_text = source.read_text(encoding="utf-8") if source.is_file() else ""
            target_text = target.read_text(encoding="utf-8") if target.is_file() else ""
            if marker_blocks(source_text, move.source_capability, move.source_version):
                results.append(
                    (
                        "FAIL",
                        f"capability move {move.migration}: retired source {move.source_path} is still present",
                    )
                )
            target_matches = exact_marker_matches(
                target_text, move.target_capability, move.target_version, move.target_sha256
            )
            if not target_matches:
                template = framework_root / "templates" / "workflows" / mode / move.target_path
                template_text = template.read_text(encoding="utf-8") if template.is_file() else ""
                superseding_versions = [
                    int(version)
                    for capability, version in CAPABILITY_MARKER.findall(template_text)
                    if capability == move.target_capability and int(version) > move.target_version
                ]
                if superseding_versions:
                    current_version = max(superseding_versions)
                    target_matches = (
                        extract_marker_block(target_text, move.target_capability, current_version)
                        == extract_marker_block(template_text, move.target_capability, current_version)
                        is not None
                    )
            if not target_matches:
                results.append(
                    (
                        "FAIL",
                        f"capability move {move.migration}: target {move.target_path} is missing, modified, or duplicated",
                    )
                )
    return results


def entry_router_overlay(text: str, path: Path) -> str:
    """Validate the deliberately tiny, non-instructional host overlay."""
    if not text:
        return ""
    if len(text.encode("utf-8")) > 256 or not re.fullmatch(r"<!--[^\n]*-->\n?", text):
        raise MeridianError(
            f"{path}: an entry-router host overlay must be one HTML comment of at most 256 UTF-8 bytes"
        )
    return text.rstrip() + "\n"


def render_entry_router(router_text: str, overlay_text: str = "") -> str:
    """Render one generated entry point from the consumer-owned router."""
    return router_text.rstrip() + "\n" + ("\n" + overlay_text if overlay_text else "")


def entry_router_outputs(project_root: Path) -> dict[Path, str]:
    """Return the expected generated entry points, or fail without writing."""
    router = project_root / ENTRY_ROUTER_PATH
    if not router.is_file():
        raise MeridianError(f"entry-router source is missing: {router}")
    router_text = router.read_text(encoding="utf-8")
    if len(router_text.encode("utf-8")) > ENTRY_ROUTER_BUDGET_BYTES:
        raise MeridianError(
            f"{router}: exceeds the {ENTRY_ROUTER_BUDGET_BYTES}-byte entry-router budget"
        )
    if CLAUDE_AGENTS_POINTER_MARKER in router_text or is_agents_pointer(router_text):
        raise MeridianError(f"{router}: a generated entry router must not emit a Claude-to-AGENTS pointer")
    result = {}
    for target, relative_overlay in ENTRY_ROUTER_OVERLAYS.items():
        overlay = project_root / relative_overlay
        overlay_text = entry_router_overlay(overlay.read_text(encoding="utf-8"), overlay) if overlay.is_file() else ""
        output = render_entry_router(router_text, overlay_text)
        if len(output.encode("utf-8")) > ENTRY_ROUTER_BUDGET_BYTES:
            raise MeridianError(f"{target}: exceeds the {ENTRY_ROUTER_BUDGET_BYTES}-byte entry-router budget")
        result[Path(target)] = output
    return result


def project_uses_entry_router(project_root: Path) -> bool:
    """Whether the project's top-level agent files are generated outputs."""
    return (project_root / ENTRY_ROUTER_PATH).is_file()


def entry_router_trigger_requirements(
    project_root: Path,
    framework_root: Path,
    pending_migrations: list[str],
    planned_files: list[ManagedFile],
) -> tuple[str, ...]:
    """Report command triggers a pending migration requires in the router.

    The framework template remains the authority for the exact command text
    and routed document, while ENTRY_ROUTER.md remains the only editable input
    in an opted-in consumer. Only literal command triggers are checked here;
    prose routes such as status and audit continue to be governed by the
    explicit entry-router route map.
    """
    if not project_uses_entry_router(project_root):
        return ()
    command_trigger_versions = []
    for path in migration_record_paths(framework_root, pending_migrations):
        data = json.loads(path.read_text(encoding="utf-8"))
        command_trigger_versions.extend(
            version
            for capability, version in migration_capability_entries(data)
            if capability == "command-triggers"
        )
    if not command_trigger_versions:
        return ()

    version = max(command_trigger_versions)
    templates = {
        item.target: item.source
        for item in planned_files
        if item.target in {Path("AGENTS.md"), Path("CLAUDE.md")}
    }
    source = templates.get(Path("AGENTS.md")) or templates.get(Path("CLAUDE.md"))
    if source is None:
        raise MeridianError("upgrade plan has no managed entry-point template for command-triggers")
    block = extract_marker_block(source.read_text(encoding="utf-8"), "command-triggers", version)
    if block is None:
        raise MeridianError(
            f"entry-point template lacks capability=command-triggers v{version} required by the migration ledger"
        )

    router_text = (project_root / ENTRY_ROUTER_PATH).read_text(encoding="utf-8")
    router_lines = router_text.splitlines()
    problems = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or "—" not in stripped:
            continue
        label, route = stripped[2:].split("—", 1)
        triggers = re.findall(r"`([^`]+)`", label)
        if not triggers:
            continue
        targets = [value for value in re.findall(r"`([^`]+)`", route) if value.endswith(".md")]
        if not targets:
            raise MeridianError(f"command trigger has no routed Markdown target: {stripped}")
        target = targets[-1]
        for trigger in triggers:
            if any(trigger in router_line and target in router_line for router_line in router_lines):
                continue
            if router_text.count(target) == 1:
                guidance = (
                    f"add `{trigger}` to the existing route line for `{target}`; do not add another "
                    "line because the entry-router audit requires each route target exactly once"
                )
            else:
                guidance = f"add `{trigger}` and route it to `{target}`"
            problems.append(
                f"{ENTRY_ROUTER_PATH}: missing trigger `{trigger}` for `{target}`; {guidance}"
            )
    return tuple(problems)


def audit_entry_router(project_root: Path) -> list[tuple[str, str]]:
    """Audit an opting-in consumer's generated files and explicit route map."""
    if not (project_root / ENTRY_ROUTER_PATH).is_file():
        return []
    results = []
    try:
        outputs = entry_router_outputs(project_root)
    except MeridianError as error:
        return [("FAIL", str(error))]
    for target, expected in outputs.items():
        actual = project_root / target
        if not actual.is_file() or actual.read_text(encoding="utf-8") != expected:
            results.append(("FAIL", f"generated entry router drift: {target}; rerun `meridian generate-entry-routers --write`"))
    mapping_path = project_root / ENTRY_ROUTER_MAP_PATH
    try:
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return results + [("FAIL", f"entry-router route map is missing or invalid: {mapping_path} ({error})")]
    if not isinstance(mapping, dict) or set(mapping) != set(ENTRY_ROUTER_ROUTES):
        results.append(("FAIL", f"entry-router route map must declare exactly: {', '.join(ENTRY_ROUTER_ROUTES)}"))
        return results
    router_text = (project_root / ENTRY_ROUTER_PATH).read_text(encoding="utf-8")
    for route, expected_path in ENTRY_ROUTER_ROUTES.items():
        actual_path = mapping.get(route)
        if actual_path != expected_path:
            results.append(("FAIL", f"entry-router route {route} must target {expected_path}"))
            continue
        if router_text.count(expected_path) != 1:
            results.append(("FAIL", f"entry-router must name {expected_path} exactly once for route {route}"))
        target = project_root / expected_path
        if not target.is_file():
            results.append(("FAIL", f"entry-router route {route} target is missing: {expected_path}"))
            continue
        target_text = target.read_text(encoding="utf-8").lower()
        missing = [token for token in ENTRY_ROUTER_SAFEGUARDS[route] if token not in target_text]
        if missing:
            results.append(
                ("FAIL", f"entry-router route {route} target lacks required safeguard token(s): {', '.join(missing)}")
            )
    return results


def _audit_evidence_reference(
    project_root: Path, reference: str, surface_digests: set[str]
) -> str | None:
    """Return a diagnostic when a persisted evidence reference is not current."""
    if reference.startswith("sha256:"):
        digest = reference.removeprefix("sha256:")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            return f"invalid digest evidence {reference!r}"
        if digest not in surface_digests:
            return f"stale digest evidence {reference}"
        return None
    if reference.startswith("path:"):
        raw_path = reference.removeprefix("path:")
        try:
            relative_path = _repository_relative_path(raw_path, "audit evidence path")
        except MeridianError as error:
            return str(error)
        if not (project_root / relative_path).is_file():
            return f"missing evidence artifact {relative_path}"
        return None
    return f"unresolvable evidence reference {reference!r}; expected path:<path> or sha256:<digest>"


def _audit_snapshot_evidence(
    project_root: Path, snapshot: EvidenceSnapshot, surface_digests: set[str]
) -> list[str]:
    return [
        diagnostic
        for reference in snapshot.evidence
        if (diagnostic := _audit_evidence_reference(project_root, reference, surface_digests))
        is not None
    ]


def _audit_probe_evidence(project_root: Path, snapshot: EvidenceSnapshot) -> list[str]:
    """Require runtime/behavior claims to name concrete probe artifacts."""
    diagnostics: list[str] = []
    for reference in snapshot.evidence:
        if not reference.startswith("probe:"):
            diagnostics.append(
                f"invalid positive evidence {reference!r}; expected probe:<path>"
            )
            continue
        raw_path = reference.removeprefix("probe:")
        try:
            relative_path = _repository_relative_path(raw_path, "audit probe path")
        except MeridianError as error:
            diagnostics.append(str(error))
            continue
        if not (project_root / relative_path).is_file():
            diagnostics.append(f"missing probe artifact {relative_path}")
    return diagnostics


def audit_declared_capabilities(
    project_root: Path, framework_root: Path, requested_mode: str
) -> tuple[list[AuditResult], str]:
    """Audit effective declarations without projecting migration provenance."""
    try:
        manifest = load_manifest(project_root, framework_root)
    except MeridianError as error:
        # Preserve the CLI's protocol-compatibility diagnostic: callers must
        # update the framework before this version can interpret the manifest.
        if "newer than this Meridian CLI supports" in str(error):
            raise
        return [AuditResult("FAIL", "declaration/manifest", str(error))], requested_mode

    workflow_mode = manifest_workflow_mode(manifest)
    if requested_mode != workflow_mode:
        return [
            AuditResult(
                "FAIL",
                "declaration/workflow-mode",
                f"requested {requested_mode}, but the locked manifest declares {workflow_mode}",
            )
        ], workflow_mode

    protocol_version = check_protocol_compatibility(manifest)
    if "capabilityProfiles" not in manifest or not manifest.get("capabilityProfiles"):
        status = (
            "FAIL"
            if protocol_version >= CAPABILITY_DECLARATION_REQUIRED_PROTOCOL
            else "UNVERIFIED"
        )
        rationale = (
            f"protocol v{protocol_version} requires explicit capabilityProfiles"
            if status == "FAIL"
            else f"legacy protocol v{protocol_version} manifest has no capabilityProfiles; "
            "migration history is provenance only"
        )
        return [AuditResult(status, "declaration/legacy-compatibility", rationale)], workflow_mode

    catalog = load_capability_catalog(framework_root)
    try:
        profiles = parse_capability_profiles(manifest, catalog)
    except MeridianError as error:
        return [AuditResult("FAIL", "declaration/capabilityProfiles", str(error))], workflow_mode

    managed_files = manifest.get("managedFiles", {})
    assert isinstance(managed_files, dict)
    framework_version = read_version(framework_root)
    results: list[AuditResult] = []
    for profile in profiles:
        for declaration in profile.capabilities:
            capability = catalog.capability(declaration.capability_id)
            assert capability is not None
            prefix = f"{profile.profile_id}/{declaration.capability_id}"
            exclusions: list[str] = []
            if workflow_mode not in capability.workflow_modes:
                exclusions.append("workflow-mode-excluded")
            if profile.profile_id == "meridian-self-hosting" and not capability.self_hosting_eligible:
                exclusions.append("self-hosting-ineligible")
            if exclusions:
                rationale = ", ".join(exclusions)
                results.append(
                    AuditResult(
                        "NOT_APPLICABLE",
                        f"{prefix}/installation",
                        f"catalog exclusion: {rationale}",
                    )
                )
                for host_id, _snapshot in declaration.host_activation:
                    host_rationale = (
                        "host-profile-unsupported"
                        if host_id not in dict(capability.host_profiles)
                        else rationale
                    )
                    results.append(
                        AuditResult(
                            "NOT_APPLICABLE",
                            f"{prefix}/host/{host_id}",
                            f"catalog exclusion: {host_rationale}",
                        )
                    )
                results.append(
                    AuditResult(
                        "NOT_APPLICABLE",
                        f"{prefix}/verification",
                        f"catalog exclusion: {rationale}",
                    )
                )
                continue

            surface_failures: list[str] = []
            surface_digests: set[str] = set()
            surface_identities: list[str] = []
            for surface in declaration.managed_surface:
                surface_identities.append(f"{surface.form}:{surface.path}")
                path = project_root / surface.path
                if surface.form == "declaration-only":
                    continue
                if not path.is_file():
                    surface_failures.append(f"missing {surface.form} surface {surface.path}")
                    continue
                digest = sha256(path)
                surface_digests.add(digest)
                if f"sha256:{digest}" not in declaration.installation.evidence:
                    surface_failures.append(
                        f"{surface.form} surface {surface.path} lacks matching digest evidence"
                    )
                if surface.form == "managed-copy":
                    expected_digest = managed_files.get(surface.path)
                    if expected_digest is None:
                        surface_failures.append(
                            f"managed-copy surface {surface.path} has no managedFiles digest"
                        )
                    elif expected_digest != digest:
                        surface_failures.append(
                            f"drifted managed-copy surface {surface.path}: expected {expected_digest}, got {digest}"
                        )

            installation_evidence_failures = _audit_snapshot_evidence(
                project_root, declaration.installation, surface_digests
            )
            if declaration.installation.state != "INSTALLED":
                surface_failures.append(
                    f"declared installation state is {declaration.installation.state}"
                )
            surface_failures.extend(installation_evidence_failures)
            installation_status = "FAIL" if surface_failures else "PASS"
            results.append(
                AuditResult(
                    installation_status,
                    f"{prefix}/installation",
                    "verified surfaces: "
                    + ", ".join(surface_identities)
                    + "; "
                    + "; ".join(surface_failures)
                    if surface_failures
                    else "verified surfaces: " + ", ".join(surface_identities),
                )
            )

            supported_hosts = dict(capability.host_profiles)
            for host_id, snapshot in declaration.host_activation:
                identity = f"{prefix}/host/{host_id}"
                if host_id not in supported_hosts:
                    results.append(
                        AuditResult(
                            "NOT_APPLICABLE",
                            identity,
                            "catalog exclusion: host-profile-unsupported",
                        )
                    )
                    continue
                evidence_failures = _audit_probe_evidence(project_root, snapshot)
                if snapshot.state == "NOT_APPLICABLE":
                    results.append(
                        AuditResult(
                            "FAIL",
                            identity,
                            "host is catalog-supported, so NOT_APPLICABLE is contradictory",
                        )
                    )
                elif snapshot.state in {"ENFORCED", "ADVISORY"}:
                    failures = list(evidence_failures)
                    if installation_status != "PASS":
                        failures.append("positive activation claim depends on failed installation")
                    results.append(
                        AuditResult(
                            "FAIL" if failures else ("PASS" if snapshot.state == "ENFORCED" else "ADVISORY"),
                            identity,
                            "; ".join(failures)
                            if failures
                            else f"{snapshot.state.lower()} with {supported_hosts[host_id]} evidence",
                        )
                    )
                elif snapshot.state == "UNSUPPORTED":
                    results.append(
                        AuditResult(
                            "ADVISORY",
                            identity,
                            "declared UNSUPPORTED for a catalog-supported host",
                        )
                    )
                else:
                    results.append(
                        AuditResult(
                            "UNVERIFIED",
                            identity,
                            "applicable host activation has no effective probe evidence",
                        )
                    )

            verification = declaration.verification
            verification_failures = _audit_probe_evidence(project_root, verification)
            if verification.state in {"PASS", "ADVISORY"}:
                if verification.verified_at is None:
                    verification_failures.append("positive verification has no verifiedAt value")
                if verification.verifier_version != framework_version:
                    verification_failures.append(
                        "stale verifierVersion "
                        f"{verification.verifier_version!r}; expected {framework_version!r}"
                    )
                if installation_status != "PASS":
                    verification_failures.append("positive verification depends on failed installation")
                verification_status = (
                    "FAIL" if verification_failures else verification.state
                )
                detail = (
                    "; ".join(verification_failures)
                    if verification_failures
                    else f"verified at {verification.verified_at} by Meridian {verification.verifier_version}"
                )
            elif verification.state == "NOT_APPLICABLE":
                verification_status = "FAIL"
                detail = "capability is catalog-applicable, so NOT_APPLICABLE is contradictory"
            elif verification.state == "FAIL":
                verification_status = "FAIL"
                detail = "persisted verification state is FAIL"
            else:
                verification_status = "UNVERIFIED"
                detail = "applicable capability lacks current verification evidence"
            results.append(
                AuditResult(verification_status, f"{prefix}/verification", detail)
            )
    return results, workflow_mode


def run_audit(
    project_root: Path,
    framework_root: Path,
    mode: str,
    ci_profile: str | None = None,
) -> int:
    results, locked_mode = audit_declared_capabilities(project_root, framework_root, mode)
    legacy_checks = (
        ("marker-integrity", audit_capability_markers),
        ("duplicate-heading", audit_duplicate_headings),
        ("capability-move", audit_capability_moves),
    )
    for check_name, check in legacy_checks:
        try:
            check_results = check(project_root, framework_root, locked_mode)
        except MeridianError as error:
            results.append(AuditResult("FAIL", check_name, str(error)))
            continue
        for status, detail in check_results:
            normalized_status = "UNVERIFIED" if status == "SKIP" else status
            results.append(AuditResult(normalized_status, check_name, detail))
    for status, detail in audit_entry_router(project_root):
        results.append(AuditResult(status, "entry-router", detail))

    results.sort(key=lambda result: (result.identity, result.detail))
    for result in results:
        print(f"{result.status:14} {result.identity} — {result.detail}")

    counts = {state: 0 for state in AUDIT_STATES}
    for result in results:
        counts[result.status] += 1
    if counts["FAIL"]:
        aggregate = "FAIL"
        exit_code = 2
    elif counts["ADVISORY"] or counts["UNVERIFIED"]:
        aggregate = "UNVERIFIED" if counts["UNVERIFIED"] else "ADVISORY"
        exit_code = 1
    else:
        aggregate = "PASS"
        exit_code = 0
    summary = " ".join(f"{state}={counts[state]}" for state in AUDIT_STATES)
    print(f"SUMMARY worst={aggregate} {summary}")
    if ci_profile is not None:
        required = [
            result
            for result in results
            if result.status == "FAIL"
            or (
                result.identity.startswith(f"{ci_profile}/")
                and result.identity.endswith("/installation")
            )
        ]
        profile_installations = [
            result
            for result in required
            if result.identity.startswith(f"{ci_profile}/")
            and result.identity.endswith("/installation")
        ]
        required_failures = [result for result in required if result.status != "PASS"]
        if not profile_installations:
            required_failures.append(
                AuditResult(
                    "FAIL",
                    f"{ci_profile}/ci-gate",
                    "profile has no declared installation results",
                )
            )
        ci_status = "FAIL" if required_failures else "PASS"
        print(
            f"CI_GATE profile={ci_profile} worst={ci_status} "
            f"required={len(required)} failures={len(required_failures)}"
        )
        return 2 if required_failures else 0
    return exit_code


def _load_profile_probe(
    project_root: Path,
    relative_path: str,
    profile: CatalogProfile,
    expected_host: str,
) -> dict[str, object]:
    path = project_root / relative_path
    if not path.is_file():
        raise MeridianError(f"required probe is missing: {relative_path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MeridianError(f"required probe is invalid JSON: {relative_path}") from error
    data = _required_object(value, f"probe {relative_path}")
    if data.get("schemaVersion") != 1:
        raise MeridianError(f"probe {relative_path} must use schemaVersion 1")
    if data.get("profileId") != profile.profile_id or data.get("profileVersion") != profile.version:
        raise MeridianError(f"probe {relative_path} targets the wrong profile version")
    if data.get("hostProfile") != expected_host:
        raise MeridianError(f"probe {relative_path} must target host profile {expected_host}")
    for field in ("host", "hostVersion", "invocationMode", "configurationLayer", "fallback"):
        _required_string(data.get(field), f"probe {relative_path}.{field}")
    state = _required_string(data.get("state"), f"probe {relative_path}.state")
    if state not in {"PASS", "ADVISORY", "UNSUPPORTED", "UNVERIFIED"}:
        raise MeridianError(f"probe {relative_path}.state is unsupported: {state}")
    for field in ("observationTime", "evidenceArtifact"):
        field_value = data.get(field)
        if field_value is not None and (not isinstance(field_value, str) or not field_value.strip()):
            raise MeridianError(f"probe {relative_path}.{field} must be null or a non-empty string")
    if state == "PASS" and (data.get("observationTime") is None or data.get("evidenceArtifact") is None):
        raise MeridianError(f"probe {relative_path} PASS requires observationTime and evidenceArtifact")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        raise MeridianError(f"probe {relative_path}.checks must be a non-empty list")
    covered: set[str] = set()
    for index, raw_check in enumerate(checks):
        check = _required_object(raw_check, f"probe {relative_path}.checks[{index}]")
        capability_id = _required_string(
            check.get("capability"), f"probe {relative_path}.checks[{index}].capability"
        )
        if capability_id not in dict(profile.capabilities):
            raise MeridianError(f"probe {relative_path} names undeclared capability {capability_id}")
        _required_string(check.get("behavior"), f"probe {relative_path}.checks[{index}].behavior")
        dimensions = _required_string_list(
            check.get("dimensions"), f"probe {relative_path}.checks[{index}].dimensions", non_empty=True
        )
        if len(set(dimensions)) != len(dimensions):
            raise MeridianError(f"probe {relative_path} has duplicate check dimensions")
        covered.add(capability_id)
    data["_coveredCapabilities"] = sorted(covered)
    return data


def profile_doctor(project_root: Path, framework_root: Path, profile_id: str) -> int:
    """Resolve a profile and all repository-owned evidence without mutation."""
    results: list[AuditResult] = []
    try:
        manifest = load_manifest(project_root, framework_root)
        catalog = load_capability_catalog(framework_root)
        profile = catalog.profile(profile_id)
        if profile is None:
            raise MeridianError(f"capability profile is not present in the catalog: {profile_id}")
        declarations = {item.profile_id: item for item in parse_capability_profiles(manifest, catalog)}
        declaration = declarations.get(profile_id)
        if declaration is None:
            raise MeridianError(f"manifest does not declare capability profile: {profile_id}")
        audit_results, _mode = audit_declared_capabilities(
            project_root, framework_root, manifest_workflow_mode(manifest)
        )
        for result in audit_results:
            if result.identity.startswith(f"{profile_id}/") and result.identity.endswith("/installation"):
                results.append(result)
        for capability in declaration.capabilities:
            references = list(capability.installation.evidence)
            references.extend(
                reference
                for _host, snapshot in capability.host_activation
                for reference in snapshot.evidence
            )
            references.extend(capability.verification.evidence)
            for reference in references:
                if reference.startswith(("path:", "probe:")):
                    raw_path = reference.split(":", 1)[1]
                    relative = _repository_relative_path(raw_path, "profile evidence path")
                    status = "PASS" if (project_root / relative).is_file() else "FAIL"
                    results.append(AuditResult(status, f"{profile_id}/evidence/{relative}", "resolved" if status == "PASS" else "missing"))
        ci_probe = _load_profile_probe(
            project_root, profile.verification_probe, profile, "host-neutral-ci"
        )
        missing_ci = sorted(set(dict(profile.capabilities)) - set(ci_probe["_coveredCapabilities"]))
        results.append(AuditResult(
            "FAIL" if missing_ci else "PASS",
            f"{profile_id}/probe/host-neutral-ci",
            "missing capability checks: " + ", ".join(missing_ci) if missing_ci else f"resolved {profile.verification_probe}",
        ))
        supported_by_host: dict[str, set[str]] = {}
        for capability_id, _version in profile.capabilities:
            capability = catalog.capability(capability_id)
            assert capability is not None
            for host_id, _kind in capability.host_profiles:
                supported_by_host.setdefault(host_id, set()).add(capability_id)
        for host_id, probe_path in profile.host_probes:
            probe = _load_profile_probe(project_root, probe_path, profile, host_id)
            missing = sorted(supported_by_host[host_id] - set(probe["_coveredCapabilities"]))
            results.append(AuditResult(
                "FAIL" if missing else "PASS",
                f"{profile_id}/probe/{host_id}",
                "missing capability checks: " + ", ".join(missing) if missing else f"resolved {probe_path}; host state={probe['state']}",
            ))
    except MeridianError as error:
        results.append(AuditResult("FAIL", f"{profile_id}/doctor", str(error)))
    results.sort(key=lambda result: (result.identity, result.detail))
    for result in results:
        print(f"{result.status:14} {result.identity} — {result.detail}")
    failures = sum(result.status == "FAIL" for result in results)
    print(f"SUMMARY profile={profile_id} PASS={sum(result.status == 'PASS' for result in results)} FAIL={failures}")
    return 2 if failures else 0


def bootstrap_capability_profile(
    project_root: Path, framework_root: Path, profile_id: str, *, apply: bool
) -> dict[str, object]:
    """Observe catalog surfaces and conservatively declare one profile.

    Static files can establish installation only. Host activation and
    capability verification remain UNVERIFIED until a versioned probe records
    stronger evidence.
    """
    manifest = load_manifest(project_root, framework_root)
    catalog = load_capability_catalog(framework_root)
    profile = catalog.profile(profile_id)
    if profile is None:
        raise MeridianError(f"capability profile is not present in the catalog: {profile_id}")
    workflow_mode = manifest_workflow_mode(manifest)
    declarations: dict[str, object] = {}
    managed_files = dict(manifest.get("managedFiles", {}))
    for capability_id, required_version in profile.capabilities:
        capability = catalog.capability(capability_id)
        assert capability is not None
        if workflow_mode not in capability.workflow_modes:
            raise MeridianError(
                f"profile {profile_id} capability {capability_id} excludes workflow {workflow_mode}"
            )
        surfaces: list[dict[str, str]] = []
        evidence: list[str] = []
        complete = True
        for surface in capability.managed_surfaces:
            form = surface.forms[0]
            surfaces.append({"path": surface.path, "form": form})
            path = project_root / surface.path
            if form != "declaration-only" and not path.is_file():
                complete = False
                continue
            if form != "declaration-only":
                digest = sha256(path)
                evidence.append(f"sha256:{digest}")
                if form == "managed-copy":
                    managed_files[surface.path] = digest
        declarations[capability_id] = {
            "requiredVersion": required_version,
            "managedSurface": surfaces,
            "installation": {
                "state": "INSTALLED" if complete else "MISSING",
                "evidence": sorted(set(evidence)),
                "notApplicableRationale": None,
            },
            "hostActivation": {
                host_id: {
                    "state": "UNVERIFIED",
                    "evidence": [],
                    "notApplicableRationale": None,
                }
                for host_id, _evidence_kind in capability.host_profiles
            },
            "verification": {
                "state": "UNVERIFIED",
                "evidence": [],
                "verifiedAt": None,
                "verifierVersion": None,
                "notApplicableRationale": None,
            },
        }
    updated = canonical_manifest(manifest)
    profiles = dict(updated.get("capabilityProfiles", {}))
    profiles[profile_id] = {
        "profileVersion": profile.version,
        "capabilities": declarations,
    }
    updated["capabilityProfiles"] = profiles
    updated["managedFiles"] = dict(sorted(managed_files.items()))
    validate_manifest(updated, catalog)
    if apply:
        write_manifest(project_root, updated, framework_root)
    return updated


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


def copy_baseline(
    project_root: Path,
    framework_root: Path,
    mode: str,
    version: str,
    managed_files_override: list[ManagedFile] | None = None,
) -> None:
    destination_root = project_root / BASELINES_PATH / version
    for item in managed_files_override or managed_files(framework_root, mode):
        destination = destination_root / item.target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item.source, destination)


def prune_stale_baselines(project_root: Path, keep_version: str) -> None:
    """Remove every baseline snapshot except the one the manifest now points at.

    Only the baseline matching `manifest.workflowBaselineVersion` is ever read again
    (see `plan_upgrade`); older snapshots are dead weight the moment an
    upgrade or adoption completes.
    """
    baselines_root = project_root / BASELINES_PATH
    if not baselines_root.is_dir():
        return
    for entry in baselines_root.iterdir():
        if entry.is_dir() and entry.name != keep_version:
            shutil.rmtree(entry)


def lock_project(
    project_root: Path,
    framework_root: Path,
    mode: str,
) -> None:
    require_release_version(framework_root)
    version = read_version(framework_root)
    baseline_version = latest_migration_to(framework_root, version)
    files = managed_files(framework_root, mode)
    missing = [str(item.target) for item in files if not (project_root / item.target).is_file()]
    if missing:
        raise MeridianError("project is missing managed files: " + ", ".join(missing))

    copy_baseline(project_root, framework_root, mode, baseline_version)
    manifest = {
        "frameworkVersion": version,
        "protocolVersion": PROTOCOL_VERSION,
        "workflowMode": mode,
        "managedFiles": {str(item.target): sha256(item.source) for item in files},
        "appliedMigrations": migration_ids(framework_root, "0.0.0", baseline_version),
    }
    manifest["workflowBaselineVersion"] = baseline_version
    write_manifest(project_root, manifest, framework_root)
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


def apply_additive_move_checks(
    plan: list[PlanItem],
    project_root: Path,
    framework_root: Path,
    mode: str,
    baseline_root: Path,
    pending_migrations: list[str],
) -> list[PlanItem]:
    """Turn unsafe pending additive moves into deterministic upgrade conflicts.

    A normal three-way merge only reasons about whole files. A capability move
    instead proves the protected block itself: the old marker must be identical
    to the installed baseline, while unrelated project-owned text in that file
    remains eligible for preservation. A pre-created destination may be
    retained only if it is the exact released marker block.
    """
    by_target = {item.file.target: index for index, item in enumerate(plan)}
    derived_entry_points = {
        item.file.target for item in plan if item.action == "router"
    }

    def conflict(target: Path, detail: str) -> None:
        index = by_target[target]
        plan[index] = PlanItem(plan[index].file, "conflict", detail)

    for move in declared_capability_moves(framework_root, pending_migrations):
        if move.stage not in ("additive", "retirement"):
            continue
        if move.source_path in derived_entry_points or move.target_path in derived_entry_points:
            continue
        source_base = baseline_root / move.source_path
        source_local = project_root / move.source_path
        if not source_base.is_file() or not source_local.is_file():
            conflict(move.source_path, f"capability move {move.migration} source baseline or local file is missing")
            continue
        base_text = source_base.read_text(encoding="utf-8")
        local_text = source_local.read_text(encoding="utf-8")
        if move.source_path == Path("CLAUDE.md") and is_agents_pointer(local_text):
            # A declared pointer deliberately owns no duplicated Claude marker;
            # the matching AGENTS move supplies the source proof instead.
            continue
        source_in_intermediate_state = False
        if not exact_marker_matches(base_text, move.source_capability, move.source_version, move.source_sha256):
            source_in_intermediate_state = (
                not marker_blocks(base_text, move.source_capability, move.source_version)
                and not marker_blocks(local_text, move.source_capability, move.source_version)
                and pending_migration_establishes_move_source(
                    framework_root, pending_migrations, move
                )
            )
            if not source_in_intermediate_state:
                conflict(move.source_path, f"capability move {move.migration} source does not match the installed baseline")
                continue
        if not source_in_intermediate_state and not exact_marker_matches(
            local_text, move.source_capability, move.source_version, move.source_sha256
        ):
            conflict(move.source_path, f"capability move {move.migration} source marker was locally modified or duplicated")
            continue
        target_local = project_root / move.target_path
        if target_local.is_file():
            target_text = target_local.read_text(encoding="utf-8")
            if not exact_marker_matches(
                target_text, move.target_capability, move.target_version, move.target_sha256
            ):
                conflict(move.target_path, f"capability move {move.migration} target marker is not exact")
                continue
            current = plan[by_target[move.target_path]]
            if move.stage == "additive" and current.action == "conflict" and not (baseline_root / move.target_path).is_file():
                plan[by_target[move.target_path]] = PlanItem(
                    current.file,
                    "keep",
                    f"pre-created target marker for capability move {move.migration} is exact",
                )
        elif move.stage == "retirement":
            planned_target = plan[by_target[move.target_path]]
            incoming_target = planned_target.file.source.read_text(encoding="utf-8")
            if planned_target.action != "add" or not exact_marker_matches(
                incoming_target, move.target_capability, move.target_version, move.target_sha256
            ):
                conflict(move.target_path, f"capability move {move.migration} target file is missing")
        if move.stage == "retirement":
            current = plan[by_target[move.source_path]]
            if current.action == "append-markers":
                plan[by_target[move.source_path]] = PlanItem(
                    current.file,
                    "append-retire-markers",
                    "update required marker versions, then retire declared duplicate marker blocks "
                    "without touching other local text",
                )
    return plan


def plan_from_baseline(
    project_root: Path,
    framework_root: Path,
    mode: str,
    installed_version: str,
    baseline_root: Path,
    applied_migrations: list[object],
    target_version_override: str | None = None,
    managed_files_override: list[ManagedFile] | None = None,
    installed_framework_version: str | None = None,
    capability_profiles: object | None = None,
) -> tuple[dict[str, object], list[PlanItem]]:
    target_framework_version = target_version_override or read_version(framework_root)
    target_baseline_version = latest_migration_to(framework_root, target_framework_version)
    if version_key(target_baseline_version) < version_key(installed_version):
        raise MeridianError("framework source is older than the project lockfile")
    if not baseline_root.is_dir():
        raise MeridianError(f"baseline snapshot is missing: {baseline_root}")

    manifest: dict[str, object] = {
        "frameworkVersion": installed_framework_version or installed_version,
        "workflowBaselineVersion": installed_version,
        "workflowMode": mode,
        "appliedMigrations": applied_migrations,
    }
    if capability_profiles is not None:
        manifest["capabilityProfiles"] = capability_profiles

    requirements = capability_requirements(framework_root)
    applied = {str(migration) for migration in applied_migrations}
    pending_migrations = [
        migration
        for migration in migration_ids(framework_root, installed_version, target_baseline_version)
        if migration not in applied
    ]

    planned_files = managed_files_override or managed_files(framework_root, mode)
    router_project = project_uses_entry_router(project_root)
    router_problems = entry_router_trigger_requirements(
        project_root, framework_root, pending_migrations, planned_files
    )
    router_problem_owner = Path("AGENTS.md")

    plan = []
    for item in planned_files:
        if router_project and item.target in {Path("AGENTS.md"), Path("CLAUDE.md")}:
            plan.append(
                PlanItem(
                    item,
                    "router",
                    f"generated from {ENTRY_ROUTER_PATH}; template merge is disabled",
                    router_problems if item.target == router_problem_owner else (),
                )
            )
            continue
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
            local_text = local.read_text(encoding="utf-8")
            if (
                item.target == Path("CLAUDE.md")
                and CLAUDE_AGENTS_POINTER_MARKER not in local_text
                and "036-explicit-claude-agents-pointer" in pending_migrations
                and agents_pointer_satisfies_claude(
                    project_root, framework_root, mode, item.source.read_text(encoding="utf-8"), local_text
                )
            ):
                plan.append(
                    PlanItem(
                        item,
                        "pointer-upgrade",
                        "add the explicit Claude-to-AGENTS pointer marker without changing project-owned pointer text",
                    )
                )
                continue
            normalized = deduplicate_identical_template_markers(
                local_text, item.source.read_text(encoding="utf-8")
            )
            if normalized is not None:
                plan.append(
                    PlanItem(
                        item,
                        "deduplicate-markers",
                        "template unchanged, but local file contains duplicate identical protected marker(s)",
                    )
                )
            else:
                plan.append(PlanItem(item, "keep", "template unchanged"))
        elif sha256(local) == sha256(base):
            plan.append(PlanItem(item, "replace", "local file matches installed baseline"))
        elif sha256(local) == sha256(item.source):
            plan.append(PlanItem(item, "keep", "local file already matches target"))
        else:
            clean, merged = merge_clean(local, base, item.source)
            if clean:
                merged_text = merged.decode("utf-8")
                if deduplicate_identical_template_markers(
                    merged_text, item.source.read_text(encoding="utf-8")
                ) is not None:
                    plan.append(
                        PlanItem(
                            item,
                            "merge-deduplicate-markers",
                            "three-way merge duplicated an identical new protected marker; retain one canonical copy",
                        )
                    )
                else:
                    plan.append(PlanItem(item, "merge", "three-way merge"))
                continue
            local_text = local.read_text(encoding="utf-8")
            base_text = base.read_text(encoding="utf-8")
            template_text = item.source.read_text(encoding="utf-8")
            if item.target == Path("CLAUDE.md") and agents_pointer_can_follow_upgrade(
                project_root, framework_root, mode, baseline_root, template_text, local_text
            ):
                legacy_pointer = CLAUDE_AGENTS_POINTER_MARKER not in local_text
                action = (
                    "pointer-upgrade"
                    if legacy_pointer and "036-explicit-claude-agents-pointer" in pending_migrations
                    else "pointer-verified"
                )
                plan.append(
                    PlanItem(
                        item,
                        action,
                        "project declares CLAUDE.md as an AGENTS.md pointer; shared markers are current or "
                        "will be updated safely in AGENTS.md",
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
    if mode == "governed-sdd":
        plan = apply_additive_move_checks(
            plan,
            project_root,
            framework_root,
            mode,
            baseline_root,
            pending_migrations,
        )
    return manifest, plan


def prepare_upgrade_targets(
    project_root: Path, framework_root: Path, stop_before_retirement: bool
) -> tuple[dict[str, object], str | None, list[ManagedFile] | None]:
    """The manifest, plus an effective target-version cap and matching
    managed-files substitution when `--stop-before-retirement` is set and it
    actually narrows the upgrade. Both are `None` when the flag is unset, or
    the pending migrations contain no retirement-stage move (a full,
    unmodified upgrade)."""
    manifest = load_manifest(project_root, framework_root)
    if not stop_before_retirement:
        return manifest, None, None
    installed_version = manifest_baseline_version(manifest)
    full_target = read_version(framework_root)
    capped_target = capped_target_version(framework_root, installed_version, full_target)
    if capped_target == full_target:
        return manifest, None, None
    applied = {str(migration) for migration in manifest.get("appliedMigrations", [])}
    full_pending = set(migration_ids(framework_root, installed_version, full_target)) - applied
    capped_pending = set(migration_ids(framework_root, installed_version, capped_target)) - applied
    excluded = full_pending - capped_pending
    scratch_dir = Path(tempfile.mkdtemp(prefix="meridian-capped-"))
    baseline_root = project_root / BASELINES_PATH / installed_version
    managed_override = capped_managed_files(
        framework_root, manifest_workflow_mode(manifest), baseline_root, excluded, scratch_dir
    )
    return manifest, capped_target, managed_override


def plan_upgrade(
    project_root: Path, framework_root: Path, stop_before_retirement: bool = False
) -> tuple[dict[str, object], list[PlanItem]]:
    manifest, target_override, managed_override = prepare_upgrade_targets(
        project_root, framework_root, stop_before_retirement
    )
    installed_version = manifest_baseline_version(manifest)
    return plan_from_baseline(
        project_root,
        framework_root,
        manifest_workflow_mode(manifest),
        installed_version,
        project_root / BASELINES_PATH / installed_version,
        list(manifest.get("appliedMigrations", [])),
        target_version_override=target_override,
        managed_files_override=managed_override,
        installed_framework_version=str(manifest.get("frameworkVersion", "")),
        capability_profiles=manifest.get("capabilityProfiles"),
    )


def print_plan(
    manifest: dict[str, object],
    framework_root: Path,
    plan: list[PlanItem],
    target_version_override: str | None = None,
) -> None:
    target_version = target_version_override or read_version(framework_root)
    installed_baseline_version = manifest_baseline_version(manifest)
    target_baseline_version = latest_migration_to(framework_root, target_version)
    print(
        f"Meridian {installed_baseline_version} -> {target_baseline_version} "
        f"({manifest_workflow_mode(manifest)})"
    )
    framework_delta = f"Framework: {manifest['frameworkVersion']} -> {target_version}"
    if (
        str(manifest["frameworkVersion"]) != target_version
        and installed_baseline_version == target_baseline_version
    ):
        framework_delta += " (CLI-only; no baseline change)"
    print(framework_delta)
    applied = {str(item) for item in manifest.get("appliedMigrations", [])}
    pending = [
        migration
        for migration in migration_ids(
            framework_root, installed_baseline_version, target_baseline_version
        )
        if migration not in applied
    ]
    for migration in pending:
        print(f"MIGRATION {migration}")
    for item in plan:
        print(f"{item.action.upper():8} {item.file.target} — {item.detail}")
        for problem in item.problems:
            print(f"MISSING-ROUTER {problem}")
    conflicts = sum(item.action == "conflict" for item in plan)
    router_blockers = sum(bool(item.problems) for item in plan)
    if conflicts:
        print(f"BLOCKED: {conflicts} conflict(s); no files were changed.")
    if router_blockers:
        print(f"BLOCKED: {router_blockers} router requirement(s); no files were changed.")


def plan_has_blockers(plan: list[PlanItem], owner_reconciled: bool = False) -> bool:
    """Whether apply/check must stop before writing any project file."""
    return any(item.problems or (item.action == "conflict" and not owner_reconciled) for item in plan)


def apply_plan(
    project_root: Path,
    framework_root: Path,
    manifest: dict[str, object],
    plan: list[PlanItem],
    baseline_root: Path,
    owner_reconciled: bool = False,
    target_version_override: str | None = None,
    managed_files_override: list[ManagedFile] | None = None,
) -> None:
    print_plan(manifest, framework_root, plan, target_version_override=target_version_override)
    if plan_has_blockers(plan, owner_reconciled=owner_reconciled):
        raise MeridianError("upgrade has blocking plan items")

    installed_version = manifest_baseline_version(manifest)
    target_version = target_version_override or read_version(framework_root)
    target_baseline_version = latest_migration_to(framework_root, target_version)
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
            for migration in migration_ids(framework_root, installed_version, target_baseline_version)
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
            elif item.action == "merge-deduplicate-markers":
                _, merged = merge_clean(local, baseline_root / item.file.target, item.file.source)
                normalized = deduplicate_identical_template_markers(
                    merged.decode("utf-8"), item.file.source.read_text(encoding="utf-8")
                )
                if normalized is None:
                    raise MeridianError(
                        f"marker deduplication is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(normalized, encoding="utf-8")
            elif item.action == "deduplicate-markers":
                normalized = deduplicate_identical_template_markers(
                    local.read_text(encoding="utf-8"), item.file.source.read_text(encoding="utf-8")
                )
                if normalized is None:
                    raise MeridianError(
                        f"marker deduplication is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(normalized, encoding="utf-8")
            elif item.action == "pointer-upgrade":
                local_text = local.read_text(encoding="utf-8")
                if not agents_pointer_satisfies_claude(
                    project_root,
                    framework_root,
                    manifest_workflow_mode(manifest),
                    item.file.source.read_text(encoding="utf-8"),
                    local_text,
                ):
                    raise MeridianError(
                        f"AGENTS.md no longer satisfies the Claude pointer for {item.file.target}; rerun upgrade --check"
                    )
                if CLAUDE_AGENTS_POINTER_MARKER not in local_text:
                    first_newline = local_text.find("\n")
                    insertion = CLAUDE_AGENTS_POINTER_MARKER + "\n"
                    updated = (
                        insertion + "\n" + local_text
                        if first_newline < 0
                        else local_text[: first_newline + 1] + "\n" + insertion + local_text[first_newline + 1 :]
                    )
                    local.write_text(updated, encoding="utf-8")
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
            elif item.action == "append-retire-markers":
                base = baseline_root / item.file.target
                appended = append_only_new_markers(
                    local.read_text(encoding="utf-8"),
                    base.read_text(encoding="utf-8"),
                    item.file.source.read_text(encoding="utf-8"),
                )
                removals = removals_for_managed_file(framework_root, pending_migrations, item.file.target)
                removal_pairs = [(capability, version) for capability, version, _superseded_by in removals]
                retired = remove_retired_markers(appended or "", base.read_text(encoding="utf-8"), removal_pairs)
                if appended is None or retired is None:
                    raise MeridianError(
                        f"marker-aware relocation is no longer safe for {item.file.target}; rerun upgrade --check"
                    )
                local.write_text(retired, encoding="utf-8")
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

    if project_uses_entry_router(project_root):
        for target, output in entry_router_outputs(project_root).items():
            (project_root / target).write_text(output, encoding="utf-8")
        router_failures = [
            detail for status, detail in audit_entry_router(project_root) if status == "FAIL"
        ]
        if router_failures:
            raise MeridianError(
                "entry-router audit failed after regeneration: " + "; ".join(router_failures)
            )

    if target_baseline_version != installed_version:
        copy_baseline(
            project_root,
            framework_root,
            manifest_workflow_mode(manifest),
            target_baseline_version,
            managed_files_override=managed_files_override,
        )
        prune_stale_baselines(project_root, target_baseline_version)
    manifest["frameworkVersion"] = target_version
    manifest["workflowBaselineVersion"] = target_baseline_version
    manifest["protocolVersion"] = PROTOCOL_VERSION
    manifest["managedFiles"] = {}
    for item in managed_files_override or managed_files(framework_root, manifest_workflow_mode(manifest)):
        digest_source = item.source
        if project_uses_entry_router(project_root) and item.target in {
            Path("AGENTS.md"),
            Path("CLAUDE.md"),
        }:
            digest_source = project_root / item.target
        manifest["managedFiles"][str(item.target)] = sha256(digest_source)
    prior = {str(item) for item in manifest.get("appliedMigrations", [])}
    prior.update(migration_ids(framework_root, installed_version, target_baseline_version))
    manifest["appliedMigrations"] = sorted(prior)
    write_manifest(project_root, manifest, framework_root)
    print("Upgrade applied. Review the diff, run project checks, then commit it.")


def apply_upgrade(
    project_root: Path,
    framework_root: Path,
    owner_reconciled: bool = False,
    stop_before_retirement: bool = False,
) -> None:
    require_release_version(framework_root)
    manifest, target_override, managed_override = prepare_upgrade_targets(
        project_root, framework_root, stop_before_retirement
    )
    installed_version = manifest_baseline_version(manifest)
    manifest, plan = plan_from_baseline(
        project_root,
        framework_root,
        manifest_workflow_mode(manifest),
        installed_version,
        project_root / BASELINES_PATH / installed_version,
        list(manifest.get("appliedMigrations", [])),
        target_version_override=target_override,
        managed_files_override=managed_override,
        installed_framework_version=str(manifest.get("frameworkVersion", "")),
        capability_profiles=manifest.get("capabilityProfiles"),
    )
    apply_plan(
        project_root,
        framework_root,
        manifest,
        plan,
        project_root / BASELINES_PATH / manifest_baseline_version(manifest),
        owner_reconciled=owner_reconciled,
        target_version_override=target_override,
        managed_files_override=managed_override,
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


def task_identity_json(project_root: Path, identity: ResolvedTaskIdentity) -> dict[str, object]:
    """Render the diagnostic with the same effective attempt used by budgets,
    without persisting the transition that a mutating budget command records.
    """
    state = load_budget_state(project_root)
    meta = dict(state.get(identity.canonical_id) or {"attempt": 1, "lastStatus": None})
    status = read_task_field(identity.task_path.read_text(encoding="utf-8"), "Status") or "UNKNOWN"
    attempt = int(meta.get("attempt", 1))
    if meta.get("lastStatus") == "READY_FOR_REVIEW" and status == "IN_PROGRESS":
        attempt += 1
    return identity.as_json(project_root, attempt)


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
    require_named_validation_commands(text)
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
    block_zone = ""
    if workflow.is_file():
        workflow_text = workflow.read_text(encoding="utf-8")
        block_match = re.search(
            r"<!-- MERIDIAN:BEGIN capability=execution-assets .*?<!-- MERIDIAN:END -->",
            workflow_text,
            re.DOTALL,
        )
        block_zone = block_match.group(0) if block_match else ""
        match = re.search(
            r"<!-- MERIDIAN:BEGIN capability=execution-assets .*?<!-- MERIDIAN:END -->\s*(.*?)(?=^## |\Z)",
            workflow_text,
            re.MULTILINE | re.DOTALL,
        )
        zone = match.group(1) if match else ""
    queue_matches = re.findall(r"`([^`]*queue[^`]*\.md)`", zone, re.IGNORECASE)
    queues = [Path(path) for path in dict.fromkeys(path for path in queue_matches if "archive" not in path.lower())]
    if len(queues) != 1:
        block_matches = re.findall(r"`([^`]*queue[^`]*\.md)`", block_zone, re.IGNORECASE)
        queues = [Path(path) for path in dict.fromkeys(path for path in block_matches if "archive" not in path.lower())]
    queue = queues[0] if len(queues) == 1 else Path("tasks/QUEUE.md")
    roots = [Path("tasks")]
    for raw in re.findall(r"task files live (?:at|under)\s+`([^`]+)`", zone + "\n" + block_zone, re.IGNORECASE):
        prefix = raw.split("<", 1)[0].rstrip("/")
        candidate = Path(prefix)
        root = candidate.parent if candidate.suffix else candidate
        if root not in roots:
            roots.append(root)
    adr_matches = re.findall(r"ADR log(?:\s+is|\s+at)?\s+`([^`]+)`", zone, re.IGNORECASE)
    if len(set(adr_matches)) != 1:
        adr_matches = re.findall(r"ADR log(?:\s+is|\s+at)?\s+`([^`]+)`", block_zone, re.IGNORECASE)
    adr_log = Path(adr_matches[0]) if len(set(adr_matches)) == 1 else Path("docs/ARCHITECTURE_DECISIONS.md")
    handoff_matches = re.findall(r"[Cc]ompletion handoffs live at `([^`]+)/<TASK-ID>\.md`", zone)
    if len(set(handoff_matches)) != 1:
        handoff_matches = re.findall(r"[Cc]ompletion handoffs live at `([^`]+)/<TASK-ID>\.md`", block_zone)
    review_matches = re.findall(r"(?:durable )?review records (?:live )?at `([^`]+)/<TASK-ID>\.md`", zone, re.IGNORECASE)
    if len(set(review_matches)) != 1:
        review_matches = re.findall(r"(?:durable )?review records (?:live )?at `([^`]+)/<TASK-ID>\.md`", block_zone, re.IGNORECASE)
    handoff_root = Path(handoff_matches[0]) if len(set(handoff_matches)) == 1 else Path("tasks/handoffs")
    review_root = Path(review_matches[0]) if len(set(review_matches)) == 1 else Path("tasks/reviews")
    for label, path in (
        ("queue", queue),
        ("ADR log", adr_log),
        ("handoff root", handoff_root),
        ("review root", review_root),
        *(("task root", root) for root in roots),
    ):
        if path.is_absolute() or ".." in path.parts:
            raise MeridianError(f"canonical {label} must be a safe project-relative path: {path}")
    return ProjectLocations(
        queue=queue,
        task_roots=tuple(roots),
        adr_log=adr_log,
        handoff_root=handoff_root,
        review_root=review_root,
    )


@dataclass(frozen=True)
class _TaskAuthority:
    canonical_id: str
    task_paths: tuple[Path, ...]
    queue_links: tuple[Path, ...]
    queue_records: int


def read_task_identity_policy(project_root: Path) -> TaskIdentityPolicy:
    path = project_root / TASK_IDENTITY_PATH
    if not path.is_file():
        return TaskIdentityPolicy(version=1, mode="opaque")
    try:
        declaration = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise MeridianError(f"invalid task identity declaration: {path}") from error
    if not isinstance(declaration, dict):
        raise MeridianError("task identity declaration must be a JSON object")
    if set(declaration) != {"version", "mode"}:
        raise MeridianError("task identity declaration accepts only version and mode")
    if type(declaration["version"]) is not int or declaration["version"] != 1:
        raise MeridianError(f"unsupported task identity policy version: {declaration['version']!r}")
    if declaration["mode"] not in ("opaque", "milestone"):
        raise MeridianError(f"unsupported task identity mode: {declaration['mode']!r}")
    return TaskIdentityPolicy(version=1, mode=str(declaration["mode"]))


def _task_record_id(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for pattern in (
        r"^>\s*\*\*ID\*\*:\s*`([^`]+)`\s*$",
        r"^ID:\s*`?([^`\s]+)`?\s*$",
    ):
        match = re.search(pattern, text, re.MULTILINE)
        if match and "[" not in match.group(1) and "<" not in match.group(1):
            return match.group(1)
    return None


def _clean_queue_id(cell: str) -> tuple[str, str | None]:
    cell = cell.strip().strip("`")
    link = re.fullmatch(r"\[([^]]+)\]\(([^)]+)\)", cell)
    if link:
        return link.group(1).strip().strip("`"), link.group(2).strip()
    return cell, None


def _task_authorities(project_root: Path, locations: ProjectLocations) -> dict[str, _TaskAuthority]:
    task_paths: dict[str, set[Path]] = {}
    queue_links: dict[str, set[Path]] = {}
    queue_counts: dict[str, int] = {}
    excluded_names = {"QUEUE.md", "QUEUE_ARCHIVE.md", "QUEUE_TEMPLATE.md", "TASK_BLUEPRINT.md"}
    for root in locations.task_roots:
        absolute = project_root / root
        if not absolute.is_dir():
            continue
        for path in absolute.rglob("*.md"):
            relative_parts = path.relative_to(absolute).parts
            if path.name in excluded_names or {"handoffs", "reviews"}.intersection(relative_parts):
                continue
            canonical = _task_record_id(path) or path.stem
            task_paths.setdefault(canonical, set()).add(path.resolve())

    queue_path = (project_root / locations.queue).resolve()
    if queue_path.is_file():
        lines = queue_path.read_text(encoding="utf-8").splitlines()
        headers: list[str] | None = None
        for line in lines:
            if not line.lstrip().startswith("|"):
                headers = None
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if "ID" in cells:
                headers = cells
                continue
            if headers is None or len(cells) != len(headers) or set("".join(cells)) <= {"-", ":"}:
                continue
            canonical, inline_link = _clean_queue_id(cells[headers.index("ID")])
            if not canonical or canonical in ("ID", "[ID]"):
                continue
            queue_counts[canonical] = queue_counts.get(canonical, 0) + 1
            link_value = inline_link
            for heading in ("Task file", "File"):
                if heading in headers:
                    _label, candidate = _clean_queue_id(cells[headers.index(heading)])
                    link_value = candidate or link_value
            if link_value and "://" not in link_value and not link_value.startswith("#"):
                resolved = (queue_path.parent / link_value.split("#", 1)[0]).resolve()
                if project_root.resolve() not in (resolved, *resolved.parents):
                    raise MeridianError(f"queue task link escapes the project: {link_value}")
                queue_links.setdefault(canonical, set()).add(resolved)

    identities = set(task_paths) | set(queue_counts)
    return {
        canonical: _TaskAuthority(
            canonical,
            tuple(sorted(task_paths.get(canonical, set()))),
            tuple(sorted(queue_links.get(canonical, set()))),
            queue_counts.get(canonical, 0),
        )
        for canonical in identities
    }


def _numeric_alias_key(value: str) -> str | None:
    match = NUMERIC_TASK_ALIAS.fullmatch(value)
    if match is None or int(match.group(1)) <= 0:
        return None
    return match.group(1)


def _authority_matches(authorities: dict[str, _TaskAuthority], supplied_id: str) -> list[str]:
    if supplied_id in authorities:
        return [supplied_id]
    structured = STRUCTURED_TASK_ID.fullmatch(supplied_id.upper())
    if structured:
        candidate = supplied_id.upper()
        return [candidate] if candidate in authorities else []
    numeric = _numeric_alias_key(supplied_id)
    if numeric is None:
        return []
    return [canonical for canonical in authorities if _numeric_alias_key(canonical) == numeric]


def _identity_names(canonical_id: str, kind: str) -> tuple[str, str, dict[str, object] | None]:
    """Derive branch and artifact names without spawning Git."""
    structured = STRUCTURED_TASK_ID.fullmatch(canonical_id)
    semantic: dict[str, object] | None = None
    if kind == "structured":
        if structured is None:
            raise MeridianError(f"invalid structured task ID: {canonical_id!r}")
        semantic = {
            "milestone": int(structured.group("milestone")),
            "workstream": structured.group("workstream"),
            "ordinal": int(structured.group("ordinal")),
        }
        branch = canonical_id.lower()
    else:
        numeric = _numeric_alias_key(canonical_id)
        branch = f"task-{numeric}" if numeric is not None else canonical_id.lower()
    artifact = canonical_id
    normalized = unicodedata.normalize("NFKC", artifact)
    if normalized != artifact or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", artifact):
        raise MeridianError(f"task ID is not a safe filesystem component: {canonical_id!r}")
    if artifact in (".", "..") or artifact.casefold() in {"con", "prn", "aux", "nul"} or artifact.endswith((".", ".lock")):
        raise MeridianError(f"task ID is a reserved filesystem or Git component: {canonical_id!r}")
    return branch, artifact, semantic


def _check_branch_name(canonical_id: str, branch: str) -> None:
    checked = subprocess.run(
        ["git", "check-ref-format", "--branch", branch],
        text=True,
        capture_output=True,
        check=False,
    )
    if checked.returncode != 0 or not SAFE_PATH_COMPONENT.fullmatch(branch):
        raise MeridianError(f"task ID does not derive a safe Git branch: {canonical_id!r}")


def _identity_derivations(canonical_id: str, kind: str) -> tuple[str, str, dict[str, object] | None]:
    branch, artifact, semantic = _identity_names(canonical_id, kind)
    _check_branch_name(canonical_id, branch)
    return branch, artifact, semantic


def resolve_task_identity(
    project_root: Path,
    supplied_id: str,
    intent: str,
    *,
    check_queue_links: bool = True,
) -> ResolvedTaskIdentity:
    if intent not in ("existing", "new"):
        raise MeridianError(f"unsupported task identity intent: {intent!r}")
    project_root = project_root.resolve()
    supplied = supplied_id.strip()
    if not supplied or supplied != supplied_id.strip() or any(separator in supplied for separator in ("/", "\\")):
        raise MeridianError(f"invalid task ID: {supplied_id!r}")
    policy = read_task_identity_policy(project_root)
    locations = resolve_project_locations(project_root)
    authorities = _task_authorities(project_root, locations)
    matches = _authority_matches(authorities, supplied)
    if len(matches) > 1:
        raise MeridianError(f"ambiguous task identity {supplied_id!r}: {', '.join(sorted(matches))}")
    if intent == "existing" and not matches:
        raise MeridianError(f"unknown task identity: {supplied_id!r}")

    if matches:
        canonical = matches[0]
    elif policy.mode == "milestone":
        canonical = supplied.upper()
        if STRUCTURED_TASK_ID.fullmatch(canonical) is None:
            raise MeridianError("new milestone-mode tasks must use M<milestone>-<WORKSTREAM>-<ordinal>")
    else:
        canonical = supplied

    structured = STRUCTURED_TASK_ID.fullmatch(canonical)
    structured_casefold = STRUCTURED_TASK_ID.fullmatch(canonical.upper())
    if policy.mode == "milestone" and structured_casefold and structured is None:
        raise MeridianError(f"authoritative structured task ID is not canonical uppercase: {canonical!r}")
    if policy.mode == "milestone" and structured:
        kind = "structured"
    elif policy.mode == "milestone":
        if not matches:
            raise MeridianError(f"unknown legacy task identity: {supplied_id!r}")
        kind = "legacy-opaque"
    else:
        kind = "opaque"

    branch, artifact, semantic = _identity_derivations(canonical, kind)
    authority = authorities.get(canonical)
    if authority is not None:
        if len(authority.task_paths) > 1 or authority.queue_records > 1 or len(authority.queue_links) > 1:
            raise MeridianError(f"ambiguous authoritative artifacts for task {canonical}")
        if check_queue_links:
            linked_existing = tuple(path for path in authority.queue_links if path.is_file())
            if authority.queue_links and len(linked_existing) != len(authority.queue_links):
                raise MeridianError(f"queue link for task {canonical} does not resolve to an existing task file")
            if linked_existing and not authority.task_paths:
                raise MeridianError(f"queue and task authorities disagree for {canonical}")
            if authority.task_paths and linked_existing and authority.task_paths[0] != linked_existing[0]:
                raise MeridianError(f"task and queue authorities disagree for {canonical}")
        paths = authority.task_paths
        if not paths:
            raise MeridianError(f"task {canonical} has no authoritative task file")
        task_path = paths[0]
    else:
        task_path = (project_root / locations.task_roots[0] / f"{artifact}.md").resolve()

    for other_id in authorities:
        if other_id == canonical:
            continue
        try:
            other_kind = "structured" if policy.mode == "milestone" and STRUCTURED_TASK_ID.fullmatch(other_id) else "opaque"
            other_branch, other_artifact, _other_semantic = _identity_names(other_id, other_kind)
            if other_branch.casefold() != branch.casefold() and other_artifact.casefold() != artifact.casefold():
                continue
            # Only a colliding ID needs the Git ref check, so the subprocess cost
            # does not grow with the number of known tasks.
            _check_branch_name(other_id, other_branch)
        except MeridianError:
            continue
        raise MeridianError(f"task identity collision between {canonical!r} and {other_id!r}")

    return ResolvedTaskIdentity(
        policy_version=policy.version,
        mode=policy.mode,
        kind=kind,
        canonical_id=canonical,
        branch_name=branch,
        artifact_stem=artifact,
        semantic_tuple=semantic,
        task_path=task_path,
        queue_path=(project_root / locations.queue).resolve(),
        handoff_path=(project_root / locations.handoff_root / f"{artifact}.md").resolve(),
        review_path=(project_root / locations.review_root / f"{artifact}.md").resolve(),
    )


HEADING_LINE = re.compile(r"^(#{1,6})[ \t]+(.*)$", re.MULTILINE)


def extract_heading_block(text: str, matches_title) -> tuple[str, str] | None:
    """Return `(excerpt, heading title)` for the first heading satisfying
    `matches_title(title)`, bounded by the next heading at the same or a
    shallower level, or EOF. Shared by ADR-log, spec, and task-Authority
    lookups so heading-range extraction is written exactly once.
    """
    headings = [
        (match.start(), len(match.group(1)), match.group(2).strip())
        for match in HEADING_LINE.finditer(text)
    ]
    for index, (start, level, title) in enumerate(headings):
        if not matches_title(title):
            continue
        end = len(text)
        for later_start, later_level, _ in headings[index + 1:]:
            if later_level <= level:
                end = later_start
                break
        return text[start:end].rstrip("\n") + "\n", title
    return None


def find_adr_log(project_root: Path) -> Path:
    return project_root / resolve_project_locations(project_root).adr_log


def adr_show(project_root: Path, adr_id: str) -> str:
    """Print exactly one ADR section, from its `## ADR-NNNN` heading up to the
    next `## ADR-` heading or EOF, without depending on contiguous numbering.
    """
    adr_log = find_adr_log(project_root)
    if not adr_log.is_file():
        raise MeridianError(f"ADR log not found for {adr_id}: {adr_log}")
    text = adr_log.read_text(encoding="utf-8")
    result = extract_heading_block(text, lambda title: re.match(rf"{re.escape(adr_id)}\b", title) is not None)
    if result is None:
        raise MeridianError(f"unknown ADR {adr_id}: not found in {adr_log}")
    excerpt, _ = result
    return excerpt


def extract_spec_heading(project_root: Path, spec_path: str, heading: str) -> str:
    full = project_root / spec_path
    if not full.is_file():
        raise MeridianError(f"spec file not found: {spec_path}")
    text = full.read_text(encoding="utf-8")
    result = extract_heading_block(text, lambda title: title.strip() == heading.strip())
    if result is None:
        raise MeridianError(f"heading not found in {spec_path}: {heading}")
    excerpt, _ = result
    return excerpt


def authority_entries(text: str) -> list[str]:
    """Every `## Authority` bullet, with wrapped continuation lines merged
    into the bullet they belong to."""
    section = extract_heading_block(text, lambda title: title == "Authority")
    if section is None:
        return []
    body = section[0].split("\n", 1)[1] if "\n" in section[0] else ""
    entries: list[str] = []
    for line in body.splitlines():
        if line.startswith("- "):
            entries.append(line[2:].strip())
        elif line.strip() and entries:
            entries[-1] += " " + line.strip()
    return entries


SPEC_HEADING_CITATION = re.compile(r"^`([^`]+)`#(.+)$")


def resolve_authority_entry(
    project_root: Path, entry: str
) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Resolve one Authority bullet to `(source, heading, excerpt)` triples,
    plus any part of the bullet that could not be resolved (named, not
    silently dropped): every `ADR-NNNN` token cited anywhere in the bullet
    resolves through `adr_show`; a `` `path`#Heading `` citation resolves
    through the same heading-range logic against that path; anything else is
    reported unresolved.
    """
    resolved: list[tuple[str, str, str]] = []
    unresolved: list[str] = []
    adr_ids = re.findall(r"\bADR-\d+\b", entry)
    if adr_ids:
        adr_log = find_adr_log(project_root)
        for adr_id in adr_ids:
            try:
                excerpt = adr_show(project_root, adr_id)
            except MeridianError:
                unresolved.append(f"{adr_id} (not found in {adr_log})")
                continue
            resolved.append((str(adr_log), adr_id, excerpt))
        return resolved, unresolved
    match = SPEC_HEADING_CITATION.match(entry.strip())
    if match:
        spec_path, heading = match.group(1), match.group(2).strip()
        try:
            excerpt = extract_spec_heading(project_root, spec_path, heading)
        except MeridianError as error:
            unresolved.append(f"{entry} ({error})")
            return resolved, unresolved
        resolved.append((spec_path, heading, excerpt))
        return resolved, unresolved
    unresolved.append(entry)
    return resolved, unresolved


def context_authority(project_root: Path, task_id: str, labels_only: bool = False) -> str:
    """Print the task's cited ADR sections and spec headings, labeled with
    source path and heading, in place of opening the ADR log or spec file
    directly. `labels_only` drops excerpt bodies, keeping only source and
    heading, for the queue-briefing hook.
    """
    task = find_task_file(project_root, task_id)
    text = task.read_text(encoding="utf-8")
    entries = authority_entries(text)
    if not entries:
        return f"{task_id}: no Authority entries."
    lines: list[str] = []
    unresolved_all: list[str] = []
    for entry in entries:
        resolved, unresolved = resolve_authority_entry(project_root, entry)
        for source, heading, excerpt in resolved:
            lines.append(f"### {source} — {heading}")
            if not labels_only:
                lines.append(excerpt)
        unresolved_all.extend(unresolved)
    if unresolved_all:
        lines.append("### Unresolved")
        lines.extend(f"- {item}" for item in unresolved_all)
    return "\n".join(lines).rstrip("\n")


def task_cap(project_root: Path, text: str, kind: str) -> int:
    raw = read_task_field(text, BUDGET_FIELD_NAMES[kind])
    if raw and raw.isdigit():
        return int(raw)
    return profile_cap(project_root, kind)


def find_task_file(project_root: Path, task_id: str) -> Path:
    """Locate a task through the shared declaration-driven identity resolver."""
    return resolve_task_identity(project_root, task_id, "existing").task_path


def resolve_budget_key(project_root: Path, state: dict[str, object], task_id: str) -> tuple[str, str]:
    """Return the qualified `<TASK-ID>:<attempt>` state key and the task file's
    text, bumping `state`'s attempt bookkeeping in place when the task file
    shows a fresh READY_FOR_REVIEW -> IN_PROGRESS transition (a new
    remediation attempt) since the last time this was resolved.
    """
    identity = resolve_task_identity(project_root, task_id, "existing")
    task_file = identity.task_path
    text = task_file.read_text(encoding="utf-8")
    status = read_task_field(text, "Status") or "UNKNOWN"
    canonical_id = identity.canonical_id
    meta = dict(state.get(canonical_id) or {"attempt": 1, "lastStatus": None})
    if meta.get("lastStatus") == "READY_FOR_REVIEW" and status == "IN_PROGRESS":
        meta["attempt"] = int(meta.get("attempt", 1)) + 1
    meta["lastStatus"] = status
    state[canonical_id] = meta
    return identity.budget_key(int(meta["attempt"])), text


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
    stored = int(counters.get(counter_key, 0))
    count = stored + amount
    cap = task_cap(project_root, text, kind)
    if count > cap:
        raise MeridianError(
            f"{BUDGET_FIELD_NAMES[kind]} exhausted for {task_id}: "
            f"{stored} of {cap} allowed uses already recorded, {amount} more requested; "
            "return BLOCKED, do not raise the cap"
        )
    counters[counter_key] = count
    state[key] = counters
    write_budget_state(project_root, state)
    return count, cap


PREFLIGHT_HEADINGS = ("Authority", "Validation")
NORMAL_PREFLIGHT_HEADINGS = ("Expected code surface",)
SPIKE_PREFLIGHT_FIELDS = ("Question", "Budget", "Deliverable")
HANDOFF_FIELDS = (
    "Files changed",
    "Validation",
    "Validation skips",
    "Manual verification",
    "Acceptance criteria",
    "Budget usage",
    "Isolated exploration",
    "Blockers/deviations",
)
TASK_099_SKIP_TEST = "AgentLaunchTest.test_split_payload_compiles_as_applescript"
TASK_099_SKIP_REASON = "osacompile cannot resolve the iTerm2 dictionary in this environment:"
EXECUTION_EVIDENCE_PATH = Path(".meridian/execution-evidence.json")
HOST_IMPACT_STATES = ("enforced", "advisory", "unsupported", "unverified")
HOST_IMPACT_EVIDENCE_CATEGORIES = ("Static", "Host execution", "Manual activation")


def host_impact_section(text: str) -> str | None:
    """Return the optional host-impact declaration from a task record.

    Records created before the Task 044 blueprint deliberately have no such
    section.  They remain valid historical inputs rather than being rewritten
    solely to satisfy a newly introduced lifecycle gate.
    """
    section = re.search(r"^## Host impact\s*$\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return section.group(1) if section else None


def host_impact_field(section: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}:\s*(\S.*)$", section, re.MULTILINE)
    return match.group(1).strip() if match else None


def host_impact_required_profiles(section: str) -> list[tuple[str, str]]:
    """Validate a REQUIRED declaration and return its claimed profile states."""
    if not host_impact_field(section, "Policy outcome"):
        raise MeridianError("host-impact declaration BLOCKED: REQUIRED declaration is missing Policy outcome")

    table = re.search(
        r"^\|\s*Profile\s*\|\s*Before\s*\|\s*Intended after\s*\|\s*Activation preconditions\s*\|\s*Fallback\s*\|\s*$\n"
        r"^\|(?:\s*:?-+\s*\|){4}\s*:?-+\s*\|\s*$\n"
        r"((?:^\|.*\|\s*$\n?)+)",
        section,
        re.MULTILINE,
    )
    if table is None:
        raise MeridianError("host-impact declaration BLOCKED: REQUIRED declaration is missing the profile table")

    profiles: list[tuple[str, str]] = []
    for line in table.group(1).splitlines():
        if not line.strip():
            continue
        values = [value.strip() for value in line.strip().strip("|").split("|")]
        if len(values) != 5:
            raise MeridianError("host-impact declaration BLOCKED: profile table row must contain five fields")
        profile, before, intended_after, activation, fallback = values
        for name, value in (
            ("Profile", profile),
            ("Before", before),
            ("Intended after", intended_after),
            ("Activation preconditions", activation),
            ("Fallback", fallback),
        ):
            if not value:
                raise MeridianError(f"host-impact declaration BLOCKED: profile table is missing {name}")
        for name, value in (("Before", before), ("Intended after", intended_after)):
            if value not in HOST_IMPACT_STATES:
                raise MeridianError(
                    f"host-impact declaration BLOCKED: profile {profile!r} has invalid {name} state {value!r}"
                )
        profiles.append((profile, intended_after))

    for category in HOST_IMPACT_EVIDENCE_CATEGORIES:
        if not re.search(rf"^- {re.escape(category)}:\s*\S+", section, re.MULTILINE):
            raise MeridianError(f"host-impact declaration BLOCKED: REQUIRED declaration is missing {category} evidence plan")
    return profiles


def validate_host_impact_declaration(text: str) -> list[tuple[str, str]]:
    """Validate a Task 044 declaration, retaining pre-migration task records."""
    section = host_impact_section(text)
    if section is None:
        return []
    classification = host_impact_field(section, "Classification")
    if classification == "NOT_APPLICABLE":
        if not host_impact_field(section, "Rationale"):
            raise MeridianError("host-impact declaration BLOCKED: NOT_APPLICABLE declaration is missing Rationale")
        return []
    if classification == "REQUIRED":
        return host_impact_required_profiles(section)
    raise MeridianError(
        "host-impact declaration BLOCKED: Classification must be NOT_APPLICABLE or REQUIRED"
    )


def verify_host_impact_completion_evidence(text: str) -> None:
    """Require profile-specific durable evidence for each enforced claim."""
    section = host_impact_section(text)
    if section is None:
        return
    enforced_profiles = [profile for profile, state in validate_host_impact_declaration(text) if state == "enforced"]
    if not enforced_profiles:
        return
    evidence = {
        match.group(1).strip()
        for match in re.finditer(r"^- \[([^\]]+)\]:\s*\S+", section, re.MULTILINE)
    }
    missing = [profile for profile in enforced_profiles if profile not in evidence]
    if missing:
        raise MeridianError(
            "host-impact completion BLOCKED: enforced profile is missing Completion evidence: "
            + ", ".join(missing)
        )


def execution_preflight(project_root: Path, task_id: str) -> str:
    """Validate the minimum durable execution contract before implementation.

    This intentionally does not inspect a chat's reasoning setting: that is a
    host concern and is outside this command's authority.
    """
    identity = resolve_task_identity(project_root, task_id, "existing")
    task_file = identity.task_path
    text = task_file.read_text(encoding="utf-8")
    require_named_validation_commands(text)
    validate_host_impact_declaration(text)
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
    required_headings = PREFLIGHT_HEADINGS
    missing = [
        f"## {heading}"
        for heading in required_headings
        if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
    ]
    if read_task_field(text, "Class") == "SPIKE":
        missing.extend(field for field in SPIKE_PREFLIGHT_FIELDS if not read_task_field(text, field))
    else:
        missing.extend(
            f"## {heading}"
            for heading in NORMAL_PREFLIGHT_HEADINGS
            if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE)
        )
    if missing:
        raise MeridianError(
            "execution preflight BLOCKED: task is missing " + ", ".join(missing)
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
                if len(values) == len(columns) and values[columns.index("ID")] == identity.canonical_id:
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
    match = section.search(text)
    if match:
        separator = "\n\n" if match.end() < len(text) else "\n"
        reconciled = text[:match.start()] + generated + separator + text[match.end():]
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
    canonical_id = resolve_task_identity(project_root, task_id, "existing").canonical_id
    entries = state.get(canonical_id, [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise MeridianError(f"invalid execution evidence entries for {task_id}: {path}")
    return entries


def verify_validation_skips(report_text: str) -> None:
    """Accept only Task 099's named sandbox skip in a completion handoff."""
    reported = re.search(r"^- Validation skips:\s*(.+)$", report_text, re.MULTILINE)
    assert reported is not None  # HANDOFF_FIELDS has already checked its presence.
    value = reported.group(1).strip()
    validation = re.search(r"^- Validation:\s*(.+)$", report_text, re.MULTILINE)
    assert validation is not None  # HANDOFF_FIELDS has already checked its presence.
    failed_validation = re.search(r"\bexit\s+[1-9][0-9]*\b", validation.group(1))

    if value.lower() == "none":
        if failed_validation:
            raise MeridianError(
                "handoff check BLOCKED: report declares a failing validation without a named skip"
            )
        return

    if (
        TASK_099_SKIP_TEST not in value
        or TASK_099_SKIP_REASON not in value
        or "reported by `" not in value
    ):
        raise MeridianError(
            "handoff check BLOCKED: Validation skips must name "
            f"{TASK_099_SKIP_TEST}, its test-reported reason, and the reporting command"
        )
    if failed_validation:
        raise MeridianError(
            "handoff check BLOCKED: a named skip does not make a failing validation pass"
        )


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
    canonical_id = resolve_task_identity(project_root, task_id, "existing").canonical_id
    if f"Completion Report — {canonical_id}" not in text:
        raise MeridianError(f"handoff check BLOCKED: report does not identify {canonical_id}")
    verify_validation_skips(text)
    verify_execution_evidence(project_root, task_id, text)
    return f"Handoff evidence complete for {task_id}: {report}"


def default_handoff_path(project_root: Path, task_id: str) -> Path:
    return resolve_task_identity(project_root, task_id, "existing").handoff_path


def readiness_check(project_root: Path, task_id: str, report: Path) -> str:
    """Combine execution and handoff gates before a task enters review."""
    execution_preflight(project_root, task_id)
    verify_host_impact_completion_evidence(find_task_file(project_root, task_id).read_text(encoding="utf-8"))
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


def require_named_validation_commands(text: str) -> None:
    """Reject free-form Validation entries that the execution runner cannot run."""
    section = re.search(r"^## Validation\s*$\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if section is None:
        return
    entries = [line for line in section.group(1).splitlines() if line.startswith("- ")]
    if entries and len(validation_commands(text)) != len(entries):
        raise MeridianError(
            "execution contract BLOCKED: every Validation entry must use "
            "`- `validation-id`: `literal command``"
        )


def record_validation(project_root: Path, task_id: str, command_id: str, command: str, status: int) -> None:
    path = project_root / EXECUTION_EVIDENCE_PATH
    state: dict[str, object] = {}
    if path.is_file():
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise MeridianError(f"invalid execution evidence state: {path}") from error
    canonical_id = resolve_task_identity(project_root, task_id, "existing").canonical_id
    entries = list(state.get(canonical_id, []))
    entries.append({"id": command_id, "command": command, "exitStatus": status})
    state[canonical_id] = entries
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
    canonical_id = resolve_task_identity(project_root, task_id, "existing").canonical_id
    events = list(state.get(canonical_id, []))
    event: dict[str, object] = {"kind": kind, "gap": gap, "count": count, "cap": cap}
    if criterion:
        event["criterion"] = criterion
    if artifact:
        event["artifact"] = artifact
    events.append(event)
    state[canonical_id] = events
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
    canonical_id = resolve_task_identity(project_root, task_id, "existing").canonical_id
    events = list(state.get(canonical_id, []))
    events.append({
        "kind": "investigation",
        "question": question,
        "scope": scope,
        "sources": sources,
        "finding": finding,
        "count": count,
        "cap": cap,
    })
    state[canonical_id] = events
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
    "governed-sdd": "## Command triggers",
    "lean-delivery": "## Command triggers",
}


class MeridianArgumentParser(argparse.ArgumentParser):
    """Use sysexits-style usage status for machine-oriented namespaces."""

    def error(self, message: str) -> None:
        if " task identity" in self.prog or " worktree" in self.prog:
            self.print_usage(sys.stderr)
            self.exit(64, f"{self.prog}: error: {message}\n")
        super().error(message)


def generate_claude_md(mode: str, agents_text: str, existing_claude_text: str) -> str:
    anchors = (CLAUDE_MD_SHARED_ANCHOR[mode], "## Code organization") if mode == "governed-sdd" else (CLAUDE_MD_SHARED_ANCHOR[mode],)
    for anchor in anchors:
        pattern = re.compile(rf"^{re.escape(anchor)}$", re.MULTILINE)
        agents_match = pattern.search(agents_text)
        claude_match = pattern.search(existing_claude_text)
        if agents_match is not None and claude_match is not None:
            break
    else:
        raise MeridianError(f"AGENTS.md and CLAUDE.md ({mode}) do not share a supported anchor heading")
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


class ShowVersionAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(parse_semver(read_raw_version(namespace.framework_root)))
        parser.exit()


def main() -> int:
    parser = MeridianArgumentParser(prog="meridian")
    parser.add_argument(
        "--framework-root",
        type=Path,
        default=Path(os.environ.get("MERIDIAN_ROOT", Path(__file__).resolve().parents[1])),
    )
    parser.add_argument(
        "--version",
        action=ShowVersionAction,
        help="print the framework SemVer, including prerelease and build metadata",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    self_check = subparsers.add_parser(
        "self-check", help="inspect this Meridian installation"
    )
    self_check.add_argument(
        "--check-latest",
        action="store_true",
        required=True,
        help="query the latest public GitHub Release",
    )

    console = subparsers.add_parser(
        "console", help="open the read-only project state console"
    )
    console.add_argument("--project", type=Path, default=Path.cwd())
    console.add_argument(
        "--interval", type=float, default=2.0,
        help="seconds between local refreshes (default: 2)",
    )

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
    upgrade.add_argument(
        "--stop-before-retirement",
        action="store_true",
        help="cap this upgrade to the last migration before the first one that retires a "
        "duplicated entry-point marker, so a long-lag consumer can complete an additive-only "
        "release; a no-op if no pending migration retires anything",
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
    audit.add_argument(
        "--ci-profile",
        help="gate catalog-required static installation while retaining visible host UNVERIFIED rows",
    )

    profile_parser = subparsers.add_parser(
        "profile", help="inspect or bootstrap an effective capability profile"
    )
    profile_sub = profile_parser.add_subparsers(dest="profile_command", required=True)
    profile_doctor_parser = profile_sub.add_parser(
        "doctor", help="resolve a declared profile, its evidence, and required probes"
    )
    profile_doctor_parser.add_argument("profile_id")
    profile_doctor_parser.add_argument("--project", type=Path, default=Path.cwd())
    profile_bootstrap = profile_sub.add_parser(
        "bootstrap", help="observe installation surfaces without claiming host activation"
    )
    profile_bootstrap.add_argument("profile_id")
    profile_bootstrap.add_argument("--project", type=Path, default=Path.cwd())
    profile_action = profile_bootstrap.add_mutually_exclusive_group(required=True)
    profile_action.add_argument("--check", action="store_true")
    profile_action.add_argument("--apply", action="store_true")

    locations = subparsers.add_parser("locations", help="print resolved project queue and task locations")
    locations.add_argument("--project", type=Path, default=Path.cwd())
    locations.add_argument("--field", choices=("queue", "task-roots"))

    setup = subparsers.add_parser("setup", help="plan or apply worktree, Codex, and project Claude Code setup")
    setup_group = setup.add_mutually_exclusive_group(required=True)
    setup_group.add_argument("--check", action="store_true")
    setup_group.add_argument("--apply", action="store_true")
    setup.add_argument("--worktree-root", type=Path)
    setup.add_argument("--project", type=Path, default=Path.cwd())
    setup.add_argument("--config", type=Path, default=Path.home() / ".codex/config.toml", help=argparse.SUPPRESS)

    codex = subparsers.add_parser("codex", help="configure and diagnose Codex task-worktree access")
    codex_sub = codex.add_subparsers(dest="codex_command", required=True)
    codex_configure = codex_sub.add_parser("configure", help="plan or apply a bounded Codex permission profile")
    codex_configure_group = codex_configure.add_mutually_exclusive_group(required=True)
    codex_configure_group.add_argument("--check", action="store_true")
    codex_configure_group.add_argument("--apply", action="store_true")
    codex_configure.add_argument("--worktree-root", type=Path)
    codex_configure.add_argument("--config", type=Path, default=Path.home() / ".codex/config.toml", help=argparse.SUPPRESS)
    codex_configure.add_argument("--requirements", type=Path, help=argparse.SUPPRESS)
    codex_path = codex_sub.add_parser("worktree-path", help="derive one repository-qualified task worktree path")
    codex_path.add_argument("task_id")
    codex_path.add_argument("--project", type=Path, default=Path.cwd())
    codex_path.add_argument("--worktree-root", type=Path)
    codex_doctor_parser = codex_sub.add_parser("doctor", help="report Codex host capabilities separately")
    codex_doctor_parser.add_argument("--project", type=Path, default=Path.cwd())
    codex_doctor_parser.add_argument("--worktree-root", type=Path)
    codex_doctor_parser.add_argument("--config", type=Path, default=Path.home() / ".codex/config.toml", help=argparse.SUPPRESS)

    worktree = subparsers.add_parser("worktree", help="run the bounded host-neutral task-worktree lifecycle")
    worktree_sub = worktree.add_subparsers(dest="worktree_command", required=True)
    worktree_path_parser = worktree_sub.add_parser("path", help="derive the canonical task-worktree path")
    worktree_path_parser.add_argument("task_id")
    worktree_path_parser.add_argument("--project", type=Path)
    worktree_path_parser.add_argument("--worktree-root", type=Path)
    worktree_path_parser.add_argument("--format", choices=("json",))
    worktree_prepare = worktree_sub.add_parser("prepare", help="create or select exactly one canonical task worktree")
    worktree_prepare.add_argument("task_id")
    worktree_prepare.add_argument("--project", type=Path)
    worktree_prepare.add_argument("--worktree-root", type=Path)
    worktree_prepare.add_argument("--base", choices=("main",), default="main")
    worktree_prepare.add_argument("--format", choices=("json",), required=True)
    worktree_check = worktree_sub.add_parser("check", help="inspect the effective worker worktree without mutation")
    worktree_check.add_argument("task_id")
    worktree_check.add_argument("--project", type=Path)
    worktree_check.add_argument("--worktree-root", type=Path)
    worktree_check.add_argument("--format", choices=("json",), required=True)
    worktree_evidence = worktree_sub.add_parser(
        "evidence", help="record Git-derived task validation evidence without running commands"
    )
    worktree_evidence.add_argument("task_id")
    worktree_evidence.add_argument("--project", type=Path)
    worktree_evidence.add_argument("--worktree-root", type=Path)
    worktree_evidence.add_argument("--accepted", action="store_true")
    worktree_evidence.add_argument("--validation-command", action="append", default=[])
    worktree_evidence.add_argument("--validation-exit-code", action="append", type=int, default=[])
    worktree_evidence.add_argument("--task-dependency", action="append", default=[])
    worktree_evidence.add_argument("--task-behavioral-surface", action="append", default=[])
    worktree_evidence.add_argument("--main-advanced-dependency", action="append", default=[])
    worktree_evidence.add_argument("--main-advanced-behavioral-surface", action="append", default=[])
    worktree_evidence.add_argument("--full-validation-required", action="store_true")
    worktree_evidence.add_argument("--format", choices=("json",), required=True)
    worktree_closure_status = worktree_sub.add_parser(
        "closure-status", help="report the next closure step without changing lifecycle state"
    )
    worktree_closure_status.add_argument("task_id")
    worktree_closure_status.add_argument("--project", type=Path)
    worktree_closure_status.add_argument("--worktree-root", type=Path)
    worktree_closure_status.add_argument("--format", choices=("json",))
    worktree_integrate = worktree_sub.add_parser("integrate", help="stage, finalize, or abort one owned integration")
    integrate_sub = worktree_integrate.add_subparsers(dest="integrate_command", required=True)
    integrate_stage = integrate_sub.add_parser("stage", help="lease and stage the prescribed no-commit merge")
    integrate_stage.add_argument("task_id")
    integrate_stage.add_argument("--project", type=Path)
    integrate_stage.add_argument("--worktree-root", type=Path)
    integrate_stage.add_argument("--evidence", type=Path, required=True)
    integrate_stage.add_argument("--format", choices=("json",), required=True)
    integrate_finalize = integrate_sub.add_parser("finalize", help="commit an exactly validated staged candidate")
    integrate_finalize.add_argument("task_id")
    integrate_finalize.add_argument("--project", type=Path)
    integrate_finalize.add_argument("--evidence", type=Path, required=True)
    integrate_finalize.add_argument("--format", choices=("json",), required=True)
    integrate_abort = integrate_sub.add_parser("abort", help="abort one Meridian-owned staged integration")
    integrate_abort.add_argument("task_id")
    integrate_abort.add_argument("--project", type=Path)
    integrate_abort.add_argument("--format", choices=("json",), required=True)
    worktree_cleanup = worktree_sub.add_parser("cleanup", help="remove an integrated worktree and its merged local branch")
    worktree_cleanup.add_argument("task_id")
    worktree_cleanup.add_argument("--project", type=Path)
    worktree_cleanup.add_argument("--worktree-root", type=Path)
    worktree_cleanup.add_argument("--format", choices=("json",), required=True)

    validation = subparsers.add_parser("validation", help="read and verify an external validation evidence record")
    validation_sub = validation.add_subparsers(dest="validation_command", required=True)
    validation_check = validation_sub.add_parser("check", help="verify a record without running validation")
    validation_check.add_argument("record", type=Path)
    validation_check.add_argument("--project", type=Path, default=Path.cwd())
    validation_check.add_argument("--commit")
    validation_check.add_argument("--format", choices=("json",), required=True)

    task = subparsers.add_parser("task", help="inspect task records and identities")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    identity = task_sub.add_parser("identity", help="resolve the project-selected task identity policy")
    identity_sub = identity.add_subparsers(dest="identity_command", required=True)
    identity_check = identity_sub.add_parser("check", help="validate and print one resolved task identity")
    identity_check.add_argument("task_id")
    identity_check.add_argument("--project", type=Path, default=Path.cwd())
    identity_check.add_argument("--format", choices=("json",), required=True)

    adr = subparsers.add_parser("adr", help="read a project's ADR log")
    adr_sub = adr.add_subparsers(dest="adr_command", required=True)
    adr_show_parser = adr_sub.add_parser("show", help="print exactly one ADR section")
    adr_show_parser.add_argument("adr_id")
    adr_show_parser.add_argument("--project", type=Path, default=Path.cwd())

    context = subparsers.add_parser("context", help="read exactly the ADR/spec sections a task cites")
    context_sub = context.add_subparsers(dest="context_command", required=True)
    context_authority_parser = context_sub.add_parser(
        "authority", help="print a task's Authority entries resolved to ADR/spec excerpts"
    )
    context_authority_parser.add_argument("task_id")
    context_authority_parser.add_argument("--project", type=Path, default=Path.cwd())
    context_authority_parser.add_argument(
        "--labels-only", action="store_true", help="print source + heading only, not excerpt bodies"
    )

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

    generate_router = subparsers.add_parser(
        "generate-entry-routers",
        help="generate a consumer's AGENTS.md and CLAUDE.md from docs/workflows/ENTRY_ROUTER.md",
    )
    generate_router.add_argument("--project", type=Path, default=Path.cwd())
    generate_router_group = generate_router.add_mutually_exclusive_group(required=True)
    generate_router_group.add_argument("--check", action="store_true", help="exit non-zero if either generated entry point drifts")
    generate_router_group.add_argument("--write", action="store_true", help="write both generated entry points")

    hook = subparsers.add_parser("hook", help="run a Meridian host hook entry point")
    hook_sub = hook.add_subparsers(dest="hook_command", required=True)
    read_guard = hook_sub.add_parser("read-guard", help="apply the advisory-safe read guard")
    read_guard.add_argument("--host", choices=("codex",), required=True)

    arguments = parser.parse_args()
    framework_root = arguments.framework_root.resolve()
    project_root = (
        arguments.project.resolve()
        if hasattr(arguments, "project") and arguments.project is not None
        else None
    )
    try:
        if arguments.command == "self-check":
            return run_self_check(framework_root)
        if arguments.command == "console":
            if not 0.2 <= arguments.interval <= 60:
                raise MeridianError("--interval must be between 0.2 and 60")
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise MeridianError("interactive console requires a terminal")
            console_path = framework_root / "scripts" / "project_console.py"
            if not console_path.is_file():
                raise MeridianError(f"console is unavailable from framework root: {framework_root}")
            sys.path.insert(0, str(console_path.parent))
            import project_console

            return project_console.main([
                "--project", str(project_root), "--interval", str(arguments.interval),
            ])
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
            return run_audit(project_root, framework_root, mode, arguments.ci_profile)
        elif arguments.command == "profile":
            if arguments.profile_command == "doctor":
                return profile_doctor(project_root, framework_root, arguments.profile_id)
            manifest = bootstrap_capability_profile(
                project_root,
                framework_root,
                arguments.profile_id,
                apply=arguments.apply,
            )
            print(json.dumps(manifest["capabilityProfiles"][arguments.profile_id], indent=2, sort_keys=True))
        elif arguments.command == "locations":
            locations = resolve_project_locations(project_root)
            if arguments.field == "queue":
                print(locations.queue)
            elif arguments.field == "task-roots":
                print("\n".join(str(root) for root in locations.task_roots))
            else:
                print(json.dumps({"queue": str(locations.queue), "taskRoots": [str(root) for root in locations.task_roots]}))
        elif arguments.command == "setup":
            plan = plan_setup(
                arguments.worktree_root,
                arguments.config.expanduser().resolve(),
                framework_root=framework_root,
                project_root=arguments.project,
            )
            print_setup_plan(plan)
            if arguments.apply:
                changed = apply_setup(plan)
                print("result: updated; restart Codex" if changed else "result: no-op")
        elif arguments.command == "codex":
            resolved_root = resolve_worktree_root(arguments.worktree_root)
            if arguments.codex_command == "configure":
                plan = plan_codex_configuration(
                    arguments.config.expanduser().resolve(),
                    resolved_root.path,
                    arguments.requirements.expanduser().resolve() if arguments.requirements else None,
                )
                print_codex_configuration_plan(plan)
                if arguments.apply:
                    changed = apply_codex_configuration(plan)
                    if changed and plan.status in ("repair-required", "repair-and-replace-required"):
                        action = (
                            "ownership metadata repaired and root replaced"
                            if plan.status == "repair-and-replace-required"
                            else "ownership metadata repaired"
                        )
                        print(
                            f"result: {action}; this does not prove the running session loaded "
                            "the profile, so start a fresh Codex session and probe it"
                        )
                    else:
                        print("result: updated; restart Codex and select the profile" if changed else "result: no-op")
            elif arguments.codex_command == "worktree-path":
                path = task_worktree_path(project_root, resolved_root.path, arguments.task_id)
                validate_worktree_collision(project_root, path, arguments.task_id)
                print("DEPRECATED: use `meridian worktree path`", file=sys.stderr)
                print(path)
            else:
                report = codex_doctor(
                    project_root,
                    arguments.config.expanduser().resolve(),
                    resolved_root.path,
                    framework_root=framework_root,
                )
                for capability, status in report.items():
                    print(f"{capability}: {status}")
        elif arguments.command == "worktree":
            if arguments.worktree_command == "path":
                canonical_project = _verified_lifecycle_project(project_root)
                path_identity = resolve_task_identity(
                    canonical_project, arguments.task_id, "existing"
                )
                path = _task_worktree_path_for_identity(
                    canonical_project,
                    _effective_worktree_root(arguments.worktree_root),
                    path_identity,
                )
                validate_worktree_collision(canonical_project, path, arguments.task_id)
                if arguments.format == "json":
                    print(json.dumps({
                        "version": 1,
                        "path": str(path),
                        "handoff_worktree": handoff_worktree_value(
                            _effective_worktree_root(arguments.worktree_root), path
                        ),
                    }, sort_keys=True))
                else:
                    print(path)
            elif arguments.worktree_command == "prepare":
                print(json.dumps(prepare_task_worktree(
                    arguments.task_id,
                    arguments.worktree_root,
                    project_root,
                    arguments.base,
                ), sort_keys=True))
            elif arguments.worktree_command == "check":
                report, ready = inspect_task_worktree(
                    arguments.task_id,
                    arguments.worktree_root,
                    project_root,
                )
                print(json.dumps(report, sort_keys=True))
                if not ready:
                    return 2
            elif arguments.worktree_command == "evidence":
                print(json.dumps(record_task_evidence(
                    arguments.task_id,
                    arguments.worktree_root,
                    arguments.validation_command,
                    arguments.validation_exit_code,
                    accepted=arguments.accepted,
                    task_dependencies=arguments.task_dependency,
                    task_behavioral_surfaces=arguments.task_behavioral_surface,
                    main_advanced_dependencies=arguments.main_advanced_dependency,
                    main_advanced_behavioral_surfaces=arguments.main_advanced_behavioral_surface,
                    full_validation_required=arguments.full_validation_required,
                    supplied_project=project_root,
                ), sort_keys=True))
            elif arguments.worktree_command == "closure-status":
                report, ready = closure_status(
                    arguments.task_id,
                    arguments.worktree_root,
                    project_root,
                )
                if arguments.format == "json":
                    print(json.dumps(report, sort_keys=True))
                elif report["stop_reason"] is not None:
                    print(f"BLOCKED {report['stop_reason']}; resume: {report['resume']}")
                else:
                    print(f"{report['step']}; resume: {report['resume'] or 'none'}")
                if not ready:
                    return 2
            elif arguments.worktree_command == "integrate":
                if arguments.integrate_command == "stage":
                    result = stage_task_integration(
                        arguments.task_id,
                        arguments.worktree_root,
                        arguments.evidence,
                        project_root,
                    )
                elif arguments.integrate_command == "finalize":
                    result = finalize_task_integration(
                        arguments.task_id,
                        arguments.evidence,
                        project_root,
                    )
                else:
                    result = abort_task_integration(arguments.task_id, project_root)
                print(json.dumps(result, sort_keys=True))
            else:
                print(json.dumps(cleanup_task_worktree(
                    arguments.task_id,
                    arguments.worktree_root,
                    project_root,
                ), sort_keys=True))
        elif arguments.command == "task":
            resolved = resolve_task_identity(project_root, arguments.task_id, "existing")
            print(json.dumps(task_identity_json(project_root, resolved), sort_keys=True))
        elif arguments.command == "validation":
            report, exit_code = check_validation_evidence(
                arguments.record, canonical_project_root(project_root), arguments.commit
            )
            print(json.dumps(report, sort_keys=True))
            return exit_code
        elif arguments.command == "adr":
            print(adr_show(project_root, arguments.adr_id))
        elif arguments.command == "context":
            print(context_authority(project_root, arguments.task_id, arguments.labels_only))
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
        elif arguments.command == "generate-entry-routers":
            outputs = entry_router_outputs(project_root)
            drifted = [target for target, expected in outputs.items() if not (project_root / target).is_file() or (project_root / target).read_text(encoding="utf-8") != expected]
            if arguments.check:
                if drifted:
                    print("STALE generated entry router(s): " + ", ".join(str(path) for path in drifted), file=sys.stderr)
                    return 2
                print("Generated entry routers match their canonical source.")
            else:
                for target, output in outputs.items():
                    (project_root / target).write_text(output, encoding="utf-8")
                print("Generated AGENTS.md and CLAUDE.md from ENTRY_ROUTER.md.")
        elif arguments.command == "hook":
            if arguments.hook_command == "read-guard" and arguments.host == "codex":
                from codex_read_guard import main as codex_read_guard_main

                return codex_read_guard_main()
        elif arguments.check:
            if arguments.owner_reconciled:
                raise MeridianError("--owner-reconciled only applies to --apply")
            base_manifest, target_override, managed_override = prepare_upgrade_targets(
                project_root, framework_root, arguments.stop_before_retirement
            )
            installed_version = manifest_baseline_version(base_manifest)
            manifest, plan = plan_from_baseline(
                project_root,
                framework_root,
                manifest_workflow_mode(base_manifest),
                installed_version,
                project_root / BASELINES_PATH / installed_version,
                list(base_manifest.get("appliedMigrations", [])),
                target_version_override=target_override,
                managed_files_override=managed_override,
                installed_framework_version=str(base_manifest.get("frameworkVersion", "")),
                capability_profiles=base_manifest.get("capabilityProfiles"),
            )
            print_plan(manifest, framework_root, plan, target_version_override=target_override)
            if plan_has_blockers(plan):
                return 2
        else:
            apply_upgrade(
                project_root,
                framework_root,
                arguments.owner_reconciled,
                arguments.stop_before_retirement,
            )
    except MeridianError as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"BLOCKED: operating-system access failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
