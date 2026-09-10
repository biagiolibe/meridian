"""Regression tests for the capability-marker-vs-version repository guard
added for task 014 (tasks/014-generator-altered-protected-blocks.md)."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_repository as cr  # noqa: E402


class CapabilityMarkerBaselineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "templates", self.root / "templates")
        shutil.copytree(ROOT / "migrations", self.root / "migrations")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_committed_baseline_matches_the_repository_as_shipped(self) -> None:
        # No SystemExit means every recorded baseline matches the live templates.
        cr.check_capability_marker_baselines(self.root)

    def test_a_hand_edit_that_changes_marker_content_without_a_version_bump_fails(self) -> None:
        target = self.root / "templates/workflows/governed-sdd/CLAUDE.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "Treat these developer phrases as the complete authorization",
                "Treat these developer phrases as the UNAUTHORIZED HAND EDIT",
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_a_hand_edit_to_agents_md_is_caught_too(self) -> None:
        """AGENTS.md is the single source of truth the generator copies from
        (task 004); an edit there is exactly as unauthorized as one in
        CLAUDE.md, and must not silently become the new v1 just because the
        generator will faithfully propagate it."""
        target = self.root / "templates/workflows/governed-sdd/AGENTS.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "Treat these developer phrases as the complete authorization",
                "Treat these developer phrases as the UNAUTHORIZED HAND EDIT",
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_write_marker_baselines_makes_a_deliberate_change_pass_again(self) -> None:
        target = self.root / "templates/workflows/governed-sdd/CLAUDE.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "Treat these developer phrases as the complete authorization",
                "Treat these developer phrases as the deliberately reworded authorization",
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)
        cr.write_marker_baselines(self.root)
        cr.check_capability_marker_baselines(self.root)

    def test_a_version_bump_without_regenerating_the_baseline_still_fails(self) -> None:
        """Bumping the version *and* changing the content is the legitimate
        path, but it still requires the explicit `--write-marker-baselines`
        step; skipping that must not silently pass."""
        target = self.root / "templates/workflows/governed-sdd/CLAUDE.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(
            "<!-- MERIDIAN:BEGIN capability=command-triggers v1 -->",
            "<!-- MERIDIAN:BEGIN capability=command-triggers v2 -->",
            1,
        )
        target.write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_missing_baseline_file_fails(self) -> None:
        (self.root / "migrations" / "marker-baselines" / "CAPABILITY_MARKER_BASELINES.json").unlink()
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def _remove_marker_block(self, target: Path, capability: str, version: int) -> None:
        import re

        text = target.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"<!-- MERIDIAN:BEGIN capability={capability} v{version} -->\n?.*?<!-- MERIDIAN:END -->\n?",
            re.DOTALL,
        )
        match = pattern.search(text)
        self.assertIsNotNone(match, f"capability={capability} v{version} not found in {target}")
        target.write_text(text[: match.start()] + text[match.end() :], encoding="utf-8")

    def test_a_capability_removed_without_a_removes_declaration_still_fails(self) -> None:
        """The baseline guard's original task-014 behavior: an absence with
        no accounting migration is still an unauthorized change, retirement
        infrastructure or not."""
        for name in ("AGENTS.md", "CLAUDE.md"):
            self._remove_marker_block(
                self.root / "templates/workflows/governed-sdd" / name, "spike-routing", 1
            )
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_a_capability_removed_by_a_declared_migration_passes(self) -> None:
        """Task 007: `check_capability_marker_baselines` must reuse the same
        `removes` declaration `meridian upgrade` honors, not a second,
        independent notion of what a legitimate removal looks like."""
        for name in ("AGENTS.md", "CLAUDE.md"):
            self._remove_marker_block(
                self.root / "templates/workflows/governed-sdd" / name, "spike-routing", 1
            )
        (self.root / "migrations" / "999-retire-spike-routing.json").write_text(
            '{"id": "999-retire-spike-routing", "from": "1.1.20", "to": "1.1.21", '
            '"description": "test-only", "removes": '
            '[{"capability": "spike-routing", "capabilityVersion": 1}], '
            '"managedPaths": ["AGENTS.md", "CLAUDE.md"], "verification": ["test-only"]}',
            encoding="utf-8",
        )
        # No SystemExit: the recorded baseline's spike-routing entry is
        # stale relative to the live templates, but its absence is explained.
        cr.check_capability_marker_baselines(self.root)


if __name__ == "__main__":
    unittest.main()
