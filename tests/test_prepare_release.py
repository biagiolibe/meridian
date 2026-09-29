"""Tests for the release-preparation script."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_release as pr  # noqa: E402


CHANGELOG = """# Changelog

## [1.2.3]

Body of the newest release.

### Fixed

- Something.

## [1.2.2]

Older body.
"""


class ExtractChangelogSectionTest(unittest.TestCase):
    def test_returns_only_the_requested_section(self) -> None:
        section = pr.extract_changelog_section(CHANGELOG, "1.2.3")
        self.assertTrue(section.startswith("Body of the newest release."))
        self.assertIn("### Fixed", section)
        self.assertNotIn("Older body", section)

    def test_last_section_runs_to_end_of_file(self) -> None:
        self.assertEqual(pr.extract_changelog_section(CHANGELOG, "1.2.2"), "Older body.")

    def test_version_is_matched_exactly(self) -> None:
        with self.assertRaises(pr.ReleaseError):
            pr.extract_changelog_section(CHANGELOG, "1.2")

    def test_missing_or_empty_section_fails(self) -> None:
        with self.assertRaises(pr.ReleaseError):
            pr.extract_changelog_section(CHANGELOG, "9.9.9")
        with self.assertRaises(pr.ReleaseError):
            pr.extract_changelog_section("## [1.0.0]\n\n## [0.9.0]\nx\n", "1.0.0")


class ReleaseConsistencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "releases").mkdir()
        (self.root / ".claude-plugin").mkdir()
        (self.root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
        self.write_record({"version": "1.2.3", "gitTag": "v1.2.3"})
        self.write_plugin("1.2.3")

    def write_record(self, data: dict) -> None:
        (self.root / "releases" / "1.2.3.json").write_text(json.dumps(data), encoding="utf-8")

    def write_plugin(self, version: str) -> None:
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )

    def test_consistent_tree_passes(self) -> None:
        self.assertEqual(pr.check_release_consistency(self.root, "v1.2.3"), "1.2.3")

    def test_tag_must_equal_v_plus_version(self) -> None:
        with self.assertRaisesRegex(pr.ReleaseError, "does not equal"):
            pr.check_release_consistency(self.root, "v1.2.4")

    def test_release_record_is_required(self) -> None:
        (self.root / "releases" / "1.2.3.json").unlink()
        with self.assertRaisesRegex(pr.ReleaseError, "missing"):
            pr.check_release_consistency(self.root, "v1.2.3")

    def test_record_git_tag_must_match(self) -> None:
        self.write_record({"version": "1.2.3", "gitTag": "v9.9.9"})
        with self.assertRaisesRegex(pr.ReleaseError, "gitTag"):
            pr.check_release_consistency(self.root, "v1.2.3")

    def test_plugin_version_must_match(self) -> None:
        self.write_plugin("1.2.2")
        with self.assertRaisesRegex(pr.ReleaseError, "plugin.json"):
            pr.check_release_consistency(self.root, "v1.2.3")

    def test_changelog_section_is_required(self) -> None:
        (self.root / "CHANGELOG.md").write_text("## [1.2.2]\nx\n", encoding="utf-8")
        with self.assertRaisesRegex(pr.ReleaseError, "no '## \\[1.2.3\\]'"):
            pr.check_release_consistency(self.root, "v1.2.3")

    def test_notes_link_the_release_record(self) -> None:
        notes = pr.render_release_notes(self.root, "v1.2.3", "owner/repo")
        self.assertIn("Body of the newest release.", notes)
        self.assertIn(
            "https://github.com/owner/repo/blob/v1.2.3/releases/1.2.3.json", notes
        )

    def test_main_writes_notes_and_reports_failure(self) -> None:
        output = self.root / "notes.md"
        args = ["--root", str(self.root), "--notes-file", str(output)]
        self.assertEqual(pr.main(["--tag", "v1.2.3", *args]), 0)
        self.assertIn("Release record:", output.read_text(encoding="utf-8"))
        self.assertEqual(pr.main(["--tag", "v0.0.1", *args]), 1)


if __name__ == "__main__":
    unittest.main()
