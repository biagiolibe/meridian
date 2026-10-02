"""Tests for the deterministic sharded unittest runner."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_tests.py"
SPEC = importlib.util.spec_from_file_location("run_tests", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class ShardedTestRunnerTest(unittest.TestCase):
    def make_suite(self, names: list[str]) -> Path:
        directory = Path(tempfile.mkdtemp())
        for name in names:
            (directory / f"test_{directory.name}_{name}.py").write_text(
                "import unittest\n"
                "class GeneratedTest(unittest.TestCase):\n"
                "    def test_value(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
        return directory

    def run_script(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_shards_are_disjoint_and_cover_the_generated_suite(self) -> None:
        directory = self.make_suite(["gamma", "alpha", "beta", "delta", "epsilon"])
        self.addCleanup(lambda: __import__("shutil").rmtree(directory))
        tests = runner.discover_tests(directory)
        identifiers = [test.id() for test in tests]
        shards = [
            {test.id() for position, test in enumerate(tests) if position % 3 == shard}
            for shard in range(3)
        ]

        self.assertEqual(identifiers, sorted(identifiers))
        self.assertEqual(set().union(*shards), set(identifiers))
        self.assertEqual(sum(len(shard) for shard in shards), len(identifiers))

    def test_adding_a_test_changes_the_digest(self) -> None:
        directory = self.make_suite(["first"])
        self.addCleanup(lambda: __import__("shutil").rmtree(directory))
        _, original = runner.coverage(runner.discover_tests(directory))
        (directory / f"test_{directory.name}_second.py").write_text(
            "import unittest\nclass Extra(unittest.TestCase):\n    def test_value(self): pass\n",
            encoding="utf-8",
        )
        _, changed = runner.coverage(runner.discover_tests(directory))

        self.assertNotEqual(original, changed)

    def test_coverage_uses_newline_joined_sorted_ids(self) -> None:
        directory = self.make_suite(["zeta", "alpha"])
        self.addCleanup(lambda: __import__("shutil").rmtree(directory))
        tests = runner.discover_tests(directory)
        expected = hashlib.sha256("\n".join(test.id() for test in tests).encode()).hexdigest()

        self.assertEqual(runner.coverage(tests), (2, expected))

    def test_list_prints_coverage_without_running_tests(self) -> None:
        result = self.run_script("--list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^total=\d+ digest=[0-9a-f]{64}\n$")
        self.assertEqual(result.stderr, "")

    def test_invalid_shards_exit_with_usage_status(self) -> None:
        for shard in ("0/4", "5/4", "a/b"):
            with self.subTest(shard=shard):
                result = self.run_script("--shard", shard)
                self.assertEqual(result.returncode, 2)
                self.assertIn("usage:", result.stderr)
        missing = self.run_script("--shard")
        self.assertEqual(missing.returncode, 2)
        self.assertIn("usage:", missing.stderr)

    def test_empty_shard_exits_with_status_two(self) -> None:
        result = self.run_script("--shard", "999/999")

        self.assertEqual(result.returncode, 2)
        self.assertIn("selects no tests", result.stderr)
        self.assertRegex(result.stdout, r"^shard=999/999 total=\d+ selected=0 digest=[0-9a-f]{64}\n$")
