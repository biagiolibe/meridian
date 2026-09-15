"""Regression tests for `meridian adr show` and `meridian context authority`."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "meridian.py"

sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402

ADR_LOG = (
    "# Architecture Decision Log\n\n"
    "## ADR-0059 — Superseded thing\n"
    "**Status:** Superseded\n\n"
    "Old body.\n\n"
    "## ADR-0060 — Adjacent one\n"
    "**Status:** Accepted\n\n"
    "Body of 60.\n\n"
    "## ADR-0063 — Last one\n"
    "**Status:** Accepted\n\n"
    "Body of 63.\n"
)


class AuthorityExcerptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        (self.project / "tasks").mkdir(parents=True)
        (self.project / "docs").mkdir(parents=True)
        (self.project / "docs/ARCHITECTURE_DECISIONS.md").write_text(ADR_LOG, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_task(self, task_id: str, body: str) -> None:
        (self.project / "tasks" / f"{task_id}.md").write_text(body, encoding="utf-8")

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *arguments, "--project", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )

    # -- adr show -----------------------------------------------------

    def test_adr_show_splits_adjacent_headings(self) -> None:
        result = self.run_cli("adr", "show", "ADR-0060")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## ADR-0060 — Adjacent one", result.stdout)
        self.assertIn("Body of 60.", result.stdout)
        self.assertNotIn("ADR-0059", result.stdout)
        self.assertNotIn("ADR-0063", result.stdout)

    def test_adr_show_captures_the_last_entry_through_eof(self) -> None:
        result = self.run_cli("adr", "show", "ADR-0063")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## ADR-0063 — Last one", result.stdout)
        self.assertIn("Body of 63.", result.stdout)

    def test_adr_show_unknown_id_is_a_named_non_zero_error(self) -> None:
        result = self.run_cli("adr", "show", "ADR-9999")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("ADR-9999", result.stderr)
        self.assertIn("ARCHITECTURE_DECISIONS.md", result.stderr)

    def test_adr_show_resolves_a_non_default_adr_log_path(self) -> None:
        (self.project / "docs/DECISIONS.md").write_text(
            "## ADR-0001 — Custom log\nBody.\n", encoding="utf-8"
        )
        (self.project / "PROJECT_WORKFLOW.md").write_text(
            "<!-- MERIDIAN:BEGIN capability=execution-assets v1 -->\n<!-- MERIDIAN:END -->\n"
            "ADR log is `docs/DECISIONS.md`.\n\n## Roles\n",
            encoding="utf-8",
        )
        result = self.run_cli("adr", "show", "ADR-0001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Custom log", result.stdout)

    # -- context authority ---------------------------------------------

    def test_context_authority_resolves_multiple_adr_ids_in_one_bullet(self) -> None:
        self.write_task(
            "TASK-001",
            "Status: IN_PROGRESS\n\n## Authority\n\n"
            "- `docs/ARCHITECTURE_DECISIONS.md` — ADR-0060 and ADR-0063.\n\n"
            "## Expected code surface\n",
        )
        result = self.run_cli("context", "authority", "TASK-001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ADR-0060", result.stdout)
        self.assertIn("Body of 60.", result.stdout)
        self.assertIn("ADR-0063", result.stdout)
        self.assertIn("Body of 63.", result.stdout)
        self.assertNotIn("ADR-0059", result.stdout)

    def test_context_authority_resolves_a_spec_heading_citation(self) -> None:
        (self.project / "docs/specs").mkdir(parents=True)
        (self.project / "docs/specs/FOO.md").write_text(
            "# Foo\n\n## Target Section\n\nTarget body.\n\n## Other\n\nOther body.\n",
            encoding="utf-8",
        )
        self.write_task(
            "TASK-002",
            "Status: IN_PROGRESS\n\n## Authority\n\n"
            "- `docs/specs/FOO.md`#Target Section\n\n"
            "## Expected code surface\n",
        )
        result = self.run_cli("context", "authority", "TASK-002")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Target body.", result.stdout)
        self.assertNotIn("Other body.", result.stdout)

    def test_context_authority_names_an_unresolved_entry_without_failing(self) -> None:
        self.write_task(
            "TASK-003",
            "Status: IN_PROGRESS\n\n## Authority\n\n"
            "- `docs/specs/FOO.md` — accepted contract, no explicit heading cited.\n\n"
            "## Expected code surface\n",
        )
        result = self.run_cli("context", "authority", "TASK-003")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Unresolved", result.stdout)
        self.assertIn("docs/specs/FOO.md", result.stdout)

    def test_context_authority_names_an_unresolved_adr_id_without_failing(self) -> None:
        self.write_task(
            "TASK-004",
            "Status: IN_PROGRESS\n\n## Authority\n\n"
            "- `docs/ARCHITECTURE_DECISIONS.md` — ADR-9999.\n\n"
            "## Expected code surface\n",
        )
        result = self.run_cli("context", "authority", "TASK-004")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Unresolved", result.stdout)
        self.assertIn("ADR-9999", result.stdout)

    def test_context_authority_handles_a_task_with_no_authority_field(self) -> None:
        self.write_task("TASK-005", "Status: IN_PROGRESS\n\n## Expected code surface\n")
        result = self.run_cli("context", "authority", "TASK-005")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no Authority entries", result.stdout)

    def test_context_authority_labels_only_omits_excerpt_bodies(self) -> None:
        self.write_task(
            "TASK-006",
            "Status: IN_PROGRESS\n\n## Authority\n\n"
            "- `docs/ARCHITECTURE_DECISIONS.md` — ADR-0060.\n\n"
            "## Expected code surface\n",
        )
        result = self.run_cli("context", "authority", "TASK-006", "--labels-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ADR-0060", result.stdout)
        self.assertNotIn("Body of 60.", result.stdout)

    # -- shared heading extractor ---------------------------------------

    def test_extract_heading_block_direct(self) -> None:
        result = meridian.extract_heading_block(ADR_LOG, lambda title: title.startswith("ADR-0060"))
        self.assertIsNotNone(result)
        excerpt, title = result
        self.assertEqual(title, "ADR-0060 — Adjacent one")
        self.assertIn("Body of 60.", excerpt)
        self.assertNotIn("ADR-0063", excerpt)


if __name__ == "__main__":
    unittest.main()
