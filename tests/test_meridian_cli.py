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

    def test_upgrade_appends_new_marker_when_existing_marker_was_moved(self) -> None:
        """A new protected capability must not conflict solely because a project
        relocated an unchanged older protected block."""
        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        profile = self.framework / "templates/workflows/governed-sdd/docs/EXECUTION_EVIDENCE_PROFILE.md"
        incoming_policy = policy.read_text(encoding="utf-8")
        marker = re.search(
            r"<!-- MERIDIAN:BEGIN capability=execution-evidence-profile v3 -->\n?.*?"
            r"<!-- MERIDIAN:END -->\n?",
            incoming_policy,
            re.DOTALL,
        )
        self.assertIsNotNone(marker)
        policy.write_text(incoming_policy[: marker.start()] + incoming_policy[marker.end() :], encoding="utf-8")
        profile.unlink()
        (self.framework / "VERSION").write_text("1.1.14\n", encoding="utf-8")
        shutil.rmtree(self.project)
        self.project.mkdir()
        self.copy_governed_templates()
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)

        local_policy = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        local_text = local_policy.read_text(encoding="utf-8")
        validation = re.search(
            r"<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->\n?.*?"
            r"<!-- MERIDIAN:END -->\n?",
            local_text,
            re.DOTALL,
        )
        self.assertIsNotNone(validation)
        moved_validation = validation.group(0)
        local_text = (
            local_text[: validation.start()]
            + "Project-local validation procedure remains at this location.\n"
            + local_text[validation.end() :]
        )
        local_policy.write_text(
            local_text.rstrip() + "\n\n## Project validation baseline\n\n" + moved_validation,
            encoding="utf-8",
        )

        policy.write_text(incoming_policy, encoding="utf-8")
        profile.write_text("# Project Execution Evidence Profile\n", encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.15\n", encoding="utf-8")

        appended = meridian.append_only_new_markers(
            local_policy.read_text(encoding="utf-8"),
            (self.project / ".meridian/baselines/1.1.14/docs/CONTEXT_BUDGET_POLICY.md").read_text(
                encoding="utf-8"
            ),
            incoming_policy,
        )
        self.assertIsNotNone(appended)
        self.assertIn("## Project validation baseline", appended)
        self.assertIn("capability=execution-evidence-profile v3", appended)

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("MERGE    docs/CONTEXT_BUDGET_POLICY.md", checked.stdout)

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        upgraded = local_policy.read_text(encoding="utf-8")
        self.assertIn("## Project validation baseline", upgraded)
        self.assertIn("capability=validation-scoping v1", upgraded)
        self.assertIn("capability=execution-evidence-profile v3", upgraded)
        self.assertTrue((self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md").is_file())

    def test_upgrade_does_not_require_a_capability_not_marked_in_this_file(self) -> None:
        """A migration's `managedPaths` lists every file its diff touches, which
        is not the same as every file that must carry its capability marker:
        migration 002 lists `docs/CONTEXT_BUDGET_POLICY.md` because it mentions
        lifecycle orchestration in prose, but only `validation-scoping` is
        actually marked in that file's template. The per-file cosmetic-conflict
        check must derive required capabilities from the template's own marker
        set, not from `managedPaths`, or this file can never be verified."""
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        policy.write_text(
            policy.read_text(encoding="utf-8").replace("## Task-first loading", "## Task-First Loading Rules"),
            encoding="utf-8",
        )
        local = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        local_text = local.read_text(encoding="utf-8")
        self.assertIn("MERIDIAN:BEGIN capability=validation-scoping", local_text)
        local.write_text(
            local_text.replace("## Task-first loading", "## Our Task-First Loading"), encoding="utf-8"
        )
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("VERIFIED docs/CONTEXT_BUDGET_POLICY.md", checked.stdout)

    def test_upgrade_retires_a_capability_from_a_conflicting_file(self) -> None:
        """Task 007: a migration's `removes` entry deletes a retired capability's
        block during `upgrade`, even when the file also has an unrelated local
        customization that blocks a clean three-way merge -- the retirement
        mirror of `test_upgrade_appends_new_marker_when_existing_marker_was_moved`.
        """
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)

        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        incoming_policy = policy.read_text(encoding="utf-8")
        marker = re.search(
            r"<!-- MERIDIAN:BEGIN capability=minimal-read-only-status v1 -->\n?.*?"
            r"<!-- MERIDIAN:END -->\n?",
            incoming_policy,
            re.DOTALL,
        )
        self.assertIsNotNone(marker)
        incoming_policy = incoming_policy[: marker.start()] + incoming_policy[marker.end() :]
        # An unrelated framework-side edit, on the same line a local
        # customization below also touches, so the three-way merge cannot
        # auto-resolve and the file falls through to the retirement fallback.
        incoming_policy = incoming_policy.replace(
            "## Task-first loading", "## Task-First Loading (framework wording)"
        )
        policy.write_text(incoming_policy, encoding="utf-8")

        (self.framework / "migrations/999-retire-minimal-read-only-status.json").write_text(
            json.dumps(
                {
                    "id": "999-retire-minimal-read-only-status",
                    "from": "1.1.0",
                    "to": "1.1.1",
                    "description": "test-only retirement",
                    "removes": [
                        {
                            "capability": "minimal-read-only-status",
                            "capabilityVersion": 1,
                            "supersededBy": "role-scoped-agent-rules",
                        }
                    ],
                    "managedPaths": ["docs/CONTEXT_BUDGET_POLICY.md"],
                    "verification": ["test-only"],
                }
            ),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        local_policy = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        local_text = local_policy.read_text(encoding="utf-8")
        self.assertIn("MERIDIAN:BEGIN capability=minimal-read-only-status v1", local_text)
        local_policy.write_text(
            local_text.replace("## Task-first loading", "## Task-First Loading (project wording)"),
            encoding="utf-8",
        )

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("RETIRE-MARKERS docs/CONTEXT_BUDGET_POLICY.md", checked.stdout)

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        upgraded = local_policy.read_text(encoding="utf-8")
        self.assertNotIn("capability=minimal-read-only-status", upgraded)
        self.assertNotIn("A status report is not a conformance audit.", upgraded)
        # The unrelated local customization survives untouched.
        self.assertIn("## Task-First Loading (project wording)", upgraded)
        # Every other still-required capability in this file is untouched.
        self.assertIn("capability=validation-scoping v1", upgraded)
        self.assertIn("capability=evidence-tiers v1", upgraded)

        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertNotIn("minimal-read-only-status", audited.stdout)

    def test_upgrade_refuses_to_retire_a_locally_modified_block(self) -> None:
        """The same retirement, but the local copy of the retired block itself
        was edited -- must fall through to a blocking conflict rather than
        silently discard the customization along with the block."""
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)

        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        incoming_policy = policy.read_text(encoding="utf-8")
        marker = re.search(
            r"<!-- MERIDIAN:BEGIN capability=minimal-read-only-status v1 -->\n?.*?"
            r"<!-- MERIDIAN:END -->\n?",
            incoming_policy,
            re.DOTALL,
        )
        self.assertIsNotNone(marker)
        incoming_policy = incoming_policy[: marker.start()] + incoming_policy[marker.end() :]
        incoming_policy = incoming_policy.replace(
            "## Task-first loading", "## Task-First Loading (framework wording)"
        )
        policy.write_text(incoming_policy, encoding="utf-8")

        (self.framework / "migrations/999-retire-minimal-read-only-status.json").write_text(
            json.dumps(
                {
                    "id": "999-retire-minimal-read-only-status",
                    "from": "1.1.0",
                    "to": "1.1.1",
                    "description": "test-only retirement",
                    "removes": [{"capability": "minimal-read-only-status", "capabilityVersion": 1}],
                    "managedPaths": ["docs/CONTEXT_BUDGET_POLICY.md"],
                    "verification": ["test-only"],
                }
            ),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        local_policy = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        local_text = local_policy.read_text(encoding="utf-8")
        local_text = local_text.replace("## Task-first loading", "## Task-First Loading (project wording)")
        # Edit inside the very block that is about to be retired.
        local_text = local_text.replace(
            "A status report is not a conformance audit.",
            "A status report is not a conformance audit, locally customized.",
        )
        local_policy.write_text(local_text, encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 2, checked.stdout + checked.stderr)
        self.assertIn("CONFLICT docs/CONTEXT_BUDGET_POLICY.md", checked.stdout)
        self.assertIn("BLOCKED", checked.stdout)

    def _reinsert_role_scoped_agent_rules_block(self, text: str) -> str:
        block = (
            "<!-- MERIDIAN:BEGIN capability=role-scoped-agent-rules v1 -->\n"
            "## Role-scoped agent-rules reading\n\n"
            "`AGENTS.md`/`CLAUDE.md` states rules for every role in one file; reading all\n"
            "of it in every session is more than a given role needs. Read only the\n"
            "sections your current role requires, identified by heading text:\n\n"
            "- **Every role** reads the file's shared core: the introductory rules\n"
            "  through \"Command triggers\", plus \"Owner-acceptance workflow\".\n"
            "<!-- MERIDIAN:END -->\n\n"
        )
        anchor = "<!-- MERIDIAN:BEGIN capability=minimal-read-only-status v1 -->"
        self.assertIn(anchor, text)
        return text.replace(anchor, block + anchor, 1)

    def test_upgrade_removes_role_scoped_agent_rules_via_the_real_migration(self) -> None:
        """Task 008, using migration 025 itself (not a synthetic fixture): a
        project locked before the retirement has the block cleanly removed by
        `meridian upgrade` to 1.1.22."""
        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        policy.write_text(
            self._reinsert_role_scoped_agent_rules_block(policy.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.21\n", encoding="utf-8")
        shutil.rmtree(self.project)
        self.project.mkdir()
        self.copy_governed_templates()
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        local_policy = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        self.assertIn("capability=role-scoped-agent-rules v1", local_policy.read_text(encoding="utf-8"))

        # Restore the framework to its real, current (post-025) state.
        policy.write_text(
            (ROOT / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.22\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

        applied = self.run_cli("upgrade", "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        upgraded = local_policy.read_text(encoding="utf-8")
        self.assertNotIn("role-scoped-agent-rules", upgraded)
        self.assertNotIn("Role-scoped agent-rules reading", upgraded)
        self.assertIn("capability=validation-scoping v1", upgraded)

        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)

    def test_upgrade_refuses_role_scoped_agent_rules_removal_when_locally_modified(self) -> None:
        """Task 008's other half of AC3: the real migration 025 must refuse
        to discard a local edit inside the block it is retiring."""
        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        policy.write_text(
            self._reinsert_role_scoped_agent_rules_block(policy.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        (self.framework / "VERSION").write_text("1.1.21\n", encoding="utf-8")
        shutil.rmtree(self.project)
        self.project.mkdir()
        self.copy_governed_templates()
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)

        local_policy = self.project / "docs/CONTEXT_BUDGET_POLICY.md"
        local_text = local_policy.read_text(encoding="utf-8")
        local_text = local_text.replace(
            "reading all\nof it in every session is more than a given role needs.",
            "reading all\nof it in every session is more than a given role needs, locally customized.",
        )
        # Also force a genuine three-way-merge conflict on an unrelated line
        # (both sides rename the same heading differently): migration 025's
        # real diff only deletes the retired block, so nothing else in it
        # would otherwise make `merge_clean` fail on its own, and this test's
        # actual target is `remove_retired_markers`'s own refusal once the
        # merge does fail for any reason.
        local_text = local_text.replace("## Task-first loading", "## Task-First Loading (project wording)")
        local_policy.write_text(local_text, encoding="utf-8")

        incoming_policy = (ROOT / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md").read_text(
            encoding="utf-8"
        )
        incoming_policy = incoming_policy.replace(
            "## Task-first loading", "## Task-First Loading (framework wording)"
        )
        policy.write_text(incoming_policy, encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.22\n", encoding="utf-8")

        checked = self.run_cli("upgrade", "--check")
        self.assertEqual(checked.returncode, 2, checked.stdout + checked.stderr)
        self.assertIn("CONFLICT docs/CONTEXT_BUDGET_POLICY.md", checked.stdout)
        self.assertIn("BLOCKED", checked.stdout)
        # The local customization must still be on disk, untouched.
        self.assertIn("locally customized.", local_policy.read_text(encoding="utf-8"))

    def test_audit_passes_on_unmodified_markers(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
        self.assertIn("PASS", audited.stdout)
        self.assertNotIn("FAIL", audited.stdout)

    def test_audit_fails_on_edited_protected_region(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        agents = self.project / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        self.assertIn("MERIDIAN:BEGIN capability=lifecycle-orchestration v3", text)
        edited = text.replace(
            "Act only as the coordinator", "Act only as the coordinator (edited without an upgrade)"
        )
        self.assertNotEqual(text, edited, "the replacement should have matched something inside the marker")
        agents.write_text(edited, encoding="utf-8")

        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 2)
        self.assertIn("FAIL AGENTS.md: capability=lifecycle-orchestration v3", audited.stdout)
        self.assertIn("BLOCKED: 1 protected-region integrity failure", audited.stdout)

    def test_audit_fails_when_a_file_carries_two_versions_of_one_capability(self) -> None:
        """Task 012: a version bump that was appended instead of replacing the
        version it supersedes leaves a contradictory pair behind — the audit
        must surface that, not just per-version drift."""
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        agents = self.project / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        self.assertIn("MERIDIAN:BEGIN capability=command-triggers v1", text)
        relabeled = text.replace(
            "MERIDIAN:BEGIN capability=command-triggers v1",
            "MERIDIAN:BEGIN capability=command-triggers v2",
            1,
        )
        duplicate_block = re.search(
            r"<!-- MERIDIAN:BEGIN capability=command-triggers v2 -->.*?<!-- MERIDIAN:END -->",
            relabeled,
            re.DOTALL,
        )
        self.assertIsNotNone(duplicate_block)
        agents.write_text(text.rstrip() + "\n\n" + duplicate_block.group(0) + "\n", encoding="utf-8")

        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 2)
        self.assertIn(
            "FAIL AGENTS.md: capability=command-triggers carries 2 versions (v1, v2)", audited.stdout
        )

    def test_audit_skips_a_version_the_current_template_no_longer_carries(self) -> None:
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        for name in ("AGENTS.md", "CLAUDE.md"):
            local = self.project / name
            local.write_text(
                local.read_text(encoding="utf-8").replace(
                    "MERIDIAN:BEGIN capability=lifecycle-orchestration v3",
                    "MERIDIAN:BEGIN capability=lifecycle-orchestration v99",
                ),
                encoding="utf-8",
            )

        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)
        self.assertIn("SKIP", audited.stdout)
        self.assertIn("lifecycle-orchestration v99", audited.stdout)
        self.assertNotIn("FAIL", audited.stdout)

    def test_audit_fails_a_retired_marker_still_present_outside_managed_paths(self) -> None:
        """Task 007: a marker whose exact (capability, version) some migration
        declared `removes` must be reported FAIL, not the generic stale SKIP —
        `meridian upgrade` only touches the files a retiring migration's
        `managedPaths` names, so a marker left in an unlisted file would
        otherwise sit as an invisible SKIP forever."""
        self.assertEqual(self.run_cli("lock", "--mode", "governed-sdd").returncode, 0)
        (self.framework / "migrations/999-retire-validation-scoping.json").write_text(
            json.dumps(
                {
                    "id": "999-retire-validation-scoping",
                    "from": "1.1.0",
                    "to": "1.1.1",
                    "description": "test-only retirement",
                    "removes": [{"capability": "validation-scoping", "capabilityVersion": 1}],
                    "managedPaths": ["docs/CONTEXT_BUDGET_POLICY.md"],
                    "verification": ["test-only"],
                }
            ),
            encoding="utf-8",
        )
        policy = self.framework / "templates/workflows/governed-sdd/docs/CONTEXT_BUDGET_POLICY.md"
        policy_text = policy.read_text(encoding="utf-8")
        marker = re.search(
            r"<!-- MERIDIAN:BEGIN capability=validation-scoping v1 -->\n?.*?"
            r"<!-- MERIDIAN:END -->\n?",
            policy_text,
            re.DOTALL,
        )
        self.assertIsNotNone(marker)
        policy.write_text(policy_text[: marker.start()] + policy_text[marker.end() :], encoding="utf-8")
        (self.framework / "VERSION").write_text("1.1.1\n", encoding="utf-8")

        # The project's local copy still carries the marker (upgrade has not
        # run yet), so the audit must catch it as retired-but-present, not
        # a generic "stale, run upgrade" SKIP.
        audited = self.run_cli("audit", "--mode", "governed-sdd")
        self.assertEqual(audited.returncode, 2, audited.stdout + audited.stderr)
        self.assertIn("FAIL", audited.stdout)
        self.assertIn("validation-scoping v1 is retired but still present", audited.stdout)

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
        """A project adopted before migration 006 has no MERIDIAN markers at
        all, only the old bare trigger phrases and template files. The legacy
        fallback correctly proves v1 for both capabilities — not the fully
        MISSING a naive marker-only check would report — but since 008/009
        bumped both to a required v2, v1-only evidence is now correctly
        insufficient rather than falsely treated as fully satisfied. The
        emitted delta must scope the fix to the v1->v2 change, not imply a
        from-scratch rewrite of a capability the project already has."""
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
        # Satisfy validation-scoping and ci-verified-validation too (both carry
        # markers in the current templates), so this test stays about the
        # 001/002 legacy fallback specifically rather than tripping on the two
        # newer, unrelated capabilities.
        current = self.framework / "templates/workflows/governed-sdd"
        for name in (
            "docs/CONTEXT_BUDGET_POLICY.md",
            "docs/PULL_REQUEST_POLICY.md",
            "docs/CODE_REVIEW_PROMPT.md",
            "docs/COMPLETION_REPORT_TEMPLATE.md",
        ):
            shutil.copyfile(current / name, self.project / name)

        planned = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(planned.returncode, 3, planned.stdout)
        # The evidence text proves the legacy fallback did its job (v1 found),
        # distinct from "no marker found" — it's the v1->v2 gap that's real.
        self.assertIn(
            "CAPABILITY MISSING 008-review-remediation-record-v2 — no marker found; "
            "legacy pre-marker evidence only confirms v1, but v2 is required",
            planned.stdout,
        )
        self.assertIn(
            "CAPABILITY MISSING 020-reasoning-budget-contract — no marker found; "
            "legacy pre-marker evidence only confirms v1, but v3 is required",
            planned.stdout,
        )
        self.assertIn("\nNEXT_ACTION IMPLEMENT_MIGRATION\n", planned.stdout)
        # The implementer is pointed at the delta, not a from-scratch rewrite:
        # the capability is already there, only the path reference is stale.
        self.assertIn("apply only this", planned.stdout)
        self.assertIn("008-review-remediation-record-v2: Replace the literal", planned.stdout)
        self.assertIn("020-reasoning-budget-contract", planned.stdout)

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
        # Satisfy validation-scoping, ci-verified-validation, and
        # PROJECT_WORKFLOW.md's eight baseline capabilities (all carry markers
        # in the current templates) so this test can focus purely on the
        # 001/002 legacy-fallback progression it's actually about; a marker
        # only needs to be found somewhere among managed files, not
        # specifically in AGENTS.md/CLAUDE.md.
        for name in (
            "docs/CONTEXT_BUDGET_POLICY.md",
            "docs/PULL_REQUEST_POLICY.md",
            "docs/CODE_REVIEW_PROMPT.md",
            "docs/COMPLETION_REPORT_TEMPLATE.md",
            "PROJECT_WORKFLOW.md",
            "LANGUAGE_POLICY.md",
            "tasks/TASK_BLUEPRINT.md",
            "docs/CODE_ORGANIZATION.md",
            "docs/AUDIT_PROMPT_READ_ONLY.md",
        ):
            shutil.copyfile(current / name, self.project / name)
        for name in ("AGENTS.md", "CLAUDE.md"):
            target = self.project / name
            target.write_text(target.read_text(encoding="utf-8") + "\nAddress review <TASK-ID>.\n", encoding="utf-8")

        planned = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(planned.returncode, 3)
        # detect_capabilities() names the migration that introduced the
        # highest required version, not necessarily the original one — 008
        # carries the v2 delta a project stuck at v1 actually needs to apply.
        self.assertIn("CAPABILITY PRESENT 008-review-remediation-record-v2", planned.stdout)
        self.assertIn("CAPABILITY MISSING 020-reasoning-budget-contract", planned.stdout)
        self.assertIn("AGENT_REQUIRED", planned.stdout)
        self.assertIn("\nNEXT_ACTION IMPLEMENT_MIGRATION\n", planned.stdout)
        self.assertIn("IMPLEMENTER_PROMPT_BEGIN", planned.stdout)
        self.assertIn("REVIEWER_PROMPT_BEGIN", planned.stdout)
        self.assertIn("This reviewer session must be fresh", planned.stdout)
        self.assertIn("ORCHESTRATOR_PROMPT_BEGIN", planned.stdout)
        self.assertIn("adoption-review.md", planned.stdout)
        self.assertIn("020-reasoning-budget-contract", planned.stdout)
        self.assertIn("migrations/020-reasoning-budget-contract.json", planned.stdout)
        self.assertIn("/bin/meridian finalize-adoption", planned.stdout)
        self.assertFalse((self.project / ".meridian").exists())

        shutil.copyfile(current / "docs/LIFECYCLE_ORCHESTRATION.md", self.project / "docs/LIFECYCLE_ORCHESTRATION.md")
        # Replace AGENTS.md/CLAUDE.md wholesale with the current, fully marked
        # templates rather than appending one more bare phrase: this test's
        # legacy-fallback evidence was already captured above, and the five
        # AGENTS.md/CLAUDE.md-only baseline capabilities from migration 012
        # have no legacy fallback of their own to satisfy any other way.
        for name in ("AGENTS.md", "CLAUDE.md"):
            shutil.copyfile(current / name, self.project / name)
        shutil.copyfile(
            current / "docs/EXECUTION_EVIDENCE_PROFILE.md",
            self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md",
        )

        # All capabilities are now present, but nothing has been reviewed yet:
        # finalize must refuse, and the plan must ask for an independent review.
        refused = self.run_cli("finalize-adoption", "--mode", "governed-sdd")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("no independent review record found", refused.stderr)

        reviewing = self.run_cli(
            "adopt", "--mode", "governed-sdd", "--from", "1.0.0", "--assisted", "--check"
        )
        self.assertEqual(reviewing.returncode, 3)
        self.assertIn("\nNEXT_ACTION REVIEW_MIGRATION\n", reviewing.stdout)
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
        self.assertIn("\nNEXT_ACTION FINALIZE\n", ready.stdout)

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
        self.assertIn("\nNEXT_ACTION ADDRESS_REVIEW\n", planned.stdout)
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
        for name in (
            "AGENTS.md",
            "CLAUDE.md",
            "PROJECT_WORKFLOW.md",
            "LANGUAGE_POLICY.md",
            "tasks/TASK_BLUEPRINT.md",
            "docs/CODE_ORGANIZATION.md",
            "docs/AUDIT_PROMPT_READ_ONLY.md",
            "docs/REVIEW_RECORD_TEMPLATE.md",
            "docs/LIFECYCLE_ORCHESTRATION.md",
            "docs/CONTEXT_BUDGET_POLICY.md",
            "docs/EXECUTION_EVIDENCE_PROFILE.md",
            "docs/PULL_REQUEST_POLICY.md",
            "docs/CODE_REVIEW_PROMPT.md",
            "docs/COMPLETION_REPORT_TEMPLATE.md",
        ):
            shutil.copyfile(current / name, self.project / name)

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


class MarkerSupersessionTest(unittest.TestCase):
    """`append_only_new_markers` must distinguish an added capability from a
    superseded one by name, not by `(name, version)` pair — task 012 of
    docs/PLAN_TOKEN_EFFICIENCY.md. Under pair comparison, a version bump is
    indistinguishable from an unrelated new capability: the bumped pair is
    absent from both the local and base pair sets exactly like a genuinely
    new one, so the old block gets left in place while the new one is
    appended at the end, where nothing reads it.
    """

    BASE = (
        "intro\n\n"
        "<!-- MERIDIAN:BEGIN capability=mvp v1 -->\n"
        "old rule text.\n"
        "<!-- MERIDIAN:END -->\n\n"
        "tail\n"
    )
    OLD_BLOCK = "<!-- MERIDIAN:BEGIN capability=mvp v1 -->\nold rule text.\n<!-- MERIDIAN:END -->"
    NEW_BLOCK = "<!-- MERIDIAN:BEGIN capability=mvp v2 -->\nnew rule text.\n<!-- MERIDIAN:END -->"

    def test_added_capability_still_appends(self) -> None:
        template = self.BASE + (
            "\n<!-- MERIDIAN:BEGIN capability=other v1 -->\n"
            "new capability.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        result = meridian.append_only_new_markers(self.BASE, self.BASE, template)
        self.assertIsNotNone(result)
        self.assertIn("old rule text.", result)
        self.assertIn("new capability.", result)

    def test_bumped_capability_with_unmodified_block_replaces_in_place(self) -> None:
        template = self.BASE.replace(self.OLD_BLOCK, self.NEW_BLOCK)
        result = meridian.append_only_new_markers(self.BASE, self.BASE, template)
        self.assertIsNotNone(result)
        self.assertIn("capability=mvp v2", result)
        self.assertIn("new rule text.", result)
        self.assertNotIn("capability=mvp v1", result)
        self.assertNotIn("old rule text.", result)
        # Surrounding project-owned text is preserved untouched, in place.
        self.assertIn("intro", result)
        self.assertIn("tail", result)
        self.assertEqual(result.index("intro"), self.BASE.index("intro"))

    def test_bumped_capability_with_modified_block_returns_none(self) -> None:
        local = self.BASE.replace("old rule text.", "old rule text, locally customized.")
        template = self.BASE.replace(self.OLD_BLOCK, self.NEW_BLOCK)
        result = meridian.append_only_new_markers(local, self.BASE, template)
        self.assertIsNone(result)

    def test_local_file_with_two_existing_versions_is_left_untouched(self) -> None:
        local = self.BASE + "\n" + self.NEW_BLOCK + "\n"
        template = self.BASE.replace(self.OLD_BLOCK, self.NEW_BLOCK)
        result = meridian.append_only_new_markers(local, self.BASE, template)
        self.assertIsNone(result)

    def test_edited_unchanged_version_block_blocks_an_otherwise_safe_append(self) -> None:
        """A capability whose version does not change must still be checked
        against the base: an unrelated new capability elsewhere in the same
        template must not cause the function to silently accept a project's
        edit to a different, already-current protected block."""
        local = self.BASE.replace("old rule text.", "old rule text, locally edited.")
        template = self.BASE + (
            "\n<!-- MERIDIAN:BEGIN capability=other v1 -->\n"
            "new capability.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        result = meridian.append_only_new_markers(local, self.BASE, template)
        self.assertIsNone(result)


class CapabilityRetirementTest(unittest.TestCase):
    """`remove_retired_markers` (task 007 of docs/PLAN_TOKEN_EFFICIENCY.md):
    the retirement mirror of `append_only_new_markers`'s supersession case.
    Safe to delete a capability's block only when the local copy still
    matches the project's own locked baseline byte-for-byte; refuse
    otherwise so a local edit under a marker about to be deleted is never
    silently discarded along with it.
    """

    BASE = (
        "intro\n\n"
        "<!-- MERIDIAN:BEGIN capability=old-rule v1 -->\n"
        "retired rule text.\n"
        "<!-- MERIDIAN:END -->\n\n"
        "tail\n"
    )

    def test_retires_an_unmodified_block(self) -> None:
        result = meridian.remove_retired_markers(self.BASE, self.BASE, [("old-rule", 1)])
        self.assertIsNotNone(result)
        self.assertNotIn("capability=old-rule", result)
        self.assertNotIn("retired rule text.", result)
        # Surrounding project-owned text survives untouched.
        self.assertIn("intro", result)
        self.assertIn("tail", result)

    def test_retiring_an_already_absent_block_is_idempotent(self) -> None:
        local = self.BASE.replace(
            "<!-- MERIDIAN:BEGIN capability=old-rule v1 -->\n"
            "retired rule text.\n"
            "<!-- MERIDIAN:END -->\n\n",
            "",
        )
        result = meridian.remove_retired_markers(local, self.BASE, [("old-rule", 1)])
        self.assertEqual(result, local)

    def test_refuses_to_retire_a_locally_modified_block(self) -> None:
        local = self.BASE.replace("retired rule text.", "retired rule text, locally customized.")
        result = meridian.remove_retired_markers(local, self.BASE, [("old-rule", 1)])
        self.assertIsNone(result)

    def test_returns_input_unchanged_when_nothing_in_the_list_applies(self) -> None:
        result = meridian.remove_retired_markers(self.BASE, self.BASE, [("unrelated-capability", 1)])
        self.assertEqual(result, self.BASE)

    def test_refuses_when_the_same_block_appears_twice_in_one_file(self) -> None:
        """`str.replace` is content-addressed: deleting only the first of two
        byte-identical occurrences would be a silent partial mutation. Must
        refuse instead, the same duplicate-paste case `audit_duplicate_headings`
        exists to catch."""
        duplicated = self.BASE + (
            "\n<!-- MERIDIAN:BEGIN capability=old-rule v1 -->\n"
            "retired rule text.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        result = meridian.remove_retired_markers(duplicated, duplicated, [("old-rule", 1)])
        self.assertIsNone(result)

    def test_removal_collapses_only_the_local_blank_line_gap(self) -> None:
        """The blank-line cleanup after a deletion must be scoped to the
        splice point, never touching an unrelated run of blank lines
        elsewhere in the same file."""
        text = (
            "intro\n\n"
            "<!-- MERIDIAN:BEGIN capability=old-rule v1 -->\n"
            "retired rule text.\n"
            "<!-- MERIDIAN:END -->\n\n"
            "middle\n\n\n\n"
            "tail\n"
        )
        result = meridian.remove_retired_markers(text, text, [("old-rule", 1)])
        self.assertIsNotNone(result)
        self.assertEqual(result, "intro\n\nmiddle\n\n\n\ntail\n")

    def test_capability_requirements_drops_a_retired_capability(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        framework = Path(temporary.name)
        migrations = framework / "migrations"
        migrations.mkdir()
        (migrations / "001-add.json").write_text(
            json.dumps(
                {
                    "id": "001-add",
                    "from": "1.0.0",
                    "to": "1.1.0",
                    "capability": "old-rule",
                    "capabilityVersion": 1,
                    "managedPaths": ["AGENTS.md"],
                }
            ),
            encoding="utf-8",
        )
        (migrations / "002-retire.json").write_text(
            json.dumps(
                {
                    "id": "002-retire",
                    "from": "1.1.0",
                    "to": "1.2.0",
                    "removes": [{"capability": "old-rule", "capabilityVersion": 1}],
                    "managedPaths": ["AGENTS.md"],
                }
            ),
            encoding="utf-8",
        )
        requirements = meridian.capability_requirements(framework)
        self.assertNotIn("old-rule", requirements)
        self.assertIn("old-rule", meridian.retired_capability_ids(framework))

    def test_capability_requirements_honors_a_later_reintroduction(self) -> None:
        """A capability retired by one migration and reintroduced by a later
        one must end up required again — removal and addition are applied in
        migration sequence order, not as an unordered set operation."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        framework = Path(temporary.name)
        migrations = framework / "migrations"
        migrations.mkdir()
        (migrations / "001-add.json").write_text(
            json.dumps(
                {
                    "id": "001-add",
                    "from": "1.0.0",
                    "to": "1.1.0",
                    "capability": "reused-rule",
                    "capabilityVersion": 1,
                    "managedPaths": ["AGENTS.md"],
                }
            ),
            encoding="utf-8",
        )
        (migrations / "002-retire.json").write_text(
            json.dumps(
                {
                    "id": "002-retire",
                    "from": "1.1.0",
                    "to": "1.2.0",
                    "removes": [{"capability": "reused-rule", "capabilityVersion": 1}],
                    "managedPaths": ["AGENTS.md"],
                }
            ),
            encoding="utf-8",
        )
        (migrations / "003-reintroduce.json").write_text(
            json.dumps(
                {
                    "id": "003-reintroduce",
                    "from": "1.2.0",
                    "to": "1.3.0",
                    "capability": "reused-rule",
                    "capabilityVersion": 1,
                    "managedPaths": ["AGENTS.md"],
                }
            ),
            encoding="utf-8",
        )
        requirements = meridian.capability_requirements(framework)
        self.assertIn("reused-rule", requirements)
        self.assertEqual(requirements["reused-rule"], (1, "003-reintroduce"))

    def test_removals_for_managed_file_scopes_by_managed_paths(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        framework = Path(temporary.name)
        migrations = framework / "migrations"
        migrations.mkdir()
        (migrations / "001-retire.json").write_text(
            json.dumps(
                {
                    "id": "001-retire",
                    "from": "1.0.0",
                    "to": "1.1.0",
                    "removes": [{"capability": "old-rule", "capabilityVersion": 1, "supersededBy": "new-rule"}],
                    "managedPaths": ["AGENTS.md", "CLAUDE.md"],
                }
            ),
            encoding="utf-8",
        )
        for_agents = meridian.removals_for_managed_file(framework, ["001-retire"], Path("AGENTS.md"))
        self.assertEqual(for_agents, [("old-rule", 1, "new-rule")])
        for_unrelated = meridian.removals_for_managed_file(
            framework, ["001-retire"], Path("docs/UNRELATED.md")
        )
        self.assertEqual(for_unrelated, [])


class GenerateClaudeMdTest(unittest.TestCase):
    """`CLAUDE.md` is generated from `AGENTS.md` (task 004 of
    docs/PLAN_TOKEN_EFFICIENCY.md): from `meridian.CLAUDE_MD_SHARED_ANCHOR`'s
    heading onward, the committed `CLAUDE.md` must be byte-identical to what
    `generate_claude_md` derives from the committed `AGENTS.md`, so the two
    files cannot independently drift on content meant to be shared. Everything
    above the anchor is each file's own hand-authored preamble and is exempt.
    """

    def test_committed_claude_md_matches_the_generator_for_every_mode(self) -> None:
        for mode in meridian.CLAUDE_MD_SHARED_ANCHOR:
            workflow = ROOT / "templates" / "workflows" / mode
            agents_text = (workflow / "AGENTS.md").read_text(encoding="utf-8")
            claude_text = (workflow / "CLAUDE.md").read_text(encoding="utf-8")
            generated = meridian.generate_claude_md(mode, agents_text, claude_text)
            self.assertEqual(
                generated,
                claude_text,
                f"{mode}: CLAUDE.md has drifted from AGENTS.md past the shared anchor "
                f"{meridian.CLAUDE_MD_SHARED_ANCHOR[mode]!r}",
            )

    def test_generator_reports_drift_when_claude_md_diverges(self) -> None:
        agents_text = (
            "# [Project Name] — Agent Rules\n\npreamble\n\n"
            "## Code organization\n\nshared body.\n"
        )
        stale_claude_text = (
            "# [Project Name]\n\nown preamble\n\n"
            "## Code organization\n\nSTALE shared body.\n"
        )
        generated = meridian.generate_claude_md("governed-sdd", agents_text, stale_claude_text)
        self.assertNotEqual(generated, stale_claude_text)
        self.assertIn("own preamble", generated)
        self.assertIn("shared body.\n", generated)
        self.assertNotIn("STALE", generated)

    def test_generator_preserves_marker_content_verbatim_even_when_agents_md_disagrees(self) -> None:
        """The regression guard for task 014: task 004's generator copied a
        marker's content from AGENTS.md, silently changing what a released
        capability version means for every adopted project. The self-
        consistency test above can never catch that, because it compares the
        generator's output to a `CLAUDE.md` that was itself regenerated by the
        same generator. This test instead gives AGENTS.md and CLAUDE.md
        genuinely different text for the same capability+version marker and
        asserts the output keeps CLAUDE.md's own text, byte for byte — a
        marker's content may only change via a version bump and a migration,
        never via this generator.
        """
        agents_text = (
            "# [Project Name] — Agent Rules\n\npreamble\n\n"
            "## Code organization\n\n"
            "<!-- MERIDIAN:BEGIN capability=example-capability v1 -->\n"
            "NEW WORDING the generator must not introduce.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        claude_text = (
            "# [Project Name]\n\nown preamble\n\n"
            "## Code organization\n\n"
            "<!-- MERIDIAN:BEGIN capability=example-capability v1 -->\n"
            "ORIGINAL RELEASED WORDING.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        generated = meridian.generate_claude_md("governed-sdd", agents_text, claude_text)
        self.assertIn("ORIGINAL RELEASED WORDING.", generated)
        self.assertNotIn("NEW WORDING", generated)
        for capability, version in meridian.marker_pairs(claude_text):
            self.assertEqual(
                meridian.extract_marked_block(generated, capability, version),
                meridian.extract_marked_block(claude_text, capability, version),
                f"capability={capability} v{version} was altered by the generator",
            )

    def test_generator_copies_a_brand_new_marker_claude_md_does_not_have_yet(self) -> None:
        """A capability with no existing block in CLAUDE.md has nothing to
        preserve; the generator's only source for its first appearance is
        AGENTS.md, same as any other shared-body text."""
        agents_text = (
            "# [Project Name] — Agent Rules\n\npreamble\n\n"
            "## Code organization\n\n"
            "<!-- MERIDIAN:BEGIN capability=brand-new-capability v1 -->\n"
            "First-ever wording.\n"
            "<!-- MERIDIAN:END -->\n"
        )
        claude_text = "# [Project Name]\n\nown preamble\n\n## Code organization\n\nno markers here.\n"
        generated = meridian.generate_claude_md("governed-sdd", agents_text, claude_text)
        self.assertIn("First-ever wording.", generated)

    def test_generator_raises_when_the_anchor_heading_is_missing(self) -> None:
        with self.assertRaises(meridian.MeridianError):
            meridian.generate_claude_md("governed-sdd", "no anchor here", "## Code organization\nbody")
        with self.assertRaises(meridian.MeridianError):
            meridian.generate_claude_md("governed-sdd", "## Code organization\nbody", "no anchor here")

    def test_cli_check_and_write_round_trip_on_a_stale_copy(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        framework = Path(temporary.name) / "framework"
        workflow = framework / "templates" / "workflows" / "governed-sdd"
        workflow.mkdir(parents=True)
        source = ROOT / "templates" / "workflows" / "governed-sdd"
        agents_text = (source / "AGENTS.md").read_text(encoding="utf-8")
        claude_text = (source / "CLAUDE.md").read_text(encoding="utf-8")
        (workflow / "AGENTS.md").write_text(
            agents_text.replace("## Code organization", "## Code organization\n\nstale.", 1),
            encoding="utf-8",
        )
        (workflow / "CLAUDE.md").write_text(claude_text, encoding="utf-8")

        def run(*extra: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--framework-root",
                    str(framework),
                    "generate-claude-md",
                    "--mode",
                    "governed-sdd",
                    *extra,
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        checked_before = run("--check")
        self.assertEqual(checked_before.returncode, 2)
        self.assertIn("STALE", checked_before.stderr)

        written = run("--write")
        self.assertEqual(written.returncode, 0, written.stderr)

        checked_after = run("--check")
        self.assertEqual(checked_after.returncode, 0, checked_after.stderr)
        self.assertIn(
            "stale.", (workflow / "CLAUDE.md").read_text(encoding="utf-8")
        )


class BudgetCliTest(unittest.TestCase):
    """`meridian budget`: durable per-task-per-attempt diagnostic/evidence/
    context-expansion counters (task 006 of docs/PLAN_TOKEN_EFFICIENCY.md)."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        (self.project / "tasks").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_task(self, task_id: str, status: str, **overrides: str) -> None:
        lines = [f"Status: {status}"]
        for field, value in overrides.items():
            lines.append(f"{field}: {value}")
        (self.project / "tasks" / f"{task_id}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    def budget_state(self) -> dict:
        return json.loads((self.project / ".meridian/budget.json").read_text(encoding="utf-8"))

    def append_contract(self, task_id: str) -> None:
        path = self.project / "tasks" / f"{task_id}.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n" + meridian.execution_contract(self.project, task_id) + "\n", encoding="utf-8")

    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *arguments, "--project", str(self.project)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_show_defaults_with_no_state(self) -> None:
        self.write_task("TASK-001", "IN_PROGRESS")
        result = self.run_cli("budget", "show", "TASK-001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "Diagnostics 0/3 · Captures 0/2 · Expansions 0/2"
        )

    def test_show_resolves_nested_project_tasks_and_profile_defaults(self) -> None:
        (self.project / "tasks/TASK-007.md").unlink(missing_ok=True)
        nested = self.project / "docs/tasks/M19"
        nested.mkdir(parents=True)
        (nested / "TASK-007.md").write_text("Status: IN_PROGRESS\n", encoding="utf-8")
        (self.project / "PROJECT_WORKFLOW.md").write_text(
            "<!-- MERIDIAN:BEGIN capability=execution-assets v1 -->\n"
            "<!-- MERIDIAN:END -->\n"
            "Task files live under `docs/tasks/<milestone>/`; queue is `docs/TASK_QUEUE.md`.\n\n## Roles\n",
            encoding="utf-8",
        )
        profile = self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md"
        profile.parent.mkdir(exist_ok=True)
        profile.write_text(
            "`Diagnostic attempts`: 4 per failure.\n"
            "`Evidence captures`: 5 per acceptance criterion.\n"
            "`Context expansions`: 6 per task.\n",
            encoding="utf-8",
        )
        result = self.run_cli("budget", "show", "TASK-007")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "Diagnostics 0/4 · Captures 0/5 · Expansions 0/6"
        )

    def test_locations_and_preflight_use_the_declared_queue(self) -> None:
        (self.project / "docs/tasks/M19").mkdir(parents=True)
        (self.project / "docs/tasks/M19/TASK-007.md").write_text(
            "Status: IN_PROGRESS\n\n## Authority\n\n## Expected code surface\n\n## Validation\n",
            encoding="utf-8",
        )
        (self.project / "docs/TASK_QUEUE.md").write_text(
            "| Order | ID | Priority | Status | Dependencies |\n|---:|---|---|---|---|\n"
            "| 1 | TASK-007 | P0 | QUEUED | — |\n",
            encoding="utf-8",
        )
        (self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md").write_text("profile\n", encoding="utf-8")
        (self.project / "PROJECT_WORKFLOW.md").write_text(
            "<!-- MERIDIAN:BEGIN capability=execution-assets v1 -->\n<!-- MERIDIAN:END -->\n"
            "Task files live under `docs/tasks/<milestone>/`; queue is `docs/TASK_QUEUE.md`.\n\n## Roles\n",
            encoding="utf-8",
        )
        nested_task = self.project / "docs/tasks/M19/TASK-007.md"
        nested_task.write_text(
            nested_task.read_text(encoding="utf-8") + "\n" + meridian.execution_contract(self.project, "TASK-007") + "\n",
            encoding="utf-8",
        )
        locations = self.run_cli("locations", "--field", "queue")
        self.assertEqual(locations.stdout.strip(), "docs/TASK_QUEUE.md")
        preflight = self.run_cli("execution", "preflight", "TASK-007")
        self.assertNotEqual(preflight.returncode, 0)
        self.assertIn("disagrees with queue status", preflight.stderr)

    def test_execution_preflight_requires_profile_and_task_contract(self) -> None:
        self.write_task("TASK-008", "QUEUED")
        missing = self.run_cli("execution", "preflight", "TASK-008")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("missing docs/EXECUTION_EVIDENCE_PROFILE.md", missing.stderr)
        (self.project / "docs").mkdir()
        (self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md").write_text("profile\n", encoding="utf-8")
        (self.project / "tasks/TASK-008.md").write_text(
            "Status: QUEUED\n\n## Authority\n\n## Expected code surface\n\n## Validation\n",
            encoding="utf-8",
        )
        self.append_contract("TASK-008")
        passed = self.run_cli("execution", "preflight", "TASK-008")
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertIn("Execution contract:", passed.stdout)

    def test_handoff_check_rejects_missing_budget_usage(self) -> None:
        report = self.project / "handoff.md"
        report.write_text(
            "## Completion Report — TASK-009\n\n"
            "- Files changed: `a.rs`\n- Validation: `cargo test` exit 0\n"
            "- Manual verification: none\n- Acceptance criteria: all met\n"
            "- Blockers/deviations: none\n",
            encoding="utf-8",
        )
        result = self.run_cli("execution", "handoff-check", "TASK-009", str(report))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Budget usage", result.stderr)

    def test_ready_check_combines_preflight_and_handoff(self) -> None:
        (self.project / "docs").mkdir()
        (self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md").write_text("profile\n", encoding="utf-8")
        (self.project / "tasks/TASK-012.md").write_text(
            "Status: IN_PROGRESS\n\n## Authority\n\n## Expected code surface\n\n## Validation\n",
            encoding="utf-8",
        )
        self.append_contract("TASK-012")
        report = self.project / "ready.md"
        report.write_text(
            "## Completion Report — TASK-012\n\n- Files changed: none\n- Validation: exit 0\n"
            "- Manual verification: none\n- Acceptance criteria: all met\n- Budget usage: 0/3\n"
            "- Blockers/deviations: none\n",
            encoding="utf-8",
        )
        result = self.run_cli("execution", "ready-check", "TASK-012", str(report))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READY_FOR_REVIEW gate passed", result.stdout)

    def test_validation_runs_only_a_declared_literal_command_and_records_status(self) -> None:
        (self.project / "docs").mkdir()
        (self.project / "docs/EXECUTION_EVIDENCE_PROFILE.md").write_text("profile\n", encoding="utf-8")
        (self.project / "tasks/TASK-010.md").write_text(
            "Status: IN_PROGRESS\n\n## Authority\n\n## Expected code surface\n\n"
            "## Validation\n\n- `probe`: `printf validation-ok`\n",
            encoding="utf-8",
        )
        self.append_contract("TASK-010")
        result = self.run_cli("execution", "validate", "TASK-010", "probe")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validation-ok", result.stdout)
        evidence = json.loads((self.project / ".meridian/execution-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["TASK-010"][0]["id"], "probe")
        missing = self.run_cli("execution", "validate", "TASK-010", "not-declared")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("not a declared validation ID", missing.stderr)

    def test_evidence_requires_a_gap_and_capture_provenance(self) -> None:
        self.write_task("TASK-011", "IN_PROGRESS")
        missing = self.run_cli("execution", "evidence", "TASK-011", "captures", "--gap", "text is perceptual")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("require --criterion and --artifact", missing.stderr)
        recorded = self.run_cli(
            "execution", "evidence", "TASK-011", "captures", "--gap", "text is perceptual",
            "--criterion", "AC-4", "--artifact", "/tmp/capture.png",
        )
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        evidence = json.loads((self.project / ".meridian/execution-evidence.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["TASK-011"][0]["criterion"], "AC-4")
        self.assertEqual(evidence["TASK-011"][0]["artifact"], "/tmp/capture.png")
        other = self.run_cli(
            "execution", "evidence", "TASK-011", "captures", "--gap", "second criterion",
            "--criterion", "AC-5", "--artifact", "/tmp/second.png",
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        shown = self.run_cli("budget", "show", "TASK-011")
        self.assertIn("AC-4 1/2, AC-5 1/2", shown.stdout)

    def test_spend_increments_and_reports(self) -> None:
        self.write_task("TASK-002", "IN_PROGRESS")
        first = self.run_cli("budget", "spend", "TASK-002", "diagnostic")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout.strip(), "TASK-002: diagnostic 1/3")
        second = self.run_cli("budget", "spend", "TASK-002", "diagnostic")
        self.assertEqual(second.stdout.strip(), "TASK-002: diagnostic 2/3")

    def test_spend_returns_non_zero_and_names_blocked_once_cap_reached(self) -> None:
        self.write_task("TASK-003", "IN_PROGRESS")
        # Default cap is 2 captures; the first spend stays under it.
        self.assertEqual(
            self.run_cli("budget", "spend", "TASK-003", "captures").returncode, 0
        )
        exhausted = self.run_cli("budget", "spend", "TASK-003", "captures")
        self.assertNotEqual(exhausted.returncode, 0)
        self.assertIn("BLOCKED", exhausted.stderr)
        self.assertIn("Evidence captures exhausted", exhausted.stderr)
        self.assertIn("(2/2)", exhausted.stderr)

    def test_spend_respects_task_override_cap(self) -> None:
        self.write_task("TASK-004", "IN_PROGRESS", **{"Diagnostic attempts": "1"})
        first = self.run_cli("budget", "spend", "TASK-004", "diagnostic")
        self.assertNotEqual(first.returncode, 0)
        self.assertIn("(1/1)", first.stderr)

    def test_unknown_task_is_blocked_without_writing_state(self) -> None:
        result = self.run_cli("budget", "show", "TASK-NOPE")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown task", result.stderr)
        self.assertFalse((self.project / ".meridian/budget.json").exists())

    def test_missing_budget_file_is_treated_as_a_fresh_project(self) -> None:
        self.write_task("TASK-005", "IN_PROGRESS")
        self.assertFalse((self.project / ".meridian/budget.json").exists())
        result = self.run_cli("budget", "show", "TASK-005")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0/3", result.stdout)

    def test_new_review_attempt_gets_a_fresh_allocation(self) -> None:
        self.write_task("TASK-006", "IN_PROGRESS")
        self.run_cli("budget", "spend", "TASK-006", "diagnostic")
        self.run_cli("budget", "spend", "TASK-006", "diagnostic")

        # Reviewer's handoff commit moves the task to READY_FOR_REVIEW...
        self.write_task("TASK-006", "READY_FOR_REVIEW")
        self.run_cli("budget", "show", "TASK-006")
        # ...then `Address review TASK-006` moves it back to IN_PROGRESS: a
        # new remediation attempt, which must not inherit the old counters.
        self.write_task("TASK-006", "IN_PROGRESS")

        after = self.run_cli("budget", "spend", "TASK-006", "diagnostic")
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(after.stdout.strip(), "TASK-006: diagnostic 1/3")

        state = self.budget_state()
        self.assertEqual(state["TASK-006"]["attempt"], 2)
        self.assertEqual(state["TASK-006:1"]["diagnostic"], 2)
        self.assertEqual(state["TASK-006:2"]["diagnostic"], 1)


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

    def test_agents_and_claude_carry_expected_marker_versions(self) -> None:
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.WORKFLOW / name).read_text(encoding="utf-8")
            pairs = self.marker_pairs(text)
            self.assertIn(("review-remediation-record", "2"), pairs, name)
            self.assertIn(("lifecycle-orchestration", "3"), pairs, name)
            self.assertIn(("validation-scoping", "1"), pairs, name)
            self.assertIn(("spike-routing", "1"), pairs, name)

    def test_review_record_template_carries_its_own_marker(self) -> None:
        text = (self.WORKFLOW / "docs/REVIEW_RECORD_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertEqual(
            self.marker_pairs(text),
            [("review-remediation-record", "2"), ("manual-verification-record", "1")],
        )

    def test_lifecycle_orchestration_carries_its_own_marker(self) -> None:
        text = (self.WORKFLOW / "docs/LIFECYCLE_ORCHESTRATION.md").read_text(encoding="utf-8")
        self.assertEqual(self.marker_pairs(text), [("lifecycle-orchestration", "3")])

    def test_context_budget_policy_carries_its_capability_markers(self) -> None:
        text = (self.WORKFLOW / "docs/CONTEXT_BUDGET_POLICY.md").read_text(encoding="utf-8")
        self.assertEqual(
            self.marker_pairs(text),
            [
                ("queue-briefing", "1"),
                ("minimal-read-only-status", "1"),
                ("validation-scoping", "1"),
                ("evidence-tiers", "1"),
                ("execution-evidence-profile", "3"),
                ("reasoning-budget-contract", "1"),
            ],
        )

    def test_execution_evidence_profile_is_stack_agnostic_and_configurable(self) -> None:
        policy = (self.WORKFLOW / "docs/CONTEXT_BUDGET_POLICY.md").read_text(encoding="utf-8")
        profile = (self.WORKFLOW / "docs/EXECUTION_EVIDENCE_PROFILE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(("execution-evidence-profile", "3"), self.marker_pairs(policy))
        self.assertIn("Successful validation output", profile)
        self.assertIn("Failure diagnostics", profile)
        self.assertIn("Manual evidence", profile)
        self.assertNotIn("cargo", profile.lower())

    def test_reasoning_budget_contract_uses_an_exact_cap_without_auto_escalation(self) -> None:
        blueprint = (self.WORKFLOW / "tasks/TASK_BLUEPRINT.md").read_text(encoding="utf-8")
        policy = (self.WORKFLOW / "docs/CONTEXT_BUDGET_POLICY.md").read_text(
            encoding="utf-8"
        )
        lifecycle = (self.WORKFLOW / "docs/LIFECYCLE_ORCHESTRATION.md").read_text(
            encoding="utf-8"
        )
        prompts = (self.WORKFLOW / "docs/OPERATOR_PROMPTS.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(("task-blueprint", "9"), self.marker_pairs(blueprint))
        self.assertIn(("reasoning-budget-contract", "1"), self.marker_pairs(policy))
        self.assertIn(("lifecycle-orchestration", "3"), self.marker_pairs(lifecycle))
        self.assertIn("[low / medium / high / xhigh]", blueprint)
        self.assertIn("exact permitted runtime cap", blueprint)
        self.assertIn("must never raise its effort", blueprint)
        self.assertIn("automatically", blueprint)
        self.assertIn("cannot be confirmed", policy)
        self.assertIn("explicit authorization", policy)
        self.assertIn("Never escalate either worker", lifecycle)
        self.assertIn("automatically", lifecycle)
        self.assertIn("exact permitted cap", prompts)

    def test_role_scoped_agent_rules_was_retired_not_merely_deleted_by_hand(self) -> None:
        """Task 008 retired `role-scoped-agent-rules` (docs/AUDIT_TOKEN_EFFICIENCY.md
        F5) through migration 025's `removes` field, task 007's retirement
        path — not a direct template edit. This is the regression guard for
        that decision: the capability, and the section it named, must stay
        gone, and `capability_requirements()` must no longer require it."""
        policy = (self.WORKFLOW / "docs/CONTEXT_BUDGET_POLICY.md").read_text(encoding="utf-8")
        self.assertNotIn("role-scoped-agent-rules", policy)
        self.assertNotIn("Role-scoped agent-rules reading", policy)
        self.assertIn("role-scoped-agent-rules", meridian.retired_capability_ids(ROOT))
        self.assertNotIn("role-scoped-agent-rules", meridian.capability_requirements(ROOT))

    def test_minimal_read_only_status_profile_limits_context_expansion(self) -> None:
        policy = (self.WORKFLOW / "docs/CONTEXT_BUDGET_POLICY.md").read_text(encoding="utf-8")
        prompts = (self.WORKFLOW / "docs/OPERATOR_PROMPTS.md").read_text(encoding="utf-8")
        self.assertIn("A status report is not a conformance audit.", policy)
        self.assertIn("Before every expanded read", policy)
        self.assertIn("Use the minimal read-only status profile", prompts)
        self.assertIn("Do not load completed milestones", prompts)

    def test_ci_verified_validation_marker_in_each_of_its_three_docs(self) -> None:
        pull_request_policy = (self.WORKFLOW / "docs/PULL_REQUEST_POLICY.md").read_text(encoding="utf-8")
        self.assertEqual(self.marker_pairs(pull_request_policy), [("ci-verified-validation", "1")])

        code_review_prompt = (self.WORKFLOW / "docs/CODE_REVIEW_PROMPT.md").read_text(encoding="utf-8")
        self.assertEqual(
            self.marker_pairs(code_review_prompt),
            [("manual-verification-review-check", "1"), ("ci-verified-validation", "1")],
        )

        completion_report = (self.WORKFLOW / "docs/COMPLETION_REPORT_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertEqual(
            self.marker_pairs(completion_report),
            [("manual-verification-record", "1"), ("ci-verified-validation", "1")],
        )

    def test_manual_verification_precondition_gates_implementation_start(self) -> None:
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.WORKFLOW / name).read_text(encoding="utf-8")
            pairs = self.marker_pairs(text)
            self.assertIn(("manual-verification-precondition", "3"), pairs, name)
        agents = (self.WORKFLOW / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Manual verification: required", agents)
        self.assertIn("return `BLOCKED` immediately", agents)
        self.assertIn("deterministic test", agents)
        self.assertIn("probe that actually succeeds", agents)
        self.assertIn(
            "never respond to a failed probe by exploring the local environment for an alternative",
            agents,
        )
        self.assertIn(
            "it never suspends the requirement to stop on a probe that has already been "
            "attempted and failed",
            agents,
        )
        self.assertIn("check its `Manual verification rationale` first, before any probe", agents)
        self.assertIn("do not run the probe", agents)

    def test_manual_verification_record_fields_in_completion_and_review_records(self) -> None:
        completion_report = (self.WORKFLOW / "docs/COMPLETION_REPORT_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("Manual verification: `<none | screenshot path", completion_report)
        review_record = (self.WORKFLOW / "docs/REVIEW_RECORD_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn(("manual-verification-record", "1"), self.marker_pairs(review_record))
        self.assertIn("Manual verification observed:", review_record)
        self.assertIn("independently confirms", review_record)

    def test_project_workflow_carries_all_eight_baseline_capabilities(self) -> None:
        text = (self.WORKFLOW / "PROJECT_WORKFLOW.md").read_text(encoding="utf-8")
        pairs = self.marker_pairs(text)
        expected = {
            capability: "1"
            for capability in (
                "workflow-mode-lock",
                "document-precedence",
                "execution-assets",
                "roles",
                "git-workflow",
                "execution-discipline",
            )
        }
        expected["execution-assets"] = "2"
        expected["task-lifecycle"] = "2"
        expected["review-policy"] = "2"
        self.assertEqual(sorted(pairs), sorted(expected.items()))

    def test_whole_file_baseline_capabilities_each_carry_one_marker(self) -> None:
        expectations = {
            "LANGUAGE_POLICY.md": ("language-policy", "2"),
            "tasks/TASK_BLUEPRINT.md": ("task-blueprint", "9"),
            "docs/CODE_ORGANIZATION.md": ("code-organization", "1"),
            "docs/AUDIT_PROMPT_READ_ONLY.md": ("audit-prompt", "1"),
        }
        for name, pair in expectations.items():
            text = (self.WORKFLOW / name).read_text(encoding="utf-8")
            self.assertEqual(self.marker_pairs(text), [pair], name)

    def test_language_policy_marker_excludes_the_per_project_language_line(self) -> None:
        """Corrective migration 013: meridian-init.md replaces
        [Conversation language] with the project's actual choice, so that
        line must sit outside the protected region or every correctly
        initialized project would fail meridian audit on day one."""
        text = (self.WORKFLOW / "LANGUAGE_POLICY.md").read_text(encoding="utf-8")
        match = re.search(
            r"<!-- MERIDIAN:BEGIN capability=language-policy v2 -->\n?(.*?)"
            r"<!-- MERIDIAN:END -->",
            text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertNotIn("[Conversation language]", match.group(1))

    def test_agents_and_claude_carry_the_five_residual_capabilities(self) -> None:
        residual = (
            "command-triggers",
            "review-mode-boundary",
            "owner-acceptance-workflow",
            "implementer-reviewer-handoff",
            "reviewer-integrator-identity",
        )
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.WORKFLOW / name).read_text(encoding="utf-8")
            pairs = self.marker_pairs(text)
            for capability in residual:
                self.assertIn((capability, "1"), pairs, f"{name}: {capability}")

    def test_review_mode_boundary_has_no_hardcoded_review_record_path(self) -> None:
        text = (self.WORKFLOW / "AGENTS.md").read_text(encoding="utf-8")
        match = re.search(
            r"<!-- MERIDIAN:BEGIN capability=review-mode-boundary v1 -->\n?(.*?)"
            r"<!-- MERIDIAN:END -->",
            text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertNotIn("tasks/reviews/<TASK-ID>.md", match.group(1))


class DuplicateHeadingAuditTest(unittest.TestCase):
    """`audit_duplicate_headings` (task 007's duplication-detection half):
    flags a capability whose marker sits under more than one distinct
    heading within the same managed file -- the mechanical signature of an
    accidental duplicate paste. Scoped to one file at a time: the same
    capability legitimately appears under different heading names across
    different consuming documents by design.
    """

    def test_real_templates_have_no_within_file_duplicate_headings(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name) / "project"
        source = ROOT / "templates" / "workflows" / "governed-sdd"
        for path in source.rglob("*"):
            if path.is_file():
                destination = project / path.relative_to(source)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        results = meridian.audit_duplicate_headings(project, ROOT, "governed-sdd")
        self.assertEqual(results, [])

    def test_flags_a_capability_duplicated_under_two_headings_in_one_file(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name) / "project"
        project.mkdir(parents=True)
        (project / "PROJECT_WORKFLOW.md").write_text(
            "## First section\n\n"
            "<!-- MERIDIAN:BEGIN capability=dup-rule v1 -->\ntext.\n<!-- MERIDIAN:END -->\n\n"
            "## Second section\n\n"
            "<!-- MERIDIAN:BEGIN capability=dup-rule v1 -->\ntext.\n<!-- MERIDIAN:END -->\n",
            encoding="utf-8",
        )

        class FakeManagedFile:
            def __init__(self, target: Path) -> None:
                self.target = target
                self.source = project / target

        original = meridian.managed_files
        meridian.managed_files = lambda framework_root, mode: [FakeManagedFile(Path("PROJECT_WORKFLOW.md"))]
        try:
            results = meridian.audit_duplicate_headings(project, ROOT, "governed-sdd")
        finally:
            meridian.managed_files = original
        self.assertEqual(len(results), 1)
        status, message = results[0]
        self.assertEqual(status, "FAIL")
        self.assertIn("dup-rule", message)
        self.assertIn("First section", message)
        self.assertIn("Second section", message)

    def test_does_not_flag_the_same_capability_under_the_same_heading_name_across_files(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name) / "project"
        project.mkdir(parents=True)
        for name in ("AGENTS.md", "CLAUDE.md"):
            (project / name).write_text(
                "## Command triggers\n\n"
                "<!-- MERIDIAN:BEGIN capability=command-triggers v1 -->\ntext.\n<!-- MERIDIAN:END -->\n",
                encoding="utf-8",
            )

        class FakeManagedFile:
            def __init__(self, target: Path) -> None:
                self.target = target
                self.source = project / target

        original = meridian.managed_files
        meridian.managed_files = lambda framework_root, mode: [
            FakeManagedFile(Path("AGENTS.md")),
            FakeManagedFile(Path("CLAUDE.md")),
        ]
        try:
            results = meridian.audit_duplicate_headings(project, ROOT, "governed-sdd")
        finally:
            meridian.managed_files = original
        self.assertEqual(results, [])


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
