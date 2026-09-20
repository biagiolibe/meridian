"""Decision-table and structural tests for Meridian's Codex rules template."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "templates/workflows/governed-sdd/.codex/rules/meridian.rules"
PREFIX_RULE = re.compile(
    r'^prefix_rule\(pattern=\[[^\n]+\], decision="(allow|prompt|forbidden)"\)$'
)
sys.path.insert(0, str(ROOT / "scripts"))
import meridian  # noqa: E402


class CodexRulesTemplateTest(unittest.TestCase):
    def test_rules_are_managed_for_governed_sdd_only(self) -> None:
        governed = {
            item.target
            for item in meridian.managed_files(ROOT, "governed-sdd")
        }
        lean = {item.target for item in meridian.managed_files(ROOT, "lean-delivery")}
        self.assertIn(Path(".codex/rules/meridian.rules"), governed)
        self.assertNotIn(Path(".codex/rules/meridian.rules"), lean)

    def test_prefix_rules_are_single_line_and_well_formed(self) -> None:
        lines = RULES.read_text(encoding="utf-8").splitlines()
        rules = [line for line in lines if line.startswith("prefix_rule(")]
        self.assertGreaterEqual(len(rules), 9)
        for line in rules:
            self.assertRegex(line, PREFIX_RULE)
            self.assertNotIn("\n", line)

    @unittest.skipUnless(shutil.which("codex"), "codex is not on PATH; cannot evaluate execpolicy decisions")
    def test_decision_table_with_codex_execpolicy(self) -> None:
        # Each row is an evidence-table command and its expected final policy.
        # None means an empty matchedRules array: Codex uses its normal prompt.
        cases = [
            (["git", "switch", "m30-present-001"], "allow"),
            (["git", "switch", "-c", "m30-verify"], "allow"),
            (["git", "rev-parse", "main"], "allow"),
            (["git", "rev-parse", "--short", "HEAD"], "allow"),
            (["git", "merge-base", "--is-ancestor", "main", "x"], "allow"),
            (["git", "merge", "--ff-only", "x"], "allow"),
            (["git", "merge", "--no-ff", "x"], None),
            (["git", "commit", "-m", "x"], "allow"),
            (["git", "commit", "--author=override", "-m", "y"], None),
            (["git", "commit", "--amend", "-m", "x"], None),
            (["git", "push", "-u", "origin", "x"], "allow"),
            (["git", "push", "origin", "main"], "allow"),
            (["git", "push", "--force", "origin", "main"], "forbidden"),
            (["git", "push", "-f", "origin", "main"], "forbidden"),
            (["git", "push", "--force-with-lease", "origin", "main"], "forbidden"),
            (["git", "push", "--delete", "origin", "old"], "forbidden"),
            (["git", "push", "--mirror", "origin"], "forbidden"),
            (["git", "branch", "-d", "x"], "allow"),
            (["git", "branch", "--show-current"], "allow"),
            (["git", "branch", "-D", "x"], "prompt"),
            (["git", "branch", "--delete", "x"], "prompt"),
            (["git", "branch", "--force", "x"], "prompt"),
            (["meridian", "execution", "validate", "TASK-040"], "allow"),
            (["meridian", "context", "authority", "TASK-040"], "allow"),
            (["meridian", "execution", "reconcile"], None),
            (["meridian", "upgrade", "--project", "."], None),
            (["git", "rebase", "main"], None),
            (["git", "reset", "--hard", "HEAD~1"], None),
            (["git", "fetch", "origin"], None),
            (["git", "-C", "/tmp/project", "status"], None),
        ]
        for command, expected in cases:
            with self.subTest(command=command):
                result = subprocess.run(
                    ["codex", "execpolicy", "check", "--rules", str(RULES), "--", *command],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                actual = json.loads(result.stdout).get("decision")
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
