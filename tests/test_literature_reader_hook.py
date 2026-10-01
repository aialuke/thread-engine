#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "literature_reader_write.py"


def run(file_path: str) -> subprocess.CompletedProcess:
    event = {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                          capture_output=True, text=True, check=False)


class LiteratureReaderWrite(unittest.TestCase):
    def test_scratchpad_report_allowed(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            path = Path(tmp) / "session" / "scratchpad" / "reader.md"
            self.assertEqual(run(str(path)).returncode, 0)

    def test_new_research_report_allowed(self):
        self.assertEqual(run(str(REPO / "research" / "no-such-report-xyz.md")).returncode, 0)

    def test_existing_research_file_refused(self):
        result = run(str(REPO / "research" / "jev-design-cards-reading" / "README.md"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("already exists", result.stderr)

    def test_repo_file_outside_research_refused(self):
        for target in ("AGENTS.md", "scripts/new.md", "loop/state.md", ".claude/agents/x.md"):
            self.assertEqual(run(str(REPO / target)).returncode, 2, target)

    def test_non_markdown_refused(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
            self.assertEqual(run(str(Path(tmp) / "scratchpad" / "x.py")).returncode, 2)
        self.assertEqual(run(str(REPO / "research" / "x.json")).returncode, 2)

    def test_tmp_outside_scratchpad_refused(self):
        self.assertEqual(run("/tmp/elsewhere/report.md").returncode, 2)

    def test_dotdot_escape_refused(self):
        self.assertEqual(run(str(REPO / "research" / ".." / "AGENTS.md")).returncode, 2)

    def test_missing_path_refused(self):
        event = {"tool_name": "Write", "tool_input": {}}
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
