#!/usr/bin/env python3
"""Prepare one local Meridian release without contacting the network."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"\d+\.\d+\.\d+\Z")
CLI_ONLY = "CLI-only release"
TEMPLATE_CHANGING = "Template-changing release"


class ReleaseError(Exception):
    """A release precondition is not satisfied."""


def version_key(value: str) -> tuple[int, int, int]:
    if not VERSION.fullmatch(value):
        raise ReleaseError(f"version must be plain X.Y.Z, got {value!r}")
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def newest_record(root: Path) -> dict[str, object]:
    records = []
    for path in (root / "releases").glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            version_key(str(record["version"]))
            records.append(record)
        except (json.JSONDecodeError, KeyError, ReleaseError) as error:
            raise ReleaseError(f"invalid release ledger record {path.relative_to(root)}: {error}") from error
    if not records:
        raise ReleaseError("release ledger has no records")
    return max(records, key=lambda record: version_key(str(record["version"])))


def read_migrations(root: Path) -> list[dict[str, object]]:
    result = []
    for path in (root / "migrations").glob("[0-9][0-9][0-9]-*.json"):
        try:
            result.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as error:
            raise ReleaseError(f"invalid migration {path.relative_to(root)}: {error}") from error
    return result


def unreleased_body(changelog: str) -> tuple[int, int, str]:
    match = re.search(r"^## \[Unreleased\]\s*$", changelog, re.MULTILINE)
    if not match:
        raise ReleaseError("CHANGELOG.md has no '## [Unreleased]' heading")
    body_start = match.end()
    following = re.search(r"^## \[", changelog[body_start:], re.MULTILINE)
    body_end = body_start + following.start() if following else len(changelog)
    body = changelog[body_start:body_end].strip()
    if not body:
        raise ReleaseError("CHANGELOG.md '## [Unreleased]' has an empty body")
    return body_start, body_end, body


def has_upgrade_notes(body: str) -> bool:
    match = re.search(r"^###\s+Upgrade notes\s*$", body, re.MULTILINE | re.IGNORECASE)
    if not match:
        return False
    following = re.search(r"^#{1,3}\s+", body[match.end():], re.MULTILINE)
    end = match.end() + following.start() if following else len(body)
    return bool(body[match.end():end].strip())


def derive_release(root: Path, new_version: str, previous: dict[str, object], body: str) -> tuple[str, list[str], str]:
    previous_baseline = str(previous["workflowBaselineVersion"])
    introduced = [
        migration for migration in read_migrations(root)
        if version_key(str(migration["to"])) > version_key(previous_baseline)
    ]
    if not introduced:
        return CLI_ONLY, [], previous_baseline
    targets = {str(migration["to"]) for migration in introduced}
    if targets != {new_version}:
        raise ReleaseError(
            "BLOCKED: introduced migrations must all target the new version "
            f"{new_version}; found {', '.join(sorted(targets, key=version_key))}"
        )
    if not has_upgrade_notes(body):
        raise ReleaseError("BLOCKED: template-changing release needs a non-empty '### Upgrade notes' subsection")
    return TEMPLATE_CHANGING, [str(migration["id"]) for migration in introduced], new_version


def preflight(root: Path, new_version: str) -> tuple[dict[str, object], str, str, list[str], str, int]:
    branch = run_git(root, "branch", "--show-current")
    if branch.returncode or branch.stdout.strip() != "main":
        raise ReleaseError("preflight failed: current branch must be main")
    status = run_git(root, "status", "--porcelain")
    if status.returncode or status.stdout.strip():
        raise ReleaseError("preflight failed: working tree must be clean")
    current = (root / "VERSION").read_text(encoding="utf-8").strip()
    version_key(current)
    if version_key(new_version) <= version_key(current):
        raise ReleaseError(f"preflight failed: new version {new_version} must be greater than {current}")
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    previous = newest_record(root)
    if plugin.get("version") != current or str(previous.get("version")) != current:
        raise ReleaseError("preflight failed: VERSION, .claude-plugin/plugin.json, and newest release ledger record must agree")
    tag = run_git(root, "tag", "--list", f"v{new_version}")
    if tag.returncode or tag.stdout.strip():
        raise ReleaseError(f"preflight failed: local tag v{new_version} already exists")
    _start, _end, body = unreleased_body((root / "CHANGELOG.md").read_text(encoding="utf-8"))
    kind, migrations, baseline = derive_release(root, new_version, previous, body)
    protocol = protocol_version(root)
    old_protocol = previous.get("protocolVersion")
    return previous, body, kind, migrations, baseline, protocol if isinstance(protocol, int) else 0


def protocol_version(root: Path) -> int:
    source = (root / "scripts" / "meridian.py").read_text(encoding="utf-8")
    match = re.search(r"^PROTOCOL_VERSION\s*=\s*(\d+)\s*$", source, re.MULTILINE)
    if not match:
        raise ReleaseError("could not read PROTOCOL_VERSION from scripts/meridian.py")
    return int(match.group(1))


def render_changelog(changelog: str, version: str, kind: str, body: str) -> str:
    start, end, _ = unreleased_body(changelog)
    summary = "this release introduces no migration." if kind == CLI_ONLY else "this release advances the workflow baseline."
    section = f"\n\n## [{version}]\n\n{kind}: {summary}\n\n{body}\n\n"
    return changelog[:start] + "\n\n" + section + changelog[end:].lstrip("\n")


def write_release(root: Path, version: str, date: str, kind: str, migrations: list[str], baseline: str, protocol: int, body: str) -> list[Path]:
    version_path = root / "VERSION"
    plugin_path = root / ".claude-plugin" / "plugin.json"
    ledger_path = root / "releases" / f"{version}.json"
    changelog_path = root / "CHANGELOG.md"
    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    plugin["version"] = version
    version_path.write_text(f"{version}\n", encoding="utf-8")
    plugin_path.write_text(json.dumps(plugin, indent=2) + "\n", encoding="utf-8")
    ledger_path.write_text(json.dumps({"version": version, "releaseDate": date, "gitTag": f"v{version}", "protocolVersion": protocol, "workflowBaselineVersion": baseline, "baselineChanged": bool(migrations), "migrations": migrations}, indent=2) + "\n", encoding="utf-8")
    changelog_path.write_text(render_changelog(changelog_path.read_text(encoding="utf-8"), version, kind, body), encoding="utf-8")
    return [version_path, plugin_path, ledger_path, changelog_path]


def restore(root: Path, paths: list[Path]) -> None:
    for path in paths:
        relative = path.relative_to(root)
        if run_git(root, "cat-file", "-e", f"HEAD:{relative}").returncode == 0:
            run_git(root, "checkout", "HEAD", "--", str(relative))
        elif path.exists():
            path.unlink()


def validate(root: Path, version: str) -> tuple[int, list[str]]:
    notes = tempfile.NamedTemporaryFile(prefix="meridian-release-", suffix=".md", delete=False)
    notes.close()
    commands = [
        [sys.executable, "scripts/check_repository.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        [sys.executable, "scripts/prepare_release.py", "--tag", f"v{version}", "--notes-file", notes.name],
    ]
    try:
        for command in commands:
            result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
            if result.returncode:
                return result.returncode, command
    finally:
        Path(notes.name).unlink(missing_ok=True)
    return 0, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--bump", choices=("patch", "minor", "major"))
    choice.add_argument("--version")
    parser.add_argument("--date")
    parser.add_argument("--protocol-reviewed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        current = (root / "VERSION").read_text(encoding="utf-8").strip()
        current_key = version_key(current)
        if args.version:
            new_version = args.version
        else:
            major, minor, patch = current_key
            new_version = f"{major + 1}.0.0" if args.bump == "major" else (f"{major}.{minor + 1}.0" if args.bump == "minor" else f"{major}.{minor}.{patch + 1}")
        version_key(new_version)
        date = args.date or dt.date.today().isoformat()
        dt.date.fromisoformat(date)
        previous, body, kind, migrations, baseline, protocol = preflight(root, new_version)
        if protocol != previous.get("protocolVersion") and not args.protocol_reviewed:
            raise ReleaseError("BLOCKED: PROTOCOL_VERSION changed; use --protocol-reviewed only after CONTRIBUTING.md compatibility tests are added")
        if protocol == previous.get("protocolVersion"):
            print("Manifest comparison remains a manual check; this command does not perform it.")
        if args.dry_run:
            print(f"Dry run: {kind}; would write VERSION, .claude-plugin/plugin.json, releases/{new_version}.json, CHANGELOG.md")
            print(render_changelog((root / "CHANGELOG.md").read_text(encoding="utf-8"), new_version, kind, body))
            return 0
        paths = write_release(root, new_version, date, kind, migrations, baseline, protocol, body)
        status, command = validate(root, new_version)
        if status:
            restore(root, paths)
            print(f"validation failed: {' '.join(command)} exited {status}; release files restored", file=sys.stderr)
            return status
        commit = run_git(root, "add", "--", *(str(path.relative_to(root)) for path in paths))
        if commit.returncode:
            raise ReleaseError(f"could not stage release files: {commit.stderr.strip()}")
        commit = run_git(root, "commit", "-m", f"Release {new_version}")
        if commit.returncode:
            raise ReleaseError(f"could not create release commit: {commit.stderr.strip()}")
        print(
            f"Created {commit.stdout.strip()}\nDerived kind: {kind}\n"
            "Next: python3 scripts/release.py publish (Task 094)"
        )
        return 0
    except (ReleaseError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"release prepare failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
