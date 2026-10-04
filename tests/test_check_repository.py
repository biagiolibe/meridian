"""Regression tests for the repository validation checks."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_repository as cr  # noqa: E402


class PluginVersionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / ".claude-plugin").mkdir()
        (self.root / "VERSION").write_text("1.2.3\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_plugin_version(self, version: str) -> None:
        manifest = {"name": "meridian", "version": version}
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def test_matching_plugin_version_passes(self) -> None:
        self.write_plugin_version("1.2.3")

        cr.check_plugin_version(self.root)

    def test_mismatched_plugin_version_names_both_values(self) -> None:
        self.write_plugin_version("1.2.2")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_plugin_version(self.root)

        self.assertIn("1.2.2", output.getvalue())
        self.assertIn("1.2.3", output.getvalue())


class CapabilityMarkerBaselineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "templates", self.root / "templates")
        shutil.copytree(ROOT / "migrations", self.root / "migrations")
        shutil.copytree(ROOT / "capabilities", self.root / "capabilities")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_committed_baseline_matches_the_repository_as_shipped(self) -> None:
        # No SystemExit means every recorded baseline matches the live templates.
        cr.check_capability_marker_baselines(self.root)

    def test_a_hand_edit_that_changes_marker_content_without_a_version_bump_fails(self) -> None:
        target = self.root / "templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "If any acceptance criterion cannot be evaluated",
                "If any acceptance criterion is an UNAUTHORIZED HAND EDIT",
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
        target = self.root / "templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "If any acceptance criterion cannot be evaluated",
                "If any acceptance criterion is an UNAUTHORIZED HAND EDIT",
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_write_marker_baselines_makes_a_deliberate_change_pass_again(self) -> None:
        target = self.root / "templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(
            text.replace(
                "If any acceptance criterion cannot be evaluated",
                "If any acceptance criterion is deliberately reworded",
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
        target = self.root / "templates/workflows/governed-sdd/AGENTS.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(
            "<!-- MERIDIAN:BEGIN capability=command-triggers v3 -->",
            "<!-- MERIDIAN:BEGIN capability=command-triggers v4 -->",
            1,
        )
        target.write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_missing_baseline_file_fails(self) -> None:
        (self.root / "migrations" / "marker-baselines" / "CAPABILITY_MARKER_BASELINES.json").unlink()
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_capability_catalog_is_valid_as_shipped(self) -> None:
        cr.check_capability_catalog(self.root)

    def test_capability_catalog_rejects_an_unresolved_dependency(self) -> None:
        path = self.root / "capabilities/catalog-v1.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["capabilities"]["read-guard"]["dependencies"][0]["version"] = 999
        path.write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(SystemExit):
            cr.check_capability_catalog(self.root)

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
        self._remove_marker_block(self.root / "templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md", "spike-routing", 1)
        with self.assertRaises(SystemExit):
            cr.check_capability_marker_baselines(self.root)

    def test_a_capability_removed_by_a_declared_migration_passes(self) -> None:
        """Task 007: `check_capability_marker_baselines` must reuse the same
        `removes` declaration `meridian upgrade` honors, not a second,
        independent notion of what a legitimate removal looks like."""
        self._remove_marker_block(self.root / "templates/workflows/governed-sdd/docs/workflows/IMPLEMENTATION.md", "spike-routing", 1)
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


class GovernedReviewWorktreeContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "templates", self.root / "templates")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_shipped_review_contract_passes(self) -> None:
        cr.check_governed_review_worktree_contract(self.root)

    def test_retired_primary_checkout_instruction_fails(self) -> None:
        review = (
            self.root
            / "templates/workflows/governed-sdd/docs/workflows/REVIEW.md"
        )
        review.write_text(
            review.read_text(encoding="utf-8")
            + "\nThe reviewer uses that same primary checkout.\n",
            encoding="utf-8",
        )
        with self.assertRaises(SystemExit):
            cr.check_governed_review_worktree_contract(self.root)

    def test_preflight_must_precede_substantive_review_boundary(self) -> None:
        review = (
            self.root
            / "templates/workflows/governed-sdd/docs/workflows/REVIEW.md"
        )
        text = review.read_text(encoding="utf-8")
        begin = "<!-- MERIDIAN:BEGIN capability=task-worktree-review-procedure v8 -->"
        boundary = "<!-- MERIDIAN:BEGIN capability=review-mode-boundary v1 -->"
        text = text.replace(begin, "TEMP-PREFLIGHT", 1)
        text = text.replace(boundary, begin, 1).replace("TEMP-PREFLIGHT", boundary, 1)
        review.write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            cr.check_governed_review_worktree_contract(self.root)


class CheckMigrationsVersionGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "templates", self.root / "templates")
        shutil.copytree(ROOT / "capabilities", self.root / "capabilities")
        (self.root / "migrations").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_chain(self, *steps: tuple[str, str], version: str) -> None:
        for index, (source, target) in enumerate(steps, start=1):
            migration_id = f"{index:03d}-step"
            (self.root / "migrations" / f"{migration_id}.json").write_text(
                json.dumps(
                    {
                        "id": migration_id,
                        "from": source,
                        "to": target,
                        "description": "test-only",
                        "managedPaths": ["AGENTS.md"],
                        "verification": ["test-only"],
                    }
                ),
                encoding="utf-8",
            )
        (self.root / "VERSION").write_text(f"{version}\n", encoding="utf-8")

    def run_check(self) -> str:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            cr.check_migrations(self.root)
        return output.getvalue()

    def test_version_equal_to_last_migration_passes(self) -> None:
        self.write_chain(("1.0.0", "1.0.1"), ("1.0.1", "1.0.2"), version="1.0.2")

        self.run_check()

    def test_version_ahead_of_last_migration_passes_for_cli_only_release(self) -> None:
        self.write_chain(("1.0.0", "1.0.1"), version="1.0.3")

        self.run_check()

    def test_version_compares_numerically_not_lexically(self) -> None:
        self.write_chain(("1.0.0", "1.0.9"), version="1.0.10")

        self.run_check()

    def test_last_migration_ahead_of_version_fails(self) -> None:
        self.write_chain(("1.0.0", "1.0.1"), ("1.0.1", "1.0.4"), version="1.0.3")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_migrations(self.root)

        self.assertIn("ahead of the current release", output.getvalue())

    def test_non_contiguous_migration_chain_still_fails(self) -> None:
        self.write_chain(("1.0.0", "1.0.1"), ("1.0.5", "1.0.6"), version="1.0.6")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_migrations(self.root)

        self.assertIn("not contiguous", output.getvalue())

    def test_malformed_adopt_existing_paths_declaration_fails(self) -> None:
        self.write_chain(("1.0.0", "1.0.1"), version="1.0.1")
        path = self.root / "migrations/001-step.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["adoptExistingPaths"] = "AGENTS.md"
        path.write_text(json.dumps(record), encoding="utf-8")
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_migrations(self.root)

        self.assertIn("adoptExistingPaths must be a list", output.getvalue())


class CheckReleasesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "migrations").mkdir()
        (self.root / "releases").mkdir()
        (self.root / "VERSION").write_text("1.0.2\n", encoding="utf-8")
        (self.root / "migrations" / "001-step.json").write_text(
            json.dumps({"id": "001-step", "from": "1.0.0", "to": "1.0.1"}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_release(self, version: str, filename: str | None = None, **overrides: object) -> None:
        record = {
            "version": version,
            "releaseDate": "2026-01-01",
            "gitTag": f"v{version}",
            "protocolVersion": 2,
            "workflowBaselineVersion": "1.0.1",
            "baselineChanged": False,
            "migrations": [],
        }
        record.update(overrides)
        (self.root / "releases" / f"{filename or version}.json").write_text(
            json.dumps(record), encoding="utf-8"
        )

    def assert_fails(self, message: str) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_releases(self.root)
        self.assertIn(message, output.getvalue())

    def test_valid_ledger_passes(self) -> None:
        self.write_release("1.0.1", baselineChanged=True, migrations=["001-step"])
        self.write_release("1.0.2")

        cr.check_releases(self.root)

    def test_numeric_ordering_passes(self) -> None:
        (self.root / "VERSION").write_text("1.0.10\n", encoding="utf-8")
        self.write_release("1.0.9")
        self.write_release("1.0.10")

        cr.check_releases(self.root)

    def test_missing_record_for_current_version_fails(self) -> None:
        self.write_release("1.0.1", baselineChanged=True, migrations=["001-step"])

        self.assert_fails("is missing for the current VERSION")

    def test_filename_version_mismatch_fails(self) -> None:
        self.write_release("1.0.1", filename="1.0.2")

        self.assert_fails("does not match the filename")

    def test_non_monotonic_versions_fail(self) -> None:
        self.write_release("1.0.2")
        self.write_release("1.0.02")

        self.assert_fails("monotonically increasing")

    def test_baseline_changed_inconsistent_with_migrations_fails(self) -> None:
        self.write_release("1.0.1", baselineChanged=False, migrations=["001-step"])
        self.write_release("1.0.2")

        self.assert_fails("baselineChanged")

    def test_prerelease_suffix_fails(self) -> None:
        (self.root / "VERSION").write_text("1.0.2-rc.1\n", encoding="utf-8")
        self.write_release("1.0.2-rc.1")

        self.assert_fails("prerelease or build suffix")

    def test_build_suffix_fails(self) -> None:
        (self.root / "VERSION").write_text("1.0.2+dev\n", encoding="utf-8")
        self.write_release("1.0.2+dev")

        self.assert_fails("prerelease or build suffix")

    def test_latest_baseline_mismatch_fails(self) -> None:
        self.write_release("1.0.2", workflowBaselineVersion="1.0.0")

        self.assert_fails("migration-derived baseline")


class MachinePathTest(unittest.TestCase):
    """The guard rejects home-directory paths in tracked text files."""

    # Built at runtime so this file does not contain a forbidden path itself.
    FORBIDDEN = {
        "macos": "/Us" + "ers/alice/dev/project",
        "linux": "/ho" + "me/alice/project",
        "windows": "C:\\Us" + "ers\\alice\\project",
    }

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def track(self, name: str, content: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        subprocess.run(["git", "-C", str(self.root), "add", name], check=True)

    def assert_fails(self, fragment: str, **kwargs: object) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_no_machine_paths(self.root, **kwargs)
        self.assertIn(fragment, output.getvalue())

    def test_clean_tree_passes(self) -> None:
        self.track("README.md", b"Use <checkout>/scripts and ../meridian-task-1.\n")
        self.track("docs/a.md", b"path `/Us" + b"ers/<name>/x` placeholder\n")
        self.track("image.bin", b"\xff\xfe" + self.FORBIDDEN["macos"].encode())

        cr.check_no_machine_paths(self.root)

    def test_each_forbidden_form_fails_naming_file_and_line(self) -> None:
        for label, value in self.FORBIDDEN.items():
            with self.subTest(label):
                self.track(f"docs/{label}.md", f"ok\nsee {value} here\n".encode())
                self.assert_fails(f"docs/{label}.md:2")
                subprocess.run(
                    ["git", "-C", str(self.root), "rm", "-q", "-f", f"docs/{label}.md"],
                    check=True,
                )

    def test_untracked_file_is_ignored(self) -> None:
        (self.root / "scratch.md").write_text(self.FORBIDDEN["macos"], encoding="utf-8")

        cr.check_no_machine_paths(self.root)

    def test_allowed_exception_passes_only_for_that_file(self) -> None:
        self.track("frozen.md", self.FORBIDDEN["linux"].encode())
        cr.check_no_machine_paths(self.root, allowed=frozenset({"frozen.md"}))

        self.track("other.md", self.FORBIDDEN["linux"].encode())
        self.assert_fails("other.md:1", allowed=frozenset({"frozen.md"}))

    def test_repository_has_no_machine_paths(self) -> None:
        cr.check_no_machine_paths()


class ManagedDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.target = self.root / "docs/CONTEXT_BUDGET_POLICY.md"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self) -> dict[str, object]:
        return json.loads((self.root / ".meridian/manifest.json").read_text(encoding="utf-8"))

    def write_manifest(self, manifest: dict[str, object]) -> None:
        (self.root / ".meridian/manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    def drift(self) -> None:
        self.target.write_text(self.target.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")

    def test_no_drift_passes_without_writing(self) -> None:
        before = (self.root / ".meridian/manifest.json").read_bytes()

        cr.check_managed_digests(self.root)

        self.assertEqual(before, (self.root / ".meridian/manifest.json").read_bytes())

    def test_drift_names_file_digests_and_refresh_command(self) -> None:
        self.drift()
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_managed_digests(self.root)

        message = output.getvalue()
        self.assertIn("docs/CONTEXT_BUDGET_POLICY.md", message)
        self.assertIn("expected", message)
        self.assertIn("got", message)
        self.assertIn("--write-managed-digests", message)

    def test_stale_digest_evidence_fails(self) -> None:
        manifest = self.manifest()
        profiles = manifest["capabilityProfiles"]
        assert isinstance(profiles, dict)
        capabilities = profiles["meridian-self-hosting"]["capabilities"]
        assert isinstance(capabilities, dict)
        installation = capabilities["context-budgeting"]["installation"]
        assert isinstance(installation, dict)
        installation["evidence"][0] = "sha256:" + "0" * 64
        self.write_manifest(manifest)
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.check_managed_digests(self.root)

        self.assertIn("stale digest evidence", output.getvalue())

    def test_refresh_fixes_drift_and_is_idempotent(self) -> None:
        self.drift()

        changes = cr.write_managed_digests(self.root)
        after_first_write = (self.root / ".meridian/manifest.json").read_bytes()
        cr.check_managed_digests(self.root)

        self.assertTrue(any("docs/CONTEXT_BUDGET_POLICY.md" in change for change in changes))
        self.assertEqual([], cr.write_managed_digests(self.root))
        self.assertEqual(after_first_write, (self.root / ".meridian/manifest.json").read_bytes())

    def test_refresh_refuses_a_missing_listed_file(self) -> None:
        self.target.unlink()
        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cr.write_managed_digests(self.root)

        self.assertIn("listed file is missing: docs/CONTEXT_BUDGET_POLICY.md", output.getvalue())

    def test_repository_check_and_profile_doctor_agree_on_drift(self) -> None:
        self.drift()
        check_output = io.StringIO()
        doctor_output = io.StringIO()
        with contextlib.redirect_stdout(check_output), self.assertRaises(SystemExit):
            cr.check_managed_digests(self.root)
        with contextlib.redirect_stdout(doctor_output):
            doctor_status = cr.meridian.profile_doctor(
                self.root, self.root, "meridian-self-hosting"
            )

        self.assertEqual(2, doctor_status, doctor_output.getvalue())
        expected = "drifted managed-copy surface docs/CONTEXT_BUDGET_POLICY.md"
        self.assertIn(expected, check_output.getvalue())
        self.assertIn(expected, doctor_output.getvalue())


if __name__ == "__main__":
    unittest.main()
