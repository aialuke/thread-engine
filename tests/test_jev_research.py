#!/usr/bin/env python3
"""Runs the checks that live beside the Jev research scripts (research/jev-test/test_*.py),
so `python3 -m unittest discover -s tests` covers them. They pin sentences in skill files by
line number, so they fail whenever a skill edit moves one."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent.parent / "research" / "jev-test"


def load_tests(loader: unittest.TestLoader, tests: unittest.TestSuite, pattern: str | None) -> unittest.TestSuite:
    if str(RESEARCH) not in sys.path:
        sys.path.insert(0, str(RESEARCH))
    suite = unittest.TestSuite()
    for path in sorted(RESEARCH.glob("test_*.py")):
        suite.addTests(loader.loadTestsFromName(path.stem))
    return suite


if __name__ == "__main__":
    unittest.main()
