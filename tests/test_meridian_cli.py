"""Regression tests for the deterministic framework-upgrade CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "meridian.py"
MARKER_BEGIN = re.compile(r"<!-- MERIDIAN:BEGIN capability=([a-z0-9-]+) v(\d+) -->")
MARKER_END = "<!-- MERIDIAN:END -->"

sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402


class MeridianCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.framework = root / "framework"
        self.project = root / "project"
        shutil.copytree(ROOT / "templates", self.framework / "templates")
        shutil.copytree(ROOT / "migrations", self.framework / "migrations")
        shutil.copytree(ROOT / "release-baselines", self.framework / "release-baselines")
        (self.framework / "VERSION").write_text("1.1.0\n", encoding="utf-8")
        self.project.mkdir()
        self.copy_governed_templates()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def copy_governed_templates(self) -> None:
        source = self.framework / "templates" / "workflows" / "governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--framework-root",
                str(self.framework),
                *arguments,
                "--project",
                str(self.project),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_lock_and_apply_clean_template_upgrade(self) -> None:
        locked = self.run_cli("lock", "--mode", "governed-sdd")
        self.assertEqual(locked.returncode, 0, locked.stderr)

        workflow = self.framework / "templates/workflows/governed-sdd/PROJECT_WORKFLOW.md"
        workflow.write_text(workflow.read_text(encoding="utf-8") + "\nUpgrade marker.\n", encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("REPLACE  PROJECT_WORKFLOW.md", checked.stdout)

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn("Upgrade marker.", (self.project / "PROJECT_WORKFLOW.md").read_text(encoding="utf-8"))
        manifest = json.loads((self.project / ".meridian/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frameworkVersion"], "1.1.1")
        self.assertEqual(
            manifest["appliedMigrations"],
            [
                "001-review-remediation-record",
                "002-lifecycle-orchestration",
                "003-framework-updater",
                "004-validation-scoping",
            ],
        )
        baselines = sorted(path.name for path in (self.project / ".meridian/baselines").iterdir())
        self.assertEqual(baselines, ["1.1.1"], "stale 1.1.0 baseline should be pruned after upgrade")

        workflow.write_text(workflow.read_text(encoding="utf-8") + "\nSecond upgrade marker.\n", encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.2\n", encoding="utf-8")
        second_apply = self.run_cli("upgrade", "--apply")
        self.assertEqual(second_apply.returncode, 0, second_apply.stderr)
        baselines_after_second = sorted(
            path.name for path in (self.project / ".meridian/baselines").iterdir()
        )
        self.assertEqual(
            baselines_after_second,
            ["1.1.2"],
            "only the current frameworkVersion's baseline should remain after a second upgrade",
        )

    def test_upgrade_downgrades_cosmetic_conflict_to_verified(self) -> None:
        """Phase 3 of migrations/CAPABILITY_MARKERS.md: a conflict outside a
        satisfied capability marker is cosmetic and should be left untouched,
        not treated the same as a real, unverifiable conflict."""
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        agents = self.framework / "templates/workflows/governed-sdd/AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8").replace("## Code organization", "## Code Organization Rules"),
            encoding="utf-8",
        )
        local = self.project / "AGENTS.md"
        local_text = local.read_text(encoding="utf-8")
        self.assertIn("MERIDIAN:BEGIN capability=review-remediation-record", local_text)
        local.write_text(
            local_text.replace("## Code organization", "## Our Code Organization"), encoding="utf-8"
        )
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("VERIFIED AGENTS.md", checked.stdout)
        self.assertIn("capability marker(s)", checked.stdout)

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn(
            "## Our Code Organization",
            (self.project / "AGENTS.md").read_text(encoding="utf-8"),
            "a verified (cosmetic-only) conflict must leave the local file untouched",
        )

    def test_apply_refuses_conflicting_local_change(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        workflow = self.framework / "templates/workflows/governed-sdd/PROJECT_WORKFLOW.md"
        workflow.write_text(workflow.read_text(encoding="utf-8").replace("## Roles", "## Updated Roles"), encoding="utf-8")
        local = self.project / "PROJECT_WORKFLOW.md"
        local.write_text(local.read_text(encoding="utf-8").replace("## Roles", "## Local Roles"), encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 2)
        self.assertIn("BLOCKED", applied.stderr)
        self.assertIn("## Local Roles", local.read_text(encoding="utf-8"))

    def test_owner_reconciled_upgrade_registers_baseline_despite_conflicts(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        workflow = self.framework / "templates/workflows/governed-sdd/PROJECT_WORKFLOW.md"
        workflow.write_text(workflow.read_text(encoding="utf-8").replace("## Roles", "## Updated Roles"), encoding="utf-8")
        local = self.project / "PROJECT_WORKFLOW.md"
        local.write_text(local.read_text(encoding="utf-8").replace("## Roles", "## Local Roles"), encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        rejected = self.run_cli("upgrade", "--check", "--owner-reconciled")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("only applies to --apply", rejected.stderr)

        applied = self.run_cli("upgrade", "--apply", "--owner-reconciled")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn("Owner-reconciled upgrade", applied.stdout)
        self.assertIn("## Local Roles", local.read_text(encoding="utf-8"))
        manifest = json.loads((self.project / ".meridian/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frameworkVersion"], "1.1.1")
        baselines = sorted(path.name for path in (self.project / ".meridian/baselines").iterdir())
        self.assertEqual(baselines, ["1.1.1"])
        baseline_workflow = self.project / ".meridian/baselines/1.1.1/PROJECT_WORKFLOW.md"
        self.assertIn("## Updated Roles", baseline_workflow.read_text(encoding="utf-8"))

    def test_check_reports_multiple_merge_conflicts(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        workflow = self.framework / "templates/workflows/governed-sdd/PROJECT_WORKFLOW.md"
        workflow.write_text(
            workflow.read_text(encoding="utf-8")
            .replace("## Roles", "## Updated Roles")
            .replace("## Git workflow", "## Updated Git workflow"),
            encoding="utf-8",
        )
        local = self.project / "PROJECT_WORKFLOW.md"
        local.write_text(
            local.read_text(encoding="utf-8")
            .replace("## Roles", "## Local Roles")
            .replace("## Git workflow", "## Local Git workflow"),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 2)
        self.assertIn("CONFLICT PROJECT_WORKFLOW.md", checked.stdout)
        self.assertIn("BLOCKED: 1 conflict(s)", checked.stdout)

    def test_adopt_applies_packaged_legacy_migrations(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)

        checked = self.run_cli("adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("MIGRATION 001-review-remediation-record", checked.stdout)
        self.assertIn("MIGRATION 002-lifecycle-orchestration", checked.stdout)
        self.assertFalse((self.project / ".meridian").exists())

        applied = self.run_cli("adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue((self.project / "docs/REVIEW_RECORD_TEMPLATE.md").is_file())
        self.assertTrue((self.project / "docs/LIFECYCLE_ORCHESTRATION.md").is_file())
        manifest = json.loads((self.project / ".meridian/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["frameworkVersion"], "1.1.0")
        baselines = sorted(path.name for path in (self.project / ".meridian/baselines").iterdir())
        self.assertEqual(
            baselines,
            ["1.1.0"],
            "the intermediate 1.0.0 adoption baseline should be pruned once the target baseline lands",
        )

    def test_pre_marker_project_is_not_regressed_to_missing(self) -> None:
        """A project adopted before migration 006 has no MERIDIAN markers at all,
        only the old bare trigger phrases and template files. It must still be
        detected as PRESENT via the legacy fallback — not regressed to MISSING
        just because markers now exist for other, newer projects."""
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        # Simulate a pre-006 adoption: bare trigger phrases and template files,
        # with no MERIDIAN:BEGIN marker anywhere (unlike the 1.0.0 baseline
        # itself, which has neither the phrases nor the files).
        (self.project / "docs/REVIEW_RECORD_TEMPLATE.md").write_text(
            "# Review Record\n\nNo marker here, just the pre-006 shape.\n", encoding="utf-8"
        )
        (self.project / "docs/LIFECYCLE_ORCHESTRATION.md").write_text(
            "# Autonomous Task Lifecycle Orchestration\n\nNo marker here either.\n", encoding="utf-8"
        )
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.project / name
            target.write_text(
                target.read_text(encoding="utf-8") + "\nAddress review <TASK-ID>.\nRun lifecycle <TASK-ID>.\n",
                encoding="utf-8",
            )

        planned = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        # Both capabilities are present, but with no prior review record this
        # correctly asks for one before finalizing (compute_adoption_state's
        # existing REVIEW_MIGRATION path) rather than failing detection.
        self.assertEqual(planned.returncode, 3, planned.stdout)
        self.assertIn(
            "CAPABILITY PRESENT 001-review-remediation-record — no marker found; legacy pre-marker evidence confirms v1",
            planned.stdout,
        )
        self.assertIn(
            "CAPABILITY PRESENT 002-lifecycle-orchestration — no marker found; legacy pre-marker evidence confirms v1",
            planned.stdout,
        )
        self.assertIn("NEXT_ACTION REVIEW_MIGRATION", planned.stdout)

    def test_assisted_adoption_detects_only_missing_lifecycle(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        current = self.framework / "templates/workflows/governed-sdd"
        shutil.copyfile(current / "docs/REVIEW_RECORD_TEMPLATE.md", self.project / "docs/REVIEW_RECORD_TEMPLATE.md")
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.project / name
            target.write_text(target.read_text(encoding="utf-8") + "\nAddress review <TASK-ID>.\n", encoding="utf-8")

        planned = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(planned.returncode, 3)
        self.assertIn("CAPABILITY PRESENT 001-review-remediation-record", planned.stdout)
        self.assertIn("CAPABILITY MISSING 002-lifecycle-orchestration", planned.stdout)
        self.assertIn("AGENT_REQUIRED", planned.stdout)
        self.assertIn("NEXT_ACTION IMPLEMENT_MIGRATION", planned.stdout)
        self.assertIn("IMPLEMENTER_PROMPT_BEGIN", planned.stdout)
        self.assertIn("REVIEWER_PROMPT_BEGIN", planned.stdout)
        self.assertIn("This reviewer session must be fresh", planned.stdout)
        self.assertIn("ORCHESTRATOR_PROMPT_BEGIN", planned.stdout)
        self.assertIn("adoption-review.md", planned.stdout)
        self.assertIn("002-lifecycle-orchestration", planned.stdout)
        self.assertIn("migrations/002-lifecycle-orchestration.json", planned.stdout)
        self.assertIn("/bin/meridian finalize-adoption", planned.stdout)
        self.assertFalse((self.project / ".meridian").exists())

        shutil.copyfile(current / "docs/LIFECYCLE_ORCHESTRATION.md", self.project / "docs/LIFECYCLE_ORCHESTRATION.md")
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.project / name
            target.write_text(target.read_text(encoding="utf-8") + "\nRun lifecycle <TASK-ID>.\n", encoding="utf-8")

        # All capabilities are now present, but nothing has been reviewed yet:
        # finalize must refuse, and the plan must ask for an independent review.
        refused = self.run_cli("finalize-adoption", "--mode", "governed-sdd")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("no independent review record found", refused.stderr)

        reviewing = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(reviewing.returncode, 3)
        self.assertIn("NEXT_ACTION REVIEW_MIGRATION", reviewing.stdout)
        self.assertNotIn("Perform the capability-aware Meridian adoption migration", reviewing.stdout)
        self.assertIn("REVIEWER_PROMPT_BEGIN", reviewing.stdout)

        review_path = self.project / ".meridian/adoption-review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            "# Adoption Review\n\nVerdict: APPROVE\nAttempt: 1\n\n## Findings\n",
            encoding="utf-8",
        )

        ready = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(ready.returncode, 0)
        self.assertIn("NEXT_ACTION FINALIZE", ready.stdout)

        finalized = self.run_cli("finalize-adoption", "--mode", "governed-sdd")
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        self.assertTrue((self.project / ".meridian/manifest.json").is_file())

    def test_address_review_and_retry_limit(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)

        review_path = self.project / ".meridian/adoption-review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(
            "Verdict: CHANGES_REQUESTED\nAttempt: 1\n\n- [ ] add lifecycle orchestration\n",
            encoding="utf-8",
        )

        planned = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(planned.returncode, 3)
        self.assertIn("NEXT_ACTION ADDRESS_REVIEW", planned.stdout)
        self.assertIn("ATTEMPT 1", planned.stdout)

        review_path.write_text(
            "Verdict: CHANGES_REQUESTED\nAttempt: 2\n\n- [ ] still missing lifecycle orchestration\n",
            encoding="utf-8",
        )
        blocked = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("two consecutive CHANGES_REQUESTED verdicts", blocked.stderr)

    def test_emit_returns_single_prompt_block(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)

        emitted = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check",
            "--emit", "implementer",
        )
        self.assertEqual(emitted.returncode, 3)
        self.assertNotIn("IMPLEMENTER_PROMPT_BEGIN", emitted.stdout)
        self.assertIn("Perform the capability-aware Meridian adoption migration", emitted.stdout)

        rejected = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check",
            "--emit", "reviewer",
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("no reviewer prompt applies", rejected.stderr)

    def test_assisted_adoption_refuses_lean_delivery(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        planned = self.run_cli(
            "adopt", "--mode", "lean-delivery", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(planned.returncode, 2)
        self.assertIn("tracks capabilities only for governed-sdd", planned.stderr)

    def test_finalize_owner_accepted_bypasses_review_gate(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        current = self.framework / "templates" / "workflows" / "governed-sdd"
        for name in ("docs/REVIEW_RECORD_TEMPLATE.md", "docs/LIFECYCLE_ORCHESTRATION.md"):
            shutil.copyfile(current / name, self.project / name)
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.project / name
            target.write_text(
                target.read_text(encoding="utf-8") + "\nAddress review <TASK-ID>.\nRun lifecycle <TASK-ID>.\n",
                encoding="utf-8",
            )

        refused = self.run_cli("finalize-adoption", "--mode", "governed-sdd")
        self.assertEqual(refused.returncode, 2)

        accepted = self.run_cli("finalize-adoption", "--mode", "governed-sdd", "--owner-accepted")
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertIn("Owner-accepted finalize", accepted.stdout)
        self.assertTrue((self.project / ".meridian/manifest.json").is_file())

    def test_mode_and_version_autodetect(self) -> None:
        shutil.rmtree(self.project)
        self.project.mkdir()
        source = self.framework / "release-baselines/1.0.0/templates/workflows/governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = self.project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)

        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--framework-root",
                str(self.framework),
                "adopt",
                "--assisted",
                "--check",
                "--project",
                str(self.project),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("Assisted adoption 1.0.0 ->", result.stdout)


class CapabilityMarkerTest(unittest.TestCase):
    """Phase 1 of migrations/CAPABILITY_MARKERS.md: markers exist and are well-formed.

    No detection or verification code reads these yet (that's phase 2+); this
    only guards the markers themselves against silent drift or malformed
    nesting as the templates keep changing.
    """

    WORKFLOW = ROOT / "templates" / "workflows" / "governed-sdd"

    def marker_pairs(self, text: str) -> list[tuple[str, str]]:
        begins = MARKER_BEGIN.findall(text)
        end_count = text.count(MARKER_END)
        self.assertEqual(
            len(begins), end_count, "mismatched MERIDIAN:BEGIN/END marker count"
        )
        return begins

    def test_agents_and_claude_carry_both_v1_markers(self) -> None:
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.WORKFLOW / name).read_text(encoding="utf-8")
            pairs = self.marker_pairs(text)
            self.assertIn(("review-remediation-record", "1"), pairs, name)
            self.assertIn(("lifecycle-orchestration", "1"), pairs, name)

    def test_review_record_template_carries_its_own_marker(self) -> None:
        text = (self.WORKFLOW / "docs/REVIEW_RECORD_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertEqual(self.marker_pairs(text), [("review-remediation-record", "1")])

    def test_lifecycle_orchestration_carries_its_own_marker(self) -> None:
        text = (self.WORKFLOW / "docs/LIFECYCLE_ORCHESTRATION.md").read_text(encoding="utf-8")
        self.assertEqual(self.marker_pairs(text), [("lifecycle-orchestration", "1")])


class CapabilityVersionDetectionTest(unittest.TestCase):
    """Phase 2 of migrations/CAPABILITY_MARKERS.md: version-aware detection.

    No real migration requires v2 of anything yet, so this builds a synthetic
    framework with one to exercise the case Meridian's own shipped migrations
    can't: a marker present but below the version now required.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.framework = root / "framework"
        self.project = root / "project"
        (self.framework / "migrations").mkdir(parents=True)
        self.project.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_migration(self, filename: str, capability: str, version: int) -> None:
        migration_id = filename.removesuffix(".json")
        (self.framework / "migrations" / filename).write_text(
            json.dumps({"id": migration_id, "capability": capability, "capabilityVersion": version}),
            encoding="utf-8",
        )

    def test_requirement_is_the_highest_declared_version(self) -> None:
        self.write_migration("001-widget.json", "widget", 1)
        self.write_migration("002-widget-v2.json", "widget", 2)
        requirements = meridian.capability_requirements(self.framework)
        self.assertEqual(requirements["widget"], (2, "002-widget-v2"))

    def test_marker_absent_is_distinct_from_marker_stale(self) -> None:
        self.write_migration("001-widget.json", "widget", 2)

        absent = meridian.find_capability_marker_version("no marker here", "widget")
        self.assertIsNone(absent)

        stale_text = "<!-- MERIDIAN:BEGIN capability=widget v1 -->text<!-- MERIDIAN:END -->"
        self.assertEqual(meridian.find_capability_marker_version(stale_text, "widget"), 1)

    def test_detect_capabilities_distinguishes_absent_stale_and_satisfied(self) -> None:
        self.write_migration("001-widget.json", "widget", 2)
        agents = self.project / "AGENTS.md"
        claude = self.project / "CLAUDE.md"
        for path in (agents, claude):
            path.write_text("", encoding="utf-8")

        import meridian as m

        managed = [m.ManagedFile(source=Path("unused"), target=Path("AGENTS.md"))]
        original_managed_files = m.managed_files
        m.managed_files = lambda framework_root, mode: managed
        try:
            absent = m.detect_capabilities(self.project, "governed-sdd", self.framework)
            self.assertEqual(len(absent), 1)
            self.assertFalse(absent[0].present)
            self.assertIn("no MERIDIAN:BEGIN", absent[0].evidence)

            agents.write_text(
                "<!-- MERIDIAN:BEGIN capability=widget v1 -->text<!-- MERIDIAN:END -->",
                encoding="utf-8",
            )
            stale = m.detect_capabilities(self.project, "governed-sdd", self.framework)
            self.assertFalse(stale[0].present)
            self.assertEqual(stale[0].evidence, "marker present at v1, but v2 is required")

            agents.write_text(
                "<!-- MERIDIAN:BEGIN capability=widget v2 -->text<!-- MERIDIAN:END -->",
                encoding="utf-8",
            )
            satisfied = m.detect_capabilities(self.project, "governed-sdd", self.framework)
            self.assertTrue(satisfied[0].present)
        finally:
            m.managed_files = original_managed_files


if __name__ == "__main__":
    unittest.main()
