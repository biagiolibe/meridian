#!/usr/bin/env python3
"""Verify release consistency for a version tag and render its release notes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseError(Exception):
    """A release precondition is not satisfied."""


def read_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def extract_changelog_section(changelog: str, version: str) -> str:
    """Return the body of the `## [<version>]` section, without its heading."""
    heading = re.compile(rf"^## \[{re.escape(version)}\](\s.*)?$")
    lines = changelog.splitlines()
    for index, line in enumerate(lines):
        if heading.match(line):
            start = index + 1
            break
    else:
        raise ReleaseError(f"CHANGELOG.md has no '## [{version}]' section")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    body = "\n".join(lines[start:end]).strip()
    if not body:
        raise ReleaseError(f"CHANGELOG.md section '## [{version}]' is empty")
    return body


def check_release_consistency(root: Path, tag: str) -> str:
    """Validate the tagged tree against the tag and return its version."""
    version = read_version(root)
    if tag != f"v{version}":
        raise ReleaseError(f"tag {tag!r} does not equal 'v' + VERSION ('v{version}')")
    record_path = root / "releases" / f"{version}.json"
    if not record_path.is_file():
        raise ReleaseError(f"releases/{version}.json is missing")
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ReleaseError(f"releases/{version}.json is invalid JSON: {error}") from error
    if record.get("gitTag") != tag:
        raise ReleaseError(
            f"releases/{version}.json gitTag {record.get('gitTag')!r} does not equal {tag!r}"
        )
    plugin = json.loads(
        (root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    if plugin.get("version") != version:
        raise ReleaseError(
            f".claude-plugin/plugin.json version {plugin.get('version')!r} "
            f"does not match VERSION {version!r}"
        )
    extract_changelog_section((root / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    return version


def render_release_notes(root: Path, tag: str, repository: str | None = None) -> str:
    version = check_release_consistency(root, tag)
    section = extract_changelog_section(
        (root / "CHANGELOG.md").read_text(encoding="utf-8"), version
    )
    record = f"releases/{version}.json"
    target = f"https://github.com/{repository}/blob/{tag}/{record}" if repository else record
    return f"{section}\n\nRelease record: [{record}]({target})\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="version tag, for example v1.2.3")
    parser.add_argument("--notes-file", type=Path, required=True, help="release body output")
    parser.add_argument("--repository", help="owner/name, used for the release record link")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        notes = render_release_notes(args.root, args.tag, args.repository)
    except ReleaseError as error:
        print(f"release check failed: {error}", file=sys.stderr)
        return 1
    args.notes_file.write_text(notes, encoding="utf-8")
    print(f"Release {args.tag} is consistent; notes written to {args.notes_file}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
