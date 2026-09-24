#!/usr/bin/env python3
"""Checks for scripts/grok_read.py and scripts/x_read.py with a fake runner. No network."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import grok_read  # noqa: E402
import x_read  # noqa: E402


class GrokRead(unittest.TestCase):
    def test_runs_read_only_and_returns_final_object_and_cost(self) -> None:
        seen = {}

        def runner(cmd, **kwargs):
            seen["cmd"] = cmd
            text = '{"posts": [], "error": "pending"} {"posts": [{"id": "1"}], "error": null}'
            return subprocess.CompletedProcess(cmd, 0, json.dumps({"text": text, "total_cost_usd": 0.08}), "")

        data, cost = grok_read.run_structured("prompt", {"type": "object"}, runner=runner)
        self.assertEqual((data["posts"], cost), ([{"id": "1"}], 0.08))
        cmd = seen["cmd"]
        self.assertEqual(cmd[cmd.index("--sandbox") + 1], "read-only")
        denied = [cmd[i + 1] for i, part in enumerate(cmd) if part == "--deny"]
        self.assertEqual(sorted(denied), ["Bash", "Edit", "Write"])

    def test_last_json_object_takes_final_complete_object(self) -> None:
        text = '{"posts": [{"root_id": "1", "error": "pending"}]} partial {"posts": []}'
        self.assertEqual(grok_read.last_json_object(text), {"posts": []})

    def test_nonzero_exit_raises(self) -> None:
        runner = lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "", "auth expired")
        with self.assertRaises(RuntimeError):
            grok_read.run_structured("p", {}, runner=runner)


class XRead(unittest.TestCase):
    def call(self, argv, reader):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = x_read.main(argv, reader=reader)
        return code, out.getvalue(), err.getvalue()

    def test_search_adds_query_limit_and_cost(self) -> None:
        prompts = []
        reader = lambda prompt, schema: (prompts.append(prompt) or ({"posts": [], "error": None}, 0.05))
        code, out, _ = self.call(["search", '"how do I" free editor'], reader)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual((data["query"], data["limit"], data["cost_usd"]), ('"how do I" free editor', 10, 0.05))
        self.assertIn('"how do I" free editor', prompts[0])

    def test_thread_rejects_bad_id_without_calling_grok(self) -> None:
        calls = []
        code, _, err = self.call(["thread", "abc"], lambda p, s: calls.append(p))
        self.assertEqual((code, calls), (1, []))
        self.assertIn("bad post id", err)

    def test_grok_failure_is_reported_not_raised(self) -> None:
        def reader(prompt, schema):
            raise RuntimeError("grok exited 1")
        code, out, err = self.call(["thread", "2102194978269389269"], reader)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("grok exited 1", err)


if __name__ == "__main__":
    unittest.main()
