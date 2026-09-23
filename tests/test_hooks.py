#!/usr/bin/env python3
"""Checks for the two hooks, with Grok-shaped and Claude-shaped payloads."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / ".claude" / "hooks" / "guard_approved.py"
APPROVE = REPO / ".claude" / "hooks" / "approve.py"


def run(script: Path, event: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script)], input=json.dumps(event),
                          capture_output=True, text=True, check=False)


def grok(tool: str, tool_input: dict) -> dict:
    return {"toolName": tool, "toolInput": tool_input}


def claude(tool: str, tool_input: dict) -> dict:
    return {"tool_name": tool, "tool_input": tool_input}


class Guard(unittest.TestCase):
    def assert_denied(self, event: dict, words: str) -> None:
        result = run(GUARD, event)
        self.assertEqual(result.returncode, 2, event)
        self.assertIn(words, result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "deny")

    def assert_allowed(self, event: dict) -> None:
        self.assertEqual(run(GUARD, event).returncode, 0, event)

    def test_marker_writes_denied_in_both_tools(self) -> None:
        for make, shell, edit in ((grok, "run_terminal_command", "search_replace"), (claude, "Bash", "Write")):
            self.assert_denied(make(shell, {"command": "touch drafts/x/APPROVED"}), "operator typing")
            self.assert_denied(make(shell, {"command": "cd drafts/x && touch APPROVED"}), "operator typing")
            self.assert_denied(make(shell, {"command": "echo ok > drafts/x/APPROVED"}), "operator typing")
            self.assert_denied(make(shell, {"command": "rm drafts/x/APPROVED"}), "operator typing")
            self.assert_denied(make(shell, {"command": 'grok -p "/approve smart-tv"'}), "operator typing")
            self.assert_denied(make(shell, {"command": 'claude -p "/approve smart-tv"'}), "operator typing")
            self.assert_denied(make(edit, {"file_path": "drafts/x/APPROVED", "content": ""}), "operator typing")

    def test_loop_state_edits_denied_for_edit_tools(self) -> None:
        for make, edit in ((grok, "search_replace"), (claude, "Edit"), (claude, "Write")):
            for path in ("loop/state.json", "ledger/2102194978269389269.json", "ledger/SUMMARY.md",
                         "experiments.md", "/Users/x/src/thread-engine/learnings.md"):
                self.assert_denied(make(edit, {"file_path": path, "old_string": "a", "new_string": "b"}),
                                   "scripts/loop.py")

    def test_prose_mentions_stay_editable(self) -> None:
        self.assert_allowed(claude("Edit", {"file_path": "AGENTS.md", "old_string": "x",
                                            "new_string": "Never edit APPROVED or loop/state.json by hand."}))
        self.assert_allowed(claude("Bash", {"command": "python3 - <<'X'\nprint('APPROVED is absent')\nX"}))
        self.assert_allowed(claude("Bash", {"command": "python3 - <<'X'\ns = '`.claude/hooks/` — `/approve` hook'\nX"}))
        self.assert_denied(claude("Bash", {"command": '$HOME/.grok/bin/grok --effort low "/approve x"'}),
                           "operator typing")
        self.assert_allowed(grok("search_replace", {"file_path": ".claude/skills/format-settings/checklist.md",
                                                    "new_string": "- [ ] APPROVED is absent"}))

    def test_normal_work_allowed(self) -> None:
        self.assert_allowed(claude("Bash", {"command": "python3 scripts/loop.py status"}))
        self.assert_allowed(claude("Bash", {"command": "python3 scripts/post_thread.py drafts/2026-09-22-smart-tv"}))
        self.assert_allowed(claude("Read", {"file_path": "drafts/x/APPROVED"}))
        self.assert_allowed(grok("read_file", {"path": "loop/state.json"}))
        self.assert_allowed(claude("Edit", {"file_path": "drafts/x/01-hook.md", "old_string": "a", "new_string": "b"}))


class Approve(unittest.TestCase):
    def test_typed_approve_writes_digest_and_blocks_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "scripts" / "post_thread.py").write_text((REPO / "scripts" / "post_thread.py").read_text())
            draft = root / "drafts" / "2026-10-01-demo"
            draft.mkdir(parents=True)
            (draft / "01-hook.md").write_text("A result.\n")
            for event in ({"prompt": "/approve demo", "workspaceRoot": tmp},    # Grok
                          {"prompt": "/approve demo", "cwd": tmp}):             # Claude Code
                result = run(APPROVE, event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["decision"], "block")
                self.assertIn("cards-sha256:", (draft / "APPROVED").read_text())
                (draft / "APPROVED").unlink()

    def test_other_prompts_pass_through(self) -> None:
        result = run(APPROVE, {"prompt": "please approve my draft", "cwd": "."})
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
