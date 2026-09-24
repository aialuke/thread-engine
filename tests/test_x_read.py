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
    def call(self, argv, reader, lookup=lambda ids: []):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = x_read.main(argv, reader=reader, lookup=lookup)
        return code, out.getvalue(), err.getvalue()

    def test_search_adds_query_limit_and_cost(self) -> None:
        prompts = []
        reader = lambda prompt, schema: (prompts.append(prompt) or ({"posts": [], "error": None}, 0.05))
        code, out, _ = self.call(["search", '"how do I" free editor'], reader)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual((data["query"], data["limit"], data["cost_usd"]), ('"how do I" free editor', 10, 0.05))
        self.assertIn('"how do I" free editor', prompts[0])

    def test_invented_and_misquoted_posts_are_dropped_and_real_ones_use_x_data(self) -> None:
        grok_posts = [
            {"id": "2102736605039776235", "author": "someone", "created_at": None,
             "text": "Got 13 premium followers in 24 hours by replying properly", "metrics": {"views": 99999}},
            {"id": "2102145678901234567", "author": "creatorpayouts", "created_at": None,
             "text": "$42 for a thread", "metrics": {}},
            {"id": "2102000000000000001", "author": "real", "created_at": None,
             "text": "Something Grok made up about this post", "metrics": {}},
        ]
        real = {"2102736605039776235": {"id": "2102736605039776235", "author": "sidchhaya",
                                        "created_at": "2026-09-23T12:00:00.000Z",
                                        "text": "Got 13 Premium followers in 24 hours by replying properly. Thread:",
                                        "public_metrics": {"impression_count": 1200, "like_count": 30}},
                "2102000000000000001": {"id": "2102000000000000001", "author": "real",
                                        "text": "A completely different real post about cameras",
                                        "public_metrics": {}}}
        seen = []
        lookup = lambda ids: (seen.append(ids), [real[i] for i in ids if i in real])[1]
        code, out, _ = self.call(["search", "premium followers"],
                                 lambda p, s: ({"posts": grok_posts, "error": None}, 0.08), lookup)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual([p["id"] for p in data["posts"]], ["2102736605039776235"])
        kept = data["posts"][0]
        self.assertEqual((kept["author"], kept["metrics"]["views"], kept["verified"]), ("sidchhaya", 1200, True))
        reasons = {d["id"]: d["reason"] for d in data["dropped"]}
        self.assertEqual(reasons, {"2102145678901234567": "X has no such post",
                                   "2102000000000000001": "text does not match the real post"})
        self.assertEqual(len(seen), 1)

    def test_nothing_returned_when_the_check_cannot_run(self) -> None:
        def lookup(ids):
            raise x_read.x_api.XApiError("Keychain has no consumer_key")
        code, out, err = self.call(["search", "q"],
                                   lambda p, s: ({"posts": [{"id": "2102736605039776235", "text": "x"}], "error": None}, 0.08),
                                   lookup)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("none are returned", err)

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
