#!/usr/bin/env python3
"""Run Meridian's unittest suite in deterministic, disjoint shards."""

from __future__ import annotations

import argparse
import hashlib
import sys
import unittest
from collections.abc import Iterable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS_DIRECTORY = ROOT / "tests"


def iter_tests(suite: unittest.TestSuite) -> Iterable[unittest.TestCase]:
    """Yield individual test cases from a possibly nested unittest suite."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def discover_tests(tests_directory: Path = TESTS_DIRECTORY) -> list[unittest.TestCase]:
    """Discover tests and return them sorted by their stable unittest id."""
    discovered = unittest.defaultTestLoader.discover(str(tests_directory))
    return sorted(iter_tests(discovered), key=lambda test: test.id())


def coverage(tests: list[unittest.TestCase]) -> tuple[int, str]:
    """Return the test count and SHA-256 proof for a sorted test list."""
    identifiers = "\n".join(test.id() for test in tests)
    return len(tests), hashlib.sha256(identifiers.encode("utf-8")).hexdigest()


def parse_shard(value: str) -> tuple[int, int]:
    """Parse a one-based shard I/N, rejecting invalid bounds."""
    try:
        index_text, count_text = value.split("/", 1)
        index = int(index_text)
        count = int(count_text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("shard must be I/N with positive integers") from error
    if index < 1 or count < 1 or index > count:
        raise argparse.ArgumentTypeError("shard must be I/N where 1 <= I <= N")
    return index, count


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    group = argument_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--shard", type=parse_shard, metavar="I/N")
    group.add_argument("--list", action="store_true", help="print coverage without running tests")
    return argument_parser


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    tests = discover_tests()
    total, digest = coverage(tests)
    if options.list:
        print(f"total={total} digest={digest}", flush=True)
        return 0

    index, count = options.shard
    selected = [test for position, test in enumerate(tests) if position % count == index - 1]
    print(
        f"shard={index}/{count} total={total} selected={len(selected)} digest={digest}",
        flush=True,
    )
    if not selected:
        parser().error(f"shard {index}/{count} selects no tests")
    return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected)).wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
