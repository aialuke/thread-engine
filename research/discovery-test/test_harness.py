#!/usr/bin/env python3
"""Offline checks for harness.py: fake opener, fake Grok runner. No network, no Keychain.

    python3 -m unittest discover -s research/discovery-test -p 'test_harness.py'
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harness  # noqa: E402

KEYS = {"consumer_key": "CK-SECRET-VALUE", "consumer_secret": "CS-SECRET-VALUE",
        "access_token": "AT-SECRET-VALUE", "access_token_secret": "ATS-SECRET-VALUE"}
NOW = datetime(2026, 9, 27, 2, 0, tzinfo=timezone.utc)          # 12:00 Brisbane
RATE = {"x-rate-limit-limit": "450", "x-rate-limit-remaining": "449", "x-rate-limit-reset": "1790000000",
        "x-access-level": "read"}


def post(pid: str, text: str, minutes_ago: int = 30, author_id: str = "77") -> dict:
    return {"id": pid, "text": text, "author_id": author_id, "created_at": harness.iso(NOW - timedelta(minutes=minutes_ago)),
            "public_metrics": {"like_count": 6, "reply_count": 1}}


class FakeResponse:
    def __init__(self, body: dict, headers: dict | None = None) -> None:
        self.body, self.headers = body, dict(RATE if headers is None else headers)

    def read(self) -> bytes:
        return json.dumps(self.body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


class Router:
    """Answers by path. A handler returns a body dict, or an int to raise that HTTP status."""

    def __init__(self, **routes) -> None:
        self.routes, self.requests = routes, []

    def __call__(self, req, timeout=30):
        self.requests.append(req)
        path = urlsplit(req.full_url).path
        query = {k: v[0] for k, v in parse_qs(urlsplit(req.full_url).query).items()}
        for prefix, handler in self.routes.items():
            if path.startswith(prefix.replace("_", "/")):
                reply = handler(query) if callable(handler) else handler
                if isinstance(reply, int):
                    raise urllib.error.HTTPError(req.full_url, reply, "err", RATE,
                                                 io.BytesIO(json.dumps({"errors": [{"message": f"bad {reply}"}]}).encode()))
                return FakeResponse(reply)
        raise AssertionError(f"no route for {path}")


def stream(*events) -> str:
    return "\n".join(json.dumps(e) for e in events)


TOOL_TEXT = """TOOL: x_semantic_search
Main Post:
- [post:0] ID: 2103752357758787700
- Conversation ID: 2103752357758787700
- Author: Someone - @someone
- Timestamp: Sun, 27 Sep 2026 01:00:00 GMT
- Engagement: Likes=3, Views=40
- Content: Is there a free alternative to Premiere? Asking for a friend

---

Main Post:
- [post:1] ID:
- Engagement: Likes=0, Views=N/A
- Content: (No text content)

---

Main Post:
- [post:2] ID: 2103752341170315456
- Conversation ID: 2103745492480045538
- Author: Other - @other
- Timestamp: Sun, 27 Sep 2026 01:30:00 GMT
- Content: A completely different sentence Grok retyped

---

Main Post:
- [post:3] ID: 2103752332261630282
- Author: Ghost - @ghost
- Timestamp: Sun, 20 Sep 2026 09:03:35 GMT
- Content: made up
"""


def ok_stream(tool_text: str = TOOL_TEXT, closing: str = "") -> str:
    return stream({"type": "tool_call", "toolCallId": "c1", "toolName": "x_semantic_search", "kind": "search",
                   "rawInput": {"query": "free alternative", "limit": 10}, "status": "in_progress"},
                  {"type": "tool_call_update", "toolCallId": "c1", "status": "completed", "rawOutput": tool_text},
                  {"type": "text", "data": "Here are the posts. " + closing},
                  {"type": "end", "stopReason": "end_turn", "num_turns": 3,
                   "usage": {"input_tokens": 1000, "output_tokens": 200},
                   "modelUsage": {"grok-4.7": {"inputTokens": 1000}, "grok-4.5": {"inputTokens": 50}},
                   "total_cost_usd": 0.04})


class FakeGrok:
    def __init__(self, *replies) -> None:
        self.replies, self.calls = list(replies), []

    def __call__(self, cmd, **kw):
        if cmd[1:] == ["--version"]:
            return subprocess.CompletedProcess(cmd, 0, "grok 1.0.41 (test)", "")
        self.calls.append((cmd, kw))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        code, out, err = reply
        return subprocess.CompletedProcess(cmd, code, out, err)


def lookup_route(known: dict):
    def handler(q):
        ids = q["ids"].split(",")
        return {"data": [known[i] for i in ids if i in known],
                "errors": [{"resource_id": i, "title": "Not Found Error"} for i in ids if i not in known]}
    return handler


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "private"
        self.live = Path(self.tmp.name) / "live"
        self.live.mkdir()
        self.now = NOW

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make(self, router: Router, grok: FakeGrok | None = None) -> harness.Harness:
        self.store = harness.Store(self.root)
        clock = lambda: self.now
        client = harness.LoggedClient(self.store, keys=KEYS, opener=router, sleep=lambda s: None, clock=clock)
        runner = harness.GrokRunner(self.store, runner=grok or FakeGrok(), clock=clock, binary=Path("/fake/grok"),
                                    cwd_root=Path(self.tmp.name) / "grok-cwd")
        return harness.Harness(self.store, client, runner, clock=clock, live_folder=self.live)

    def all_private_text(self) -> str:
        return "".join(p.read_text(encoding="utf-8", errors="replace") for p in self.root.rglob("*") if p.is_file())


class XLayer(Base):
    def test_refuses_anything_but_get_before_sending(self) -> None:
        router = Router()
        h = self.make(router)
        for method in ("POST", "DELETE"):
            with self.assertRaises(harness.x_api.XApiError):
                h.client.request(method, "/2/tweets", {}, 0.0)
        self.assertEqual(router.requests, [])

    def test_every_call_logged_with_observability_fields_and_raw_body(self) -> None:
        body = {"data": [post("1", "free alternative please")], "meta": {"result_count": 1, "newest_id": "1"}}
        h = self.make(Router(_2_tweets_search_recent=body))
        h.run_pilot_step("P1")
        row = self.store.rows(self.store.requests)[0]
        for field in ("call_id", "time_utc", "stage", "step", "source", "endpoint", "params", "status", "latency_ms",
                      "rate_limit", "access_level", "result_count", "meta", "items", "estimated_cost", "raw_path"):
            self.assertIn(field, row)
        self.assertEqual((row["stage"], row["step"], row["status"], row["rate_limit"]["remaining"]), ("pilot", "P1", 200, "449"))
        self.assertEqual(row["estimated_cost"], 0.005)
        self.assertEqual(json.loads((self.root / row["raw_path"]).read_text()), body)
        self.assertIn("min_likes:5", row["params"]["query"])

    def test_rejected_request_is_logged_and_returned_not_raised(self) -> None:
        calls = []
        def search(q):
            calls.append(q["query"])
            return 400 if "min_likes" in q["query"] else {"data": [post("1", "x")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=search))
        # 400 body mentions no min_likes here, so P1 stops as failed-x and says why
        result = h.run_pilot_step("P1")
        self.assertEqual(result["status"], "failed-x")
        row = self.store.rows(self.store.requests)[0]
        self.assertEqual((row["status"], row["estimated_cost"]), (400, 0.0))
        self.assertIn("bad 400", json.dumps(row["error_body"]))

    def test_p1_reruns_without_min_likes_when_that_operator_is_rejected(self) -> None:
        def search(q):
            if "min_likes" in q["query"]:
                raise_body = {"errors": [{"message": "min_likes is not a valid operator"}]}
                return raise_body
            return {"data": [post("1", "x")], "meta": {"result_count": 1}}
        # emulate the 400 with a min_likes message
        class R(Router):
            def __call__(self, req, timeout=30):
                q = parse_qs(urlsplit(req.full_url).query)["query"][0]
                if "min_likes" in q:
                    self.requests.append(req)
                    raise urllib.error.HTTPError(req.full_url, 400, "bad", RATE, io.BytesIO(
                        b'{"errors":[{"message":"min_likes is not available"}]}'))
                return super().__call__(req, timeout)
        h = self.make(R(_2_tweets_search_recent=search))
        result = h.run_pilot_step("P1")
        self.assertEqual(result["status"], "done")
        self.assertEqual(len(result["calls"]), 2)
        self.assertNotIn("min_likes", self.store.progress()["settings"]["p1_query"])

    def test_budget_gate_refuses_before_sending_and_logs_it(self) -> None:
        router = Router(_2_tweets=lookup_route({}))
        h = self.make(router)
        self.store.append(self.store.requests, {"stage": "pilot", "estimated_cost": 2.46})
        with self.assertRaisesRegex(harness.Stop, "Pilot ceiling"):
            h.client.get("/2/tweets", {"ids": "1"}, kind="posts", reserve=0.05, stage="pilot", step="t")
        self.assertEqual(router.requests, [])
        self.assertIn("REFUSED", self.store.budget.read_text())
        self.store.append(self.store.requests, {"stage": "stage1", "estimated_cost": harness.X_CHECKPOINT - 2.46 - 0.005})
        with self.assertRaisesRegex(harness.Stop, "checkpoint"):
            h.client.get("/2/tweets", {"ids": "1"}, kind="posts", reserve=0.01, stage="stage2", step="t")

    def test_quiet_hour_refuses(self) -> None:
        h = self.make(Router())
        self.now = datetime(2026, 9, 27, 9, 45, tzinfo=timezone.utc)      # 19:45 Brisbane
        with self.assertRaisesRegex(harness.Stop, "19:30"):
            h.run_pilot_step("P0")
        self.assertEqual(self.store.progress()["steps"]["P0"]["status"], "pending")

    def test_p2_warns_when_not_the_same_utc_day_as_p1(self) -> None:
        body = {"data": [post("1", "x")], "includes": {"users": [{"id": "77", "username": "a"}]}, "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=body))
        self.now = datetime(2026, 9, 26, 23, 50, tzinfo=timezone.utc)     # 09:50 Brisbane
        h.run_pilot_step("P1")
        self.now = datetime(2026, 9, 27, 0, 10, tzinfo=timezone.utc)      # 10:10 Brisbane: new UTC day
        result = h.run_pilot_step("P2")
        self.assertIn("not the same UTC day", result["warning"])
        self.assertEqual(result["repeat_of_p1"], 1)
        self.assertEqual(self.store.rows(self.store.requests)[-1]["estimated_cost"], 0.015)

    def test_no_secret_reaches_any_private_file(self) -> None:
        body = {"data": [post("1", "x")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=body, _2_usage=403))
        h.run_pilot_step("P0")
        h.run_pilot_step("P1")
        text = self.all_private_text()
        for value in KEYS.values():
            self.assertNotIn(value, text)
        self.assertNotIn("oauth_signature", text)

    def test_usage_probe_403_is_an_answer_not_a_failure(self) -> None:
        h = self.make(Router(_2_usage=403))
        result = h.run_pilot_step("P0")
        self.assertEqual((result["status"], result["http"]), ("done", 403))
        self.assertIn("not with these keys", result["answer_hint"])

    def test_p5_lengths_are_exact_and_longest_first(self) -> None:
        seen = []
        h = self.make(Router(_2_tweets_search_recent=lambda q: (seen.append(len(q["query"])), 400)[1]))
        h.run_pilot_step("P5")
        self.assertEqual(seen, [4097, 1025, 513])


class GrokLayer(Base):
    def setUp(self) -> None:
        super().setUp()
        self.known = {"2103752357758787700": post("2103752357758787700", "Is there a free alternative to Premiere? Asking for a friend", 60),
                      "2103752341170315456": post("2103752341170315456", "The real text says something else entirely here", 30)}

    def configured(self, grok: FakeGrok) -> harness.Harness:
        h = self.make(Router(_2_tweets=lookup_route(self.known)), grok)
        data = self.store.progress()
        data["settings"]["model"] = "grok-4.7"
        self.store.save_progress(data)
        return h

    def test_parse_slots_keeps_empty_slots_and_ignores_conversation_ids(self) -> None:
        slots = harness.parse_slots(TOOL_TEXT)
        self.assertEqual([s["id"] for s in slots], ["2103752357758787700", None, "2103752341170315456", "2103752332261630282"])
        self.assertEqual(slots[0]["author"], "someone")
        self.assertEqual(slots[0]["created_at"], "2026-09-27T01:00:00Z")
        self.assertTrue(slots[0]["text"].startswith("Is there a free alternative"))
        self.assertEqual(slots[2]["conversation_id"], "2103745492480045538")

    def test_arm_runs_clean_saves_stream_first_and_labels_claims(self) -> None:
        grok = FakeGrok((0, ok_stream(), "some stderr"))
        h = self.configured(grok)
        result = h.run_pilot_step("P7-free")
        self.assertEqual((result["status"], result["claims_from"]), ("done", "tool_output"))
        cmd, kw = grok.calls[0]
        self.assertEqual(kw["env"]["GROK_MEMORY"], "0")
        cwd = Path(kw["cwd"])
        self.assertTrue(str(cwd).startswith(self.tmp.name))
        self.assertNotIn(harness.REPO, cwd.resolve().parents)
        for flag in ("--verbatim", "streaming-json", "read-only", "grok-4.7"):
            self.assertIn(flag, cmd)
        self.assertNotIn("--json-schema", cmd)
        row = self.store.rows(self.store.grok_log)[0]
        saved = self.root / row["saved"]["stdout"]["path"]
        self.assertEqual(saved.read_text(), ok_stream())
        self.assertEqual(row["saved"]["stdout"]["sha256"], harness.hashlib.sha256(ok_stream().encode()).hexdigest())
        self.assertEqual(row["counts"]["slots"], 4)
        self.assertEqual(row["counts"]["numeric_ids"], 3)
        self.assertEqual(row["counts"]["labels"], {"empty_slot": 1, "invented": 1, "misquoted": 1, "real": 1})
        self.assertEqual(row["counts"]["confirmed_in_window"], 1)
        self.assertEqual(row["usage"]["models_seen"], ["grok-4.5", "grok-4.7"])
        self.assertEqual((row["cost_usd"], row["cost_note"]), (0.04, "reported by CLI"))
        self.assertTrue(row["tool_calls"][0]["raw_output_has_posts"])
        self.assertIn("Run at most 3 searches", row["prompt"])
        self.assertIn('"kept"', row["prompt"])
        posts = self.store.load_posts()
        self.assertEqual(json.loads(posts["2103752341170315456"]["labels"]), ["misquoted"])

    def test_falls_back_to_closing_json_when_cli_hides_tool_output(self) -> None:
        closing = json.dumps({"posts": [{"id": "2103752357758787700", "author": "someone", "created_at": None,
                                         "text": "Is there a free alternative to Premiere?"}]})
        out = stream({"type": "tool_call", "toolCallId": "c1", "toolName": "x_keyword_search", "rawInput": {"query": "q"}},
                     {"type": "tool_call_update", "toolCallId": "c1", "status": "completed"},
                     {"type": "text", "data": "Found: " + closing}, {"type": "end", "usage": {"input_tokens": 10}})
        h = self.configured(FakeGrok((0, out, "")))
        result = h.run_pilot_step("P7-steered")
        self.assertEqual(result["claims_from"], "closing_json")
        row = self.store.rows(self.store.grok_log)[0]
        self.assertEqual(row["counts"]["labels"], {"real": 1})
        self.assertFalse(row["tool_calls"][0]["raw_output_has_posts"])
        self.assertIn("estimated", row["cost_note"])
        self.assertIn("within_time:24h", row["prompt"])        # website syntax for Grok's keyword tool
        self.assertNotIn("-is:", row["prompt"])
        self.assertNotIn("lang:", row["prompt"])

    def test_ids_named_only_in_the_answer_are_checked_apart_and_reprocess_is_idempotent(self) -> None:
        closing = json.dumps({"posts": []})
        answer = ("No overlap.\n**2103752357758787700** — @someone — Likes=3\nIs there a free alternative\n"
                  "**2103752332261630282** — @ghost\n" + closing)
        out = stream({"type": "text", "data": answer}, {"type": "end", "total_cost_usd": 0.1})
        h = self.configured(FakeGrok((0, out, "")))
        result = h.run_pilot_step("P7-self")
        self.assertEqual((result["counts"]["slots"], result["counts"]["mentioned_only"]), (0, 2))
        self.assertEqual(result["counts"]["mentioned_only_exist"], 1)
        self.assertEqual(result["counts"]["labels"], {"invented": 1, "mentioned_exists": 1})
        again = h.reprocess(result["run"])
        self.assertEqual(again["new_ids"], 0)

    def test_limit_blocks_step_keeps_partial_and_status_points_to_resume(self) -> None:
        partial = stream({"type": "tool_call", "toolCallId": "c1", "toolName": "x_semantic_search", "rawInput": {}},
                         {"type": "tool_call_update", "toolCallId": "c1", "rawOutput": TOOL_TEXT})
        h = self.configured(FakeGrok((0, ok_stream(), ""), (1, partial, "API error (status 402 Payment Required): Grok Build usage balance exhausted")))
        self.assertEqual(h.run_pilot_step("P7-free")["status"], "done")
        result = h.run_pilot_step("P7-steered")
        self.assertEqual(result["status"], "blocked-grok-limit")
        row = self.store.rows(self.store.grok_log)[1]
        self.assertTrue(row["partial"])
        self.assertEqual(row["counts"]["numeric_ids"], 3)            # what arrived was still checked
        self.assertEqual(self.store.progress()["steps"]["P7-steered"]["status"], "blocked-grok-limit")
        self.assertEqual(h.next_step(), "P0")                        # X-only steps never ran in this test
        text = h.status()
        self.assertIn("blocked-grok-limit", text)
        self.assertIn("usage-limited", text)

    def test_max_turns_is_not_mistaken_for_the_weekly_limit(self) -> None:
        h = self.configured(FakeGrok((1, "", "error_max_turns: agent stopped")))
        self.assertEqual(h.run_pilot_step("P7-free")["status"], "blocked-grok-error")

    def test_pilot_all_stops_at_the_limit_after_x_only_steps(self) -> None:
        body = {"data": [post("1", "x")], "includes": {"users": [{"id": "77", "username": "a"}]}, "meta": {"result_count": 1}}
        router = Router(_2_usage={"data": []}, _2_tweets_search_recent=body, _2_tweets_counts={"data": [{"tweet_count": 3}],
                        "meta": {"total_tweet_count": 3}}, _2_users=body, _2_tweets=lookup_route(self.known))
        (self.live / "S1.raw.txt").write_text(TOOL_TEXT)
        grok = FakeGrok((1, "", "429 Too Many Requests"))
        h = self.make(router, grok)
        data = self.store.progress()
        data["settings"]["model"] = "grok-4.7"
        self.store.save_progress(data)
        out = io.StringIO()
        with redirect_stdout(out):
            code = harness.main(["pilot", "all"], harness=h)
        self.assertEqual(code, 0)
        states = {s: h.step_state(s)["status"] for s in harness.PILOT_ORDER}
        for step in ("P0", "P1", "P1b", "P1c", "P1d", "P2", "P3", "P4", "P5", "P9"):
            self.assertEqual(states[step], "done", step)
        self.assertEqual(states["P7-free"], "blocked-grok-limit")
        self.assertTrue(all(states[s] == "pending" for s in harness.PILOT_ORDER[11:]))
        self.assertEqual(len(grok.calls), 1)                          # no further Grok attempts
        self.assertEqual(h.next_step(), "P7-free")

    def test_resume_after_restart_neither_repeats_calls_nor_double_counts(self) -> None:
        body = {"data": [post("1", "x")], "meta": {"result_count": 1}}
        router = Router(_2_usage={"data": []}, _2_tweets_search_recent=body)
        h = self.make(router)
        h.run_pilot_step("P0")
        h.run_pilot_step("P1")
        spent = self.store.x_spent()
        h2 = self.make(router)                                        # a new session over the same private/
        self.assertEqual(self.store.x_spent(), spent)
        self.assertEqual(h2.next_step(), "P1b")
        with self.assertRaisesRegex(harness.Stop, "--redo"):
            h2.run_pilot_step("P1")
        self.assertEqual(len(router.requests), 2)
        h2.run_pilot_step("P1", redo=True)
        self.assertEqual(len(h2.step_state("P1")["attempts"]), 2)

    def test_grok_checkpoint_stops_before_running(self) -> None:
        grok = FakeGrok()
        h = self.configured(grok)
        self.store.append(self.store.grok_log, {"cost_usd": 2.8})
        with self.assertRaisesRegex(harness.Stop, "Grok checkpoint"):
            h.run_pilot_step("P7-free")
        self.assertEqual(grok.calls, [])

    def test_probe_uses_explicit_utc_dates_and_skips_x_checks_when_tool_output_has_times(self) -> None:
        router = Router(_2_tweets=lookup_route(self.known))
        h = self.make(router, FakeGrok((0, ok_stream(), "")))
        data = self.store.progress()
        data["settings"]["model"] = "grok-4.7"
        self.store.save_progress(data)
        result = h.run_pilot_step("P8-b")
        row = self.store.rows(self.store.grok_log)[0]
        self.assertIn("from_date 2026-09-26, to_date 2026-09-26", row["prompt"])
        self.assertIn("every post the search returned", row["prompt"])
        self.assertEqual(row["probe"]["case"], "single-day-yesterday")
        self.assertEqual(router.requests, [])
        self.assertEqual(result["counts"]["unchecked"], 3)

    def test_posts_table_merges_sightings_from_two_sources(self) -> None:
        body = {"data": [post("2103752357758787700", "Is there a free alternative to Premiere? Asking for a friend", 60)],
                "meta": {"result_count": 1}}
        router = Router(_2_tweets_search_recent=body, _2_tweets=lookup_route(self.known))
        h = self.make(router, FakeGrok((0, ok_stream(), "")))
        data = self.store.progress()
        data["settings"]["model"] = "grok-4.7"
        self.store.save_progress(data)
        h.run_pilot_step("P1")
        h.run_pilot_step("P7-free")
        row = self.store.load_posts()["2103752357758787700"]
        self.assertEqual({s["source"] for s in json.loads(row["sightings"])}, {"K", "G"})
        self.assertEqual(json.loads(row["labels"]), ["x_api", "real"])


class RealStreamShape(unittest.TestCase):
    def test_server_side_x_search_gives_observed_args_not_posts(self) -> None:
        out = stream({"type": "available_commands", "tools": ["web_search"], "commands": ["approve", "compact"]},
                     {"type": "tool_call", "toolCallId": "c", "title": "X search:", "toolName": "X search:",
                      "rawInput": {"variant": "XSearch", "backend": True}},
                     {"type": "tool_call_update", "toolCallId": "c", "status": "completed",
                      "rawOutput": {"call_id": "xs", "name": "x_semantic_search",
                                    "input": "{\"query\":\"q\",\"limit\":\"10\",\"from_date\":\"2026-09-26\"}"}},
                     {"type": "end", "total_cost_usd": 0.01})
        parsed = harness.parse_stream(out)
        call = parsed["tools"][0]
        self.assertEqual((call["observed_tool"], call["observed_args"]["from_date"]), ("x_semantic_search", "2026-09-26"))
        self.assertEqual(parsed["project_skills_loaded"], ["approve"])

    def test_refuses_a_grok_folder_inside_the_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = harness.Store(Path(tmp))
            runner = harness.GrokRunner(store, runner=FakeGrok(), clock=lambda: NOW,
                                        cwd_root=harness.HERE / "private" / "grok-cwd-test")
            with self.assertRaisesRegex(harness.Stop, "inside the repo"):
                runner.run("g1", "p", model="m", effort="high")


class Probes(unittest.TestCase):
    def test_probe_set_separates_the_explanations(self) -> None:
        now = datetime(2026, 9, 26, 10, 40, tzinfo=timezone.utc)
        d, meta_d = harness.probe_prompt("P8-d", now)
        self.assertIn("from_date 2026-09-26, to_date 2026-09-27", d)
        self.assertEqual(meta_d["query"], harness.PROBE_QUERY)
        e, meta_e = harness.probe_prompt("P8-e", now)
        self.assertIn("no from_date or to_date", e)
        self.assertEqual((meta_e["query"], meta_e["from_date"]), (harness.BUSY_QUERY, None))
        f, _ = harness.probe_prompt("P8-f", now)
        self.assertIn(harness.BUSY_QUERY, f)
        self.assertEqual(harness.PILOT_ORDER[-6:], list(harness.PROBES))


class StagesAndScoring(Base):
    def test_demand_stage_reports_each_sort_as_its_own_k_source(self) -> None:
        seen = []
        def search(q):
            seen.append((q["sort_order"], q["query"]))
            return {"data": [post(str(1000 + len(seen)), "is there a free alternative")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=search))
        out = h.run_stage(2, "demand-tech-1", only="K")
        self.assertEqual(sorted(k for k in out if k.startswith("K-")), ["K-recency", "K-relevancy"])
        self.assertEqual(sorted(s for s, _ in seen), ["recency", "recency", "relevancy", "relevancy"])
        sources = {x["source"] for r in self.store.load_posts().values() for x in json.loads(r["sightings"])}
        self.assertEqual(sources, {"K-recency", "K-relevancy"})

    def test_tool_research_spam_query_is_a_separate_source(self) -> None:
        seen = []
        h = self.make(Router(_2_tweets_search_recent=lambda q: (seen.append(q["query"]), {"data": [], "meta": {}})[1]))
        out = h.run_stage(3, "tr-tech-1", only="K")
        self.assertTrue(all(harness.IDEAS["tr-tech-1"]["spam"] not in q for q in seen))
        out = h.run_stage(3, "tr-tech-1", only="Kspam")
        self.assertEqual(sorted(k for k in out if k.startswith("Kspam")), ["Kspam-recency", "Kspam-relevancy"])
        self.assertEqual(seen[-1], harness.IDEAS["tr-tech-1"]["spam"])

    def write_corpus(self, h, texts):
        corpus = [{"id": f"p{n}", "idea": "i", "text": t} for n, t in enumerate(texts)]
        h.store.write_atomic(h.store.root / "corpus-stage2.jsonl", "".join(json.dumps(c) + "\n" for c in corpus))
        return corpus

    def test_second_scorer_gets_every_positive_and_unclear_then_disagreements_block_finalising(self) -> None:
        h = self.make(Router())
        texts = [f"post number {n} with enough words to be unique" for n in range(12)]
        self.write_corpus(h, texts)
        first = [{"id": f"p{n}", "opening": texts[n][:30], "relevant": r, "real": 2, "useful": 1, "act": False, "type": "genuine"}
                 for n, r in enumerate([2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])]
        path = self.root / "first.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in first))
        out = h.ingest_scores(2, path, seed=1)
        self.assertEqual(out["second_score"]["positives_and_unclear"], 3)
        second_ids = {r["id"] for r in h.store.rows(h.store.root / "second-stage2.jsonl")}
        self.assertTrue({"p0", "p1", "p2"} <= second_ids)
        self.assertNotIn("relevant", h.store.rows(h.store.root / "second-stage2.jsonl")[0])   # blind to the first scores
        second = [{"id": i, "opening": texts[int(i[1:])][:30], "relevant": 0 if i == "p1" else
                   [r for r in first if r["id"] == i][0]["relevant"], "real": 2, "useful": 1, "act": False, "type": "genuine"} for i in second_ids]
        path2 = self.root / "second.jsonl"
        path2.write_text("".join(json.dumps(r) + "\n" for r in second))
        report = h.second_scores(2, path2)
        self.assertEqual(report["disagreements"], 1)
        self.assertEqual(report["agreement"]["relevant"]["first->second"]["2->0"], 1)
        with self.assertRaisesRegex(harness.Stop, "adjudication"):
            h.finalise_scores(2)
        adj = self.root / "adj.jsonl"
        adj.write_text(json.dumps({"id": "p1", "relevant": 1, "real": 2, "useful": 1, "why": "answers, doesn't ask"}) + "\n")
        done = h.finalise_scores(2, adj)
        self.assertEqual((done["final"], done["adjudicated"]), (12, 1))

    def test_recheck_records_gone_without_labelling_spam(self) -> None:
        router = Router(_2_tweets=lookup_route({"5": post("5", "still here")}))
        h = self.make(router)
        self.store.upsert_posts(NOW - timedelta(hours=30), [
            {"post_id": "5", "label": "x_api", "x": post("5", "still here"), "sighting": {"source": "K", "stage": "stage2"}},
            {"post_id": "6", "label": "x_api", "x": post("6", "deleted later"), "sighting": {"source": "K", "stage": "stage2"}}])
        out = h.recheck(24)
        self.assertEqual((out["due"], out["gone"]), (2, 1))
        self.assertEqual(json.loads(self.store.load_posts()["6"]["labels"]), ["x_api"])
        self.assertEqual(h.recheck(24), {"due": 0})


class Eligibility(unittest.TestCase):
    def test_one_rule_for_every_source(self) -> None:
        window = {"start": "2026-09-26T00:00:00Z", "end": "2026-09-27T00:00:00Z"}
        base = {"created_at": "2026-09-26T05:00:00.000Z", "lang": "en", "text": "hello"}
        self.assertEqual(harness.eligible(base, window), (True, "ok"))
        self.assertEqual(harness.eligible({**base, "lang": "ja"}, window)[1], "lang ja")
        self.assertEqual(harness.eligible({**base, "text": "RT @a: hi"}, window)[1], "retweet")
        self.assertEqual(harness.eligible({**base, "created_at": "2026-09-25T05:00:00Z"}, window)[1], "outside window")
        self.assertEqual(harness.eligible(None, window), (None, "not on X"))

    def test_closing_json_kept_flag_is_read(self) -> None:
        text = json.dumps({"posts": [{"id": "2103752357758787700", "text": "a", "kept": True},
                                     {"id": "2103752341170315456", "text": "b", "kept": False}]})
        slots, source = harness.run_claims({"stream": {"tools": [], "text": text}})
        self.assertEqual([s["kept_by_grok"] for s in slots], [True, False])


class Pieces(unittest.TestCase):
    def test_syntax_guard_and_web_conversion(self) -> None:
        harness.check_syntax('"free alternative" -is:retweet lang:en min_likes:5', "api")
        with self.assertRaises(harness.Stop):
            harness.check_syntax("free -filter:replies", "api")
        web = harness.to_web_syntax('"x" -is:retweet -is:reply lang:en min_likes:5 -has:links', 24)
        self.assertEqual(web, '"x" -filter:replies min_faves:5 -filter:links within_time:24h')
        for idea in harness.IDEAS.values():
            for q in idea["k"] + ([idea["spam"]] if "spam" in idea else []):
                harness.check_syntax(q, "api")
                harness.to_web_syntax(q, 6)

    def test_every_semantic_or_self_prompt_carries_dates_and_limit(self) -> None:
        window = harness.windows_at(NOW)["demand"]
        idea = harness.IDEAS["demand-tech-1"]
        for arm in ("free", "hinted", "steered", "self"):
            prompt = harness.arm_prompt(arm, idea, window, 24)
            self.assertIn("limit 10", prompt)
            self.assertIn(harness.OUTPUT, prompt)
        self.assertIn("from_date = 2026-09-26, to_date = 2026-09-28", harness.arm_prompt("self", idea, window, 24))
        self.assertIn("from_date 2026-09-26 and to_date 2026-09-28", harness.arm_prompt("hinted", idea, window, 24))
        self.assertNotIn("semantic", harness.arm_prompt("free", idea, window, 24).lower())

    def test_pad_query_hits_exact_lengths(self) -> None:
        for n in (513, 1025, 4097):
            q = harness.pad_query(harness.P1_BASE, n)
            self.assertEqual(len(q), n)
            self.assertTrue(q.startswith(harness.P1_BASE))

    def test_worst_case_matches_the_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "S1.raw.txt").write_text(TOOL_TEXT)
            worst = harness.worst_case(Path(tmp))
        self.assertEqual(worst["p9_ids"], 3)
        self.assertAlmostEqual(worst["x_total"], 1.19 + 5 * 0.05 + 0.15 + 3 * 0.050 + 3 * 0.005, places=4)
        self.assertEqual(worst["grok_runs"], 11)
        self.assertLessEqual(harness.worst_case()["x_total"], harness.PILOT_CEILING)

    def test_scores_are_checked_by_id_and_opening_words(self) -> None:
        corpus = {"p61864d": {"id": "p61864d", "text": "@Alexfeinberg What do you use instead of Google maps?"},
                  "p5af09d": {"id": "p5af09d", "text": "Still have Apple devices and software for work"},
                  "p0000aa": {"id": "p0000aa", "text": "Totally unscored post"}}
        rows = [{"id": "p61864f", "opening": "@Alexfeinberg What do you use i", "relevant": 1, "real": 2, "useful": 2, "act": True},
                {"id": "p5af09d", "opening": "Still have Apple devices and so", "relevant": 2, "real": 2, "useful": 2, "act": True},
                {"id": "p5af09d", "opening": "Still have Apple devices and so", "relevant": 0, "real": 0, "useful": 0, "act": False},
                {"id": "pzzzzzz", "opening": "nothing like any post at all xx", "relevant": 2, "real": 2, "useful": 2, "act": True}]
        kept, problems = harness.check_scores(corpus, rows)
        self.assertEqual([r["id"] for r in kept], ["p5af09d"])      # a wrong id is never corrected into the scores
        self.assertIn("rejected p61864f: not a corpus id; its opening matches p61864d", problems)
        self.assertTrue(any("duplicate" in p for p in problems))
        self.assertTrue(any("rejected pzzzzzz" in p for p in problems))
        self.assertIn("missing score for p0000aa", problems)

    def test_brief_carries_the_job_rubric_and_echo(self) -> None:
        brief = harness.scoring_brief("worth-joining", "x.jsonl")
        self.assertIn("witty reply", brief)
        self.assertIn('"opening"', brief)
        self.assertIn('"act"', brief)

    def test_corpus_is_blind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = harness.Store(Path(tmp))
            store.upsert_posts(NOW, [{"post_id": "5", "label": "x_api", "x": post("5", "a live reply thread"),
                                      "sighting": {"source": "K", "stage": "stage1", "idea": "wj-tech-1", "rank": 0}}])
            h = harness.Harness(store, None, None, clock=lambda: NOW)
            h.corpus(1)
            line = json.loads((Path(tmp) / "corpus-stage1.jsonl").read_text().splitlines()[0])
            self.assertEqual(set(line), {"id", "idea", "text", "replies", "age_hours"})   # Stage 1 adds reply count and age
            self.assertEqual((line["replies"], line["age_hours"]), (1, 0.5))
            self.assertNotEqual(line["id"], "5")
            key = json.loads((Path(tmp) / "corpus-key-stage1.json").read_text())
            self.assertEqual(key[line["id"]]["post_id"], "5")



def seed_block(store, *blocks) -> None:
    """blocks: (id, created datetime). Windows as the harness would have made them."""
    data = store.progress()
    for bid, at in blocks:
        data["blocks"].append({"id": bid, "created": harness.iso(at), "last_used": harness.iso(at),
                               "brisbane": "", "windows": harness.windows_at(at)})
    store.save_progress(data)


def seed_call(store, call_id, at, posts, **params) -> None:
    store.append(store.requests, {"call_id": call_id, "time_utc": harness.iso(at), "status": 200, "estimated_cost": 0.0,
                                  "params": params or None, "result_count": len(posts), "raw_path": f"raw/{call_id}.json"})
    (store.root / "raw" / f"{call_id}.json").write_text(json.dumps({"data": posts, "meta": {"result_count": len(posts)}}))


def sha(path: Path) -> str:
    return harness.hashlib.sha256(path.read_bytes()).hexdigest()


class NewPullPrep(Base):
    """27 Sep: a new X pull (Stage 1, Stage 3, a fresh Demand window) without risk to what's already scored."""

    def test_idea_cards_and_checkpoint(self) -> None:
        tr = harness.IDEAS["tr-tech-3"]
        self.assertEqual((tr["job"], tr["niche"], tr["text"]), ("tool-research", "tech", "Claude Code (the AI coding agent)"))
        self.assertEqual(tr["k"][0], '"Claude Code" -is:retweet lang:en')
        self.assertIn("-course", tr["spam"])
        for key in ("demand-comedy-1", "demand-comedy-2"):
            old, new = harness.IDEAS[key], harness.IDEAS[key + "b"]
            self.assertIn("min_likes:10", old["k"][0])
            self.assertEqual(new["k"][0], old["k"][0].replace(" min_likes:10", ""))
            self.assertEqual((new["k"][1], new["text"], new["job"]), (old["k"][1], old["text"], old["job"]))
        self.assertEqual((harness.X_CHECKPOINT, harness.PILOT_CEILING), (7.00, 2.50))

    def test_pinned_block_survives_a_gap_with_its_windows(self) -> None:
        seen = []
        h = self.make(Router(_2_tweets_search_recent=lambda q: (seen.append(q), {"data": [], "meta": {}})[1]))
        first = self.store.block(self.now)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(harness.main(["config", "--pin-block", "B1"], harness=h), 0)
            self.assertEqual(harness.main(["config", "--pin-block", "B9"], harness=h), 2)
        self.now = NOW + timedelta(hours=3)
        again = self.store.block(self.now)
        self.assertEqual((again["id"], again["windows"]), ("B1", first["windows"]))
        self.assertEqual(again["last_used"], harness.iso(self.now))
        with self.assertRaisesRegex(harness.Stop, "pinned"):
            self.store.block(self.now, new=True)
        h.run_stage(2, "demand-tech-1", only="K-recency")
        self.assertEqual({r["block"] for r in self.store.rows(self.store.requests)}, {"B1"})
        self.assertEqual({q["start_time"] for q in seen}, {first["windows"]["demand"]["start"]})
        with redirect_stdout(io.StringIO()):
            harness.main(["config", "--pin-block", "none"], harness=h)
        self.now += timedelta(hours=3)                                  # unpinned: the 2-hour rule is back
        self.assertEqual(self.store.block(self.now)["id"], "B2")

    def test_a_stop_mid_source_resumes_without_resending_what_returned(self) -> None:
        seen, stop = [], [True]
        def search(q):
            seen.append(q["query"])
            if len(seen) == 2 and stop[0]:
                raise harness.Stop("simulated stop on the second query")
            return {"data": [post(str(5000 + len(seen)), "is there a free alternative")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=search))
        with self.assertRaisesRegex(harness.Stop, "simulated"):
            h.run_stage(2, "demand-tech-1", only="K-recency")
        stop[0] = False
        out = h.run_stage(2, "demand-tech-1", only="K-recency")
        v1, v2 = harness.IDEAS["demand-tech-1"]["k"]
        self.assertEqual(seen, [v1, v2, v2])
        calls = out["K-recency"]["calls"]
        self.assertEqual([(c["variant"], c.get("reused", False)) for c in calls], [("v1", True), ("v2", False)])
        self.assertEqual(len([r for r in self.store.rows(self.store.requests) if r["status"] == 200]), 2)

    def test_min_replies_rejected_reruns_without_it_and_keeps_both_rows(self) -> None:
        seen = []
        def search(q):
            seen.append(q["query"])
            return 400 if "min_replies" in q["query"] else {"data": [post("7001", "a joke thread")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=search))
        out = h.run_stage(1, "wj-comedy-1", only="K")["K-recency"]
        self.assertEqual([c["http"] for c in out["calls"]], [400, 200, 400, 200])
        self.assertIn("min_replies rejected; reran without it", out["notes"])
        self.assertNotIn("min_replies", seen[1])
        self.assertIn("min_likes:50", seen[3])
        self.assertNotIn("  ", seen[3])
        self.assertEqual([r["status"] for r in self.store.rows(self.store.requests)], [400, 200, 400, 200])

    def seeded(self):
        """Stage 2 already scored (untouchable), plus new sightings in B2 for stages 1 and 2."""
        h = self.make(Router())
        seed_block(self.store, ("B1", NOW - timedelta(days=1)), ("B2", NOW - timedelta(hours=8)))
        for name in ("corpus-stage2.jsonl", "scores-stage2.jsonl", "final-scores-stage2.jsonl",
                     "second-stage2.jsonl", "second-scores-stage2.jsonl"):
            (self.root / name).write_text(json.dumps({"id": "pold", "text": name}) + "\n")
        seen_at = NOW - timedelta(hours=7)
        old = {**post("8001", "old stage two post from block one", 60 * 26), "conversation_id": "8000"}
        both = {**post("8002", "seen in both blocks under different ideas", 60 * 9), "conversation_id": "8002"}
        new = {**post("8003", "a new demand post in block two", 60 * 8, author_id="99"), "conversation_id": "8003"}
        wj = {**post("8004", "shipping my agent today, demo inside", 60 * 9), "conversation_id": "8004",
              "public_metrics": {"reply_count": 4, "like_count": 2}}
        seed_call(self.store, "x0001", seen_at, [wj])
        self.store.upsert_posts(NOW - timedelta(days=1), [
            {"post_id": "8001", "label": "x_api", "x": old, "sighting": {"source": "K-recency", "stage": "stage2", "idea": "demand-tech-1", "block": "B1", "eligible": True}},
            {"post_id": "8002", "label": "x_api", "x": both, "sighting": {"source": "K-recency", "stage": "stage2", "idea": "demand-tech-1", "block": "B1", "eligible": True}}])
        later = {**wj, "public_metrics": {"reply_count": 40}}          # a later fetch must not leak into the corpus
        self.store.upsert_posts(seen_at, [
            {"post_id": "8002", "label": "x_api", "x": both, "sighting": {"source": "K-relevancy", "stage": "stage2", "idea": "demand-tech-2", "block": "B2", "eligible": True}},
            {"post_id": "8003", "label": "x_api", "x": new, "sighting": {"source": "K-recency", "stage": "stage2", "idea": "demand-tech-2", "block": "B2", "eligible": True}},
            {"post_id": "8004", "label": "x_api", "x": later, "sighting": {"source": "K-recency", "stage": "stage1", "idea": "wj-tech-1", "block": "B2", "call": "x0001", "rank": 0, "eligible": True}}])
        return h

    def scores_for(self, corpus_file: str) -> list[dict]:
        return [{"id": c["id"], "opening": c["text"][:30], "relevant": 2, "real": 2, "useful": 1, "act": True,
                 "type": "genuine"} for c in self.store.rows(self.root / corpus_file)]

    def write(self, name: str, rows: list[dict]) -> Path:
        path = Path(self.tmp.name) / name
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        return path

    def test_block_commands_never_touch_stage_two_files(self) -> None:
        h = self.seeded()
        guarded = {n: sha(self.root / n) for n in ("corpus-stage2.jsonl", "scores-stage2.jsonl", "final-scores-stage2.jsonl",
                                                    "second-stage2.jsonl", "second-scores-stage2.jsonl")}
        with self.assertRaisesRegex(harness.Stop, "refusing to overwrite corpus-stage2.jsonl"):
            h.corpus(2)
        out = h.corpus(2, block="B2", batch=1)
        self.assertEqual((out["posts"], out["parts"]), (2, 2))
        self.assertIn("corpus-stage2-B2-part2.jsonl", out["written"])
        self.assertIn("corpus-stage2-B2-part2.jsonl", (self.root / "corpus-brief-stage2-B2-part2-legacy.md").read_text())
        key = json.loads((self.root / "corpus-key-stage2-B2.json").read_text())
        self.assertEqual({k["post_id"] for k in key.values()}, {"8002", "8003"})
        row = next(k for k in key.values() if k["post_id"] == "8002")
        self.assertEqual((row["idea_key"], row["conversation_id"], row["author_id"]), ("demand-tech-2", "8002", "77"))
        lines = self.store.rows(self.root / "corpus-stage2-B2.jsonl")
        self.assertEqual({l["idea"] for l in lines}, {harness.IDEAS["demand-tech-2"]["text"]})
        self.assertEqual(set(lines[0]), {"id", "idea", "text"})
        with self.assertRaisesRegex(harness.Stop, "refusing"):
            h.corpus(2, block="B2")

        scores = self.scores_for("corpus-stage2-B2.jsonl")
        part_a, part_b = self.write("a.jsonl", scores[:1]), self.write("b.jsonl", scores[1:])
        with self.assertRaisesRegex(harness.Stop, "wrote nothing.*missing"):
            h.ingest_scores(2, [part_a], block="B2")
        self.assertFalse((self.root / "scores-stage2-B2.jsonl").exists())
        dup = self.write("dup.jsonl", scores + scores[:1])
        with self.assertRaisesRegex(harness.Stop, "duplicate"):
            h.ingest_scores(2, [dup], block="B2")
        with self.assertRaisesRegex(harness.Stop, "refusing to overwrite scores-stage2.jsonl"):
            h.ingest_scores(2, [part_a, part_b])
        out = h.ingest_scores(2, [part_a, part_b], block="B2", second="all", seed=1)
        self.assertEqual(out["files"], ["scores-stage2-B2.jsonl", "second-stage2-B2.jsonl", "second-mode-stage2-B2.json"])
        self.assertEqual(len(self.store.rows(self.root / "second-stage2-B2.jsonl")), 2)
        self.assertEqual(h.second_mode(2, "B2"), "all")
        with self.assertRaisesRegex(harness.Stop, "refusing"):
            h.ingest_scores(2, [part_a, part_b], block="B2")

        with self.assertRaisesRegex(harness.Stop, "wrote nothing"):
            h.second_scores(2, part_a, block="B2")
        self.assertFalse((self.root / "second-scores-stage2-B2.jsonl").exists())
        h.second_scores(2, self.write("s.jsonl", scores), block="B2")
        self.assertTrue((self.root / "disagreements-stage2-B2.jsonl").exists())
        with self.assertRaisesRegex(harness.Stop, "refusing to overwrite final-scores-stage2.jsonl"):
            h.finalise_scores(2)
        self.assertEqual(h.finalise_scores(2, block="B2")["file"], "final-scores-stage2-B2.jsonl")
        with self.assertRaisesRegex(harness.Stop, "refusing"):
            h.finalise_scores(2, block="B2")
        self.assertEqual({n: sha(self.root / n) for n in guarded}, guarded)

    def test_second_mode_all_refuses_to_finalise_without_every_second_score(self) -> None:
        h = self.seeded()
        h.corpus(2, block="B2")
        scores = self.scores_for("corpus-stage2-B2.jsonl")
        h.ingest_scores(2, self.write("a.jsonl", scores), block="B2", second="all")
        (self.root / "second-scores-stage2-B2.jsonl").write_text(json.dumps(scores[0]) + "\n")   # as if hand-trimmed
        with self.assertRaisesRegex(harness.Stop, "no second score"):
            h.finalise_scores(2, block="B2")
        self.assertFalse((self.root / "final-scores-stage2-B2.jsonl").exists())

    def test_stage_one_corpus_carries_replies_and_age_at_fetch(self) -> None:
        h = self.seeded()
        h.corpus(1, block="B2")
        (line,) = self.store.rows(self.root / "corpus-stage1-B2.jsonl")
        self.assertEqual((line["replies"], line["age_hours"]), (4, 2.0))      # the call's copy, not the later 40
        brief = (self.root / "corpus-brief-stage1-B2-legacy.md").read_text()
        self.assertNotIn("Judge from the text alone", brief)
        self.assertIn("replies and age_hours", brief)
        # other jobs' briefs unchanged, byte for byte
        self.assertEqual(sha_text(harness.scoring_brief("demand", "x.jsonl")),
                         "dea3f440fbedb063a579f88fa67315cf13b2a09ef117ff873bb2331fde4124c6")
        self.assertEqual(sha_text(harness.scoring_brief("tool-research", "x.jsonl")),
                         "a5f8555221eed2bdd70722a04b509c058816fc04bfa52a5a6f49c1b1ed7f4d28")

    def test_reread_batches_by_100_and_marks_gone_only_when_sent_and_absent(self) -> None:
        router_seen = []
        live = {}
        def lookup(q):
            ids = q["ids"].split(",")
            router_seen.append(ids)
            return {"data": [live[i] for i in ids if i in live]}
        h = self.make(Router(_2_tweets=lookup))
        seed_block(self.store, ("B1", NOW - timedelta(hours=8)), ("B2", NOW - timedelta(hours=1)))
        found_at = NOW - timedelta(hours=7)
        posts = [post(str(9000 + n), f"post {n}", 60 * 8) for n in range(120)]
        seed_call(self.store, "x0001", found_at, posts)
        live.update({p["id"]: {**p, "public_metrics": {"reply_count": 9}} for p in posts if int(p["id"]) % 2 == 0})
        self.store.upsert_posts(NOW - timedelta(hours=30), [   # first_seen long ago: hours must come from the block sighting
            {"post_id": p["id"], "label": "x_api", "x": p,
             "sighting": {"source": "K-recency", "stage": "stage1", "block": "B1", "call": "x0001"}} for p in posts])
        other = post("9999", "found in B2 only", 60)
        self.store.upsert_posts(NOW - timedelta(hours=30), [
            {"post_id": "9999", "label": "x_api", "x": other, "sighting": {"source": "K-recency", "stage": "stage1", "block": "B2"}}])
        self.store.pin_block("B1")
        out = h.reread()
        self.assertEqual([len(ids) for ids in router_seen], [100, 20])
        self.assertEqual((out["due"], out["reread"], out["gone"], out["block"]), (120, 120, 60, "B1"))
        rows = {r["post_id"]: r for r in self.store.rows(self.root / "reread.jsonl")}
        self.assertNotIn("9999", rows)
        self.assertEqual(rows["9000"]["hours_later"], 7.0)
        self.assertEqual((rows["9000"]["gone"], rows["9001"]["gone"]), (False, True))
        self.assertEqual(rows["9000"]["after"], {"reply_count": 9})
        self.assertEqual(h.reread(), {"due": 0, "block": "B1", "recovered": 0})

    def test_reread_failed_batch_marks_nothing_gone(self) -> None:
        h = self.make(Router(_2_tweets=400))
        seed_block(self.store, ("B1", NOW - timedelta(hours=8)))
        seed_call(self.store, "x0001", NOW - timedelta(hours=7), [])
        self.store.upsert_posts(NOW - timedelta(hours=7), [
            {"post_id": "9100", "label": "x_api", "x": post("9100", "a"), "sighting": {"stage": "stage1", "block": "B1", "call": "x0001"}}])
        out = h.reread(block="B1")
        self.assertEqual((out["reread"], out["failed_calls"][0]["http"]), (0, 400))
        self.assertFalse((self.root / "reread.jsonl").exists())
        self.assertEqual(self.store.load_posts()["9100"]["reread"], "")

    def test_manifest_lists_every_sighting_in_the_block(self) -> None:
        def search(q):
            base = 7100 if q["sort_order"] == "recency" else 7200
            return {"data": [post(str(base + n), "is there a free alternative", 30) for n in range(2)], "meta": {"result_count": 2}}
        h = self.make(Router(_2_tweets_search_recent=search))
        h.run_stage(2, "demand-tech-1", only="K")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(harness.main(["manifest", "--block", "B1"], harness=h), 0)
        with (self.root / "manifest-B1.csv").open(newline="") as fh:
            rows = list(harness.csv.DictReader(fh))
        self.assertEqual(list(rows[0]), ["post_id", "stage", "idea", "source", "sort", "variant", "rank", "call",
                                         "result_count", "eligible"])
        self.assertEqual(len(rows), 8)                                 # 2 sorts × 2 queries × 2 posts (sightings, not posts)
        self.assertEqual({(r["sort"], r["variant"]) for r in rows},
                         {("recency", "v1"), ("recency", "v2"), ("relevancy", "v1"), ("relevancy", "v2")})
        self.assertEqual({r["result_count"] for r in rows}, {"2"})
        self.assertEqual({r["rank"] for r in rows}, {"0", "1"})
        self.assertEqual({r["eligible"] for r in rows}, {"True"})

    def test_cli_parses_the_new_options(self) -> None:
        args = harness.build_parser().parse_args(["ingest-scores", "--stage", "1", "--block", "B3", "--second", "all", "a", "b"])
        self.assertEqual((args.files, args.block, args.second), (["a", "b"], "B3", "all"))
        args = harness.build_parser().parse_args(["corpus", "--stage", "3", "--block", "B3", "--batch", "50"])
        self.assertEqual((args.block, args.batch), ("B3", 50))
        with self.assertRaisesRegex(harness.Stop, "B3"):
            harness.Harness._suffix(1, "../x")


def sha_text(text: str) -> str:
    return harness.hashlib.sha256(text.encode()).hexdigest()


class ReviewFixes(Base):
    """28 Sep review: interrupted runs never pay twice or overwrite, score ingest fails closed, corpus sets
    publish whole, and the budget gates can't be walked past."""

    # 1. reread
    def test_reread_saves_each_batch_so_a_resume_fetches_only_the_rest(self) -> None:
        seen, stop = [], [True]
        live = {}
        def lookup(q):
            ids = q["ids"].split(",")
            seen.append(ids)
            if len(seen) == 2 and stop[0]:
                raise harness.Stop("simulated stop on the second batch")
            return {"data": [live[i] for i in ids if i in live]}
        h = self.make(Router(_2_tweets=lookup))
        seed_block(self.store, ("B1", NOW - timedelta(hours=8)))
        posts = [post(str(9000 + n), f"post {n}", 60 * 8) for n in range(120)]
        seed_call(self.store, "x0001", NOW - timedelta(hours=7), posts)
        live.update({p["id"]: p for p in posts})
        self.store.upsert_posts(NOW - timedelta(hours=7), [
            {"post_id": p["id"], "label": "x_api", "x": p,
             "sighting": {"source": "K-recency", "stage": "stage1", "block": "B1", "call": "x0001"}} for p in posts])
        with self.assertRaisesRegex(harness.Stop, "simulated"):
            h.reread(block="B1")
        first = set(seen[0])
        self.assertEqual({pid for pid, r in self.store.load_posts().items() if r["reread"]}, first)
        stop[0] = False
        out = h.reread(block="B1")
        self.assertEqual((out["due"], out["reread"]), (20, 20))
        self.assertEqual(len(seen), 3)
        self.assertEqual(set(seen[2]), {p["id"] for p in posts} - first)

    def _reread_fixture(self, seen):
        live = {}
        def lookup(q):
            ids = q["ids"].split(",")
            seen.append(ids)
            return {"data": [live[i] for i in ids if i in live and i != "9003"]}      # 9003 is gone
        h = self.make(Router(_2_tweets=lookup))
        seed_block(self.store, ("B1", NOW - timedelta(hours=8)))
        posts = [post(str(9000 + n), f"post {n}", 60 * 8) for n in range(10)]
        seed_call(self.store, "x0001", NOW - timedelta(hours=7), posts)
        live.update({p["id"]: p for p in posts})
        self.store.upsert_posts(NOW - timedelta(hours=7), [
            {"post_id": p["id"], "label": "x_api", "x": p,
             "sighting": {"source": "K-recency", "stage": "stage1", "block": "B1", "call": "x0001"}} for p in posts])
        return h

    def test_reread_recovers_from_its_log_when_the_table_update_failed(self) -> None:
        seen = []
        h = self._reread_fixture(seen)
        real = self.store.upsert_posts
        def broken(now, updates):
            raise OSError("disk full while saving posts.csv")
        self.store.upsert_posts = broken
        with self.assertRaises(OSError):
            h.reread(block="B1")
        self.store.upsert_posts = real
        out = h.reread(block="B1")
        self.assertEqual(len(seen), 1)                                   # paid once, never again
        self.assertEqual((out["recovered"], out["due"]), (10, 0))
        self.assertTrue(all(r["reread"] for r in self.store.load_posts().values()))

    def test_reread_recovers_from_the_saved_body_when_nothing_was_logged(self) -> None:
        seen = []
        h = self._reread_fixture(seen)
        real = self.store.append
        def broken(path, row):
            if path.name == "reread.jsonl":
                raise OSError("crash before the first reread line")
            return real(path, row)
        self.store.append = broken
        with self.assertRaises(OSError):
            h.reread(block="B1")
        self.store.append = real
        out = h.reread(block="B1")
        self.assertEqual(len(seen), 1)
        self.assertEqual(out["recovered"], 10)
        gone = {pid for pid, r in self.store.load_posts().items() if json.loads(r["reread"])["gone"]}
        self.assertEqual(gone, {"9003"})

    # 2. recheck
    def test_recheck_skips_a_rejected_batch_instead_of_marking_it_gone(self) -> None:
        answer = [403]
        h = self.make(Router(_2_tweets=lambda q: answer[0] if answer[0] != 200 else lookup_route({"5": post("5", "here")})(q)))
        self.store.upsert_posts(NOW - timedelta(hours=30), [
            {"post_id": "5", "label": "x_api", "x": post("5", "here"), "sighting": {"source": "K", "stage": "stage2"}},
            {"post_id": "6", "label": "x_api", "x": post("6", "gone"), "sighting": {"source": "K", "stage": "stage2"}}])
        out = h.recheck(24)
        self.assertEqual((out["due"], out["gone"], out["failed_calls"][0]["http"]), (2, 0, 403))
        self.assertFalse((self.root / "recheck.jsonl").exists())
        answer[0] = 200
        self.assertEqual(h.recheck(24), {"due": 2, "gone": 1})       # both still due, checked on a 200

    # 3a. K query sent before processing
    def test_k_query_logged_as_sent_before_processing_so_a_crash_never_resends(self) -> None:
        seen = []
        def search(q):
            seen.append(q["query"])
            return {"data": [post(str(6000 + len(seen)), "is there a free alternative")], "meta": {"result_count": 1}}
        h = self.make(Router(_2_tweets_search_recent=search))
        real, calls = h._note_posts, [0]
        def crash_once(*a, **k):
            calls[0] += 1
            if calls[0] == 1:
                raise RuntimeError("crash while processing posts")
            return real(*a, **k)
        h._note_posts = crash_once
        with self.assertRaisesRegex(RuntimeError, "processing"):
            h.run_stage(2, "demand-tech-1", only="K-recency")
        h._note_posts = real
        out = h.run_stage(2, "demand-tech-1", only="K-recency")
        v1, v2 = harness.IDEAS["demand-tech-1"]["k"]
        self.assertEqual(seen, [v1, v2])                                # v1 not sent again
        self.assertEqual([(c["variant"], c.get("reused", False)) for c in out["K-recency"]["calls"]], [("v1", True), ("v2", False)])
        self.assertIn("6001", self.store.load_posts())                  # v1's posts recovered from its raw body
        self.assertTrue(all(s["noted"] for s in h._sent(f"S2:demand-tech-1:K-recency:B1")))

    # 3b. raw bodies are exclusive
    def test_raw_body_never_overwritten_when_the_log_lost_its_row(self) -> None:
        h = self.make(Router(_2_usage={"data": []}))
        (self.root / "raw" / "x0001.json").write_text("precious")       # a crash left the body, not the row
        h.run_pilot_step("P0")
        self.assertEqual((self.root / "raw" / "x0001.json").read_text(), "precious")
        (row,) = self.store.rows(self.store.requests)
        self.assertEqual((row["call_id"], row["raw_path"]), ("x0002", "raw/x0002.json"))
        self.assertEqual(json.loads((self.root / "raw" / "x0002.json").read_text()), {"data": []})
        self.assertEqual(self.store.next_id(self.store.requests, "x", self.root / "raw"), "x0003")

    # 3c. Grok resume
    def grok_ready(self, grok: FakeGrok) -> harness.Harness:
        known = {"2103752357758787700": post("2103752357758787700", "Is there a free alternative to Premiere? Asking for a friend", 60)}
        h = self.make(Router(_2_tweets=lookup_route(known)), grok)
        data = self.store.progress()
        data["settings"]["model"] = "grok-4.7"
        self.store.save_progress(data)
        return h

    def test_grok_run_saved_before_a_crash_is_finished_from_its_output_not_paid_again(self) -> None:
        grok = FakeGrok((0, ok_stream(), ""))                            # one reply: a second run would fail
        h = self.grok_ready(grok)
        with mock.patch.object(harness, "check_claims", side_effect=RuntimeError("crash while checking claims")):
            with self.assertRaisesRegex(RuntimeError, "checking claims"):
                h.run_pilot_step("P7-free")
        self.assertEqual(self.store.rows(self.store.grok_log), [])
        self.assertTrue((self.root / "grok" / "g0001.pending.json").exists())
        result = h.run_pilot_step("P7-free")
        self.assertEqual((result["status"], result["run"], len(grok.calls)), ("done", "g0001", 1))
        (row,) = self.store.rows(self.store.grok_log)
        self.assertTrue(row["resumed_from_saved_output"])
        self.assertEqual(row["counts"]["labels"]["real"], 1)
        self.assertFalse((self.root / "grok" / "g0001.pending.json").exists())
        self.assertEqual(self.store.grok_spent(), 0.04)                 # billed once

    def test_an_unrecorded_grok_run_blocks_every_other_grok_step(self) -> None:
        grok = FakeGrok((0, ok_stream(), ""), (0, ok_stream(), ""))
        h = self.grok_ready(grok)
        with mock.patch.object(harness, "check_claims", side_effect=RuntimeError("crash while checking claims")):
            with self.assertRaisesRegex(RuntimeError, "checking claims"):
                h.run_pilot_step("P7-free")
        other = next(a for a in harness.PILOT_ARMS if a != "P7-free")
        with self.assertRaisesRegex(harness.Stop, r"g0001 for step P7-free was paid for but isn't recorded"):
            h.run_pilot_step(other)
        self.assertEqual(len(grok.calls), 1)                             # no second paid run

    def test_grok_run_logged_but_not_recorded_is_recorded_not_paid_again(self) -> None:
        grok = FakeGrok((0, ok_stream(), ""))
        h = self.grok_ready(grok)
        real = h.record
        def crash_on_done(name, status, attempt, todo=""):
            if status == "done":
                raise RuntimeError("crash before the step was recorded")
            return real(name, status, attempt, todo)
        h.record = crash_on_done
        with self.assertRaisesRegex(RuntimeError, "recorded"):
            h.run_pilot_step("P7-free")
        h.record = real
        self.assertEqual(h.step_state("P7-free")["status"], "pending")
        result = h.run_pilot_step("P7-free")
        self.assertEqual((result["status"], result["run"], len(grok.calls)), ("done", "g0001", 1))
        self.assertEqual(len(self.store.rows(self.store.grok_log)), 1)

    def test_saved_grok_output_with_no_record_stops_every_grok_step(self) -> None:
        grok = FakeGrok((0, ok_stream(), ""))
        h = self.grok_ready(grok)
        (self.root / "grok" / "g0001.stdout").write_text(ok_stream())
        with self.assertRaisesRegex(harness.Stop, r"g0001 was paid for.*move private/grok/g0001\.\* aside"):
            h.run_pilot_step("P7-free")
        self.assertEqual(grok.calls, [])

    # 4. score ingest
    TEXTS = ["Is there a free alternative to Premiere Pro for editing",
             "Is there a free alternative to Photoshop these days",
             "Completely different words about the weather today"]

    def good_scores(self) -> list[dict]:
        return [{"id": f"p{n}", "opening": t[:30], "relevant": 2, "real": 2, "useful": 1, "act": True, "type": "genuine"}
                for n, t in enumerate(self.TEXTS)]

    def refuses_on_both_paths(self, mutate, pattern: str) -> None:
        for path in ("ingest", "second"):
            with self.subTest(path=path, pattern=pattern):
                self.root = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "private"
                h = self.make(Router())
                h.store.write_atomic(self.root / "corpus-stage2.jsonl", "".join(
                    json.dumps({"id": f"p{n}", "idea": "i", "text": t}) + "\n" for n, t in enumerate(self.TEXTS)))
                bad = self.root.parent / "bad.jsonl"
                bad.write_text("".join(json.dumps(r) + "\n" for r in mutate(self.good_scores())))
                if path == "ingest":
                    with self.assertRaisesRegex(harness.Stop, "wrote nothing.*" + pattern):
                        h.ingest_scores(2, bad)
                    written = ("scores-stage2.jsonl", "second-stage2.jsonl", "second-mode-stage2.json")
                else:
                    good = self.root.parent / "good.jsonl"
                    good.write_text("".join(json.dumps(r) + "\n" for r in self.good_scores()))
                    h.ingest_scores(2, good, second="all", seed=1)
                    with self.assertRaisesRegex(harness.Stop, "wrote nothing.*" + pattern):
                        h.second_scores(2, bad)
                    written = ("second-scores-stage2.jsonl", "disagreements-stage2.jsonl")
                self.assertFalse(any((self.root / n).exists() for n in written))

    @staticmethod
    def change(n: int, **fields):
        def mutate(rows):
            for k, v in fields.items():
                if v is KeyError:
                    rows[n].pop(k, None)
                else:
                    rows[n][k] = v
            return rows
        return mutate

    def test_score_ingest_rejects_a_missing_or_empty_opening(self) -> None:
        self.refuses_on_both_paths(self.change(0, opening=KeyError), "rejected p0: no opening words")
        self.refuses_on_both_paths(self.change(0, opening="   "), "rejected p0: no opening words")

    def test_score_ingest_needs_the_posts_own_opening_not_a_shared_prefix(self) -> None:
        self.refuses_on_both_paths(self.change(0, opening="Is there a free"), "rejected p0: opening 'is there a free'")
        self.refuses_on_both_paths(self.change(0, opening=self.TEXTS[2][:30]), "rejected p0: opening")
        # the post's own first 20 characters, whitespace and case aside, are enough
        rows = self.good_scores()
        rows[0]["opening"] = "  IS THERE a   free alternative"
        kept, problems = harness.check_scores({f"p{n}": {"text": t} for n, t in enumerate(self.TEXTS)}, rows)
        self.assertEqual((len(kept), problems), (3, []))

    def test_score_ingest_aborts_on_a_wrong_id_or_an_unknown_type(self) -> None:
        self.refuses_on_both_paths(self.change(2, id="pwrong"), "rejected pwrong: not a corpus id; its opening matches p2")
        self.refuses_on_both_paths(self.change(1, type="spam-ish"), "rejected p1: unknown type 'spam-ish'; types are genuine")

    def test_score_ingest_rejects_booleans_as_scores_and_numbers_as_act(self) -> None:
        self.assertTrue(True in (0, 1, 2))                               # why the check is by type
        self.refuses_on_both_paths(self.change(0, relevant=True), "rejected p0: relevant, real and useful")
        self.refuses_on_both_paths(self.change(1, useful=False), "rejected p1: relevant, real and useful")
        self.refuses_on_both_paths(self.change(0, real=2.0), "rejected p0: relevant, real and useful")
        self.refuses_on_both_paths(self.change(0, act=1), "rejected p0: act must be true or false, not 1")
        self.refuses_on_both_paths(self.change(2, act=KeyError), "rejected p2: act must be true or false, not None")

    def test_fail_closed_aborts_on_any_problem(self) -> None:
        with self.assertRaisesRegex(harness.Stop, "w: wrote nothing; 1 problem"):
            harness.Harness._fail_closed(["p1: something no prefix names"], "w")
        harness.Harness._fail_closed([], "w")
        self.refuses_on_both_paths(lambda rows: rows[:2], "missing score for p2")
        self.refuses_on_both_paths(lambda rows: rows + rows[:1], "duplicate score for p0")

    # 5 and 6. corpus
    def one_post_store(self) -> harness.Harness:
        h = self.make(Router())
        self.store.upsert_posts(NOW, [{"post_id": "5", "label": "x_api", "x": post("5", "a live reply thread"),
                                       "sighting": {"source": "K", "stage": "stage1", "idea": "wj-tech-1", "rank": 0}}])
        return h

    def corpus_files(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if "corpus" in p.name)

    def test_corpus_failure_while_writing_leaves_no_final_file(self) -> None:
        h = self.one_post_store()
        real, temps = Path.write_text, []
        def flaky(path, *a, **k):
            if path.name.startswith(".corpus"):
                temps.append(path.name)
                if len(temps) == 2:
                    raise OSError("disk full after the first temp write")
            return real(path, *a, **k)
        with mock.patch.object(Path, "write_text", flaky):
            with self.assertRaisesRegex(OSError, "disk full"):
                h.corpus(1)
        self.assertEqual(self.corpus_files(), [])                        # no final names, temps removed
        self.assertEqual(h.corpus(1)["posts"], 1)                        # and the set can still be built

    def test_corpus_crash_mid_rename_names_the_partial_set(self) -> None:
        h = self.one_post_store()
        real, moved = harness.os.replace, []
        def flaky(src, dst):
            if Path(dst).name.startswith("corpus"):
                moved.append(Path(dst).name)
                if len(moved) == 2:
                    raise OSError("crash mid-rename")
            return real(src, dst)
        with mock.patch.object(harness.os, "replace", flaky):
            with self.assertRaisesRegex(OSError, "mid-rename"):
                h.corpus(1)
        self.assertEqual(self.corpus_files(), ["corpus-key-stage1.json"])
        with self.assertRaisesRegex(harness.Stop, r"partial corpus set for stage1.*corpus-key-stage1\.json. Remove"):
            h.corpus(1)
        (self.root / "corpus-key-stage1.json").unlink()
        self.assertEqual(h.corpus(1)["posts"], 1)
        with self.assertRaisesRegex(harness.Stop, "refusing to overwrite corpus-stage1.jsonl"):
            h.corpus(1)

    def test_corpus_brief_is_named_legacy_and_points_jev_raters_elsewhere(self) -> None:
        h = self.one_post_store()
        out = h.corpus(1)
        self.assertEqual(out["brief"], "corpus-brief-stage1-legacy.md")
        self.assertFalse((self.root / "corpus-brief-stage1.md").exists())
        first = (self.root / out["brief"]).read_text().split("\n")[0]
        self.assertIn("`research/jev-test/raters.py brief`", first)
        self.assertIn("corpus-stage1.jsonl", (self.root / out["brief"]).read_text())

    # 7. budget
    def test_x_reserve_covers_every_slot_and_refuses_a_call_that_would_pass_the_checkpoint(self) -> None:
        router = Router(_2_tweets_search_recent={"data": [], "meta": {}})
        h = self.make(router)
        params = {"query": "q", "max_results": "10"}
        self.assertEqual(harness.max_cost("posts", params, NOW), 10 * harness.POST)
        self.assertEqual(harness.max_cost("posts", {**params, "expansions": "author_id"}, NOW), 10 * (harness.POST + harness.USER))
        self.assertEqual(harness.max_cost("counts", {"granularity": "day", "start_time": harness.iso(NOW - timedelta(days=6, hours=23)),
                                                     "end_time": harness.iso(NOW)}, NOW), harness.WORST["P3"])
        self.store.append(self.store.requests, {"stage": "stage1", "estimated_cost": 6.90})
        with self.assertRaisesRegex(harness.Stop, "X API checkpoint"):   # caller's reserve 0: the gate works out 0.15
            h.client.get("/2/tweets/search/recent", {**params, "expansions": "author_id"}, kind="posts", reserve=0.0,
                         stage="stage1", step="t")
        self.assertEqual(router.requests, [])
        h.client.get("/2/tweets/search/recent", params, kind="posts", reserve=0.0, stage="stage1", step="t")
        self.assertEqual(len(router.requests), 1)

    def test_x_call_that_overshoots_blocks_the_next_even_a_free_one(self) -> None:
        many = [post(str(100 + n), "x") for n in range(10)]
        router = Router(_2_tweets=lambda q: {"data": many, "includes": {"tweets": many}}, _2_usage={"data": []})
        h = self.make(router)
        self.store.append(self.store.requests, {"stage": "stage1", "estimated_cost": 6.94})
        harness.lookup_ids(h.client, [p["id"] for p in many], False, stage="stage1", step="t")   # reserved 0.05, billed 0.10
        self.assertGreater(self.store.x_spent(), harness.X_CHECKPOINT)
        with self.assertRaisesRegex(harness.Stop, "X API checkpoint"):
            h.client.get("/2/usage/tweets", {"days": "7"}, kind="usage", reserve=0.0, stage="stage1", step="t2")
        self.assertEqual(len(router.requests), 1)

    def test_grok_reserve_is_the_worst_case_and_an_overshoot_blocks_the_next_run(self) -> None:
        self.assertEqual(harness.GROK_RESERVE, 0.57)
        self.assertGreater(harness.GROK_RESERVE, 0.3219)                 # the dearest run to 27 Sep
        dear = stream({"type": "text", "data": '{"posts": []}'}, {"type": "end", "total_cost_usd": 0.70})
        grok = FakeGrok((0, dear, ""))
        h = self.grok_ready(grok)
        self.store.append(self.store.grok_log, {"cost_usd": 2.50})       # 2.50 + 0.57 passes 3.00 (0.30 didn't)
        with self.assertRaisesRegex(harness.Stop, "Grok checkpoint"):
            h.run_pilot_step("P7-free")
        self.assertEqual(grok.calls, [])
        self.store.append(self.store.grok_log, {"cost_usd": -0.10})      # 2.40 + 0.57 fits
        self.assertEqual(h.run_pilot_step("P7-free")["status"], "done")
        self.assertAlmostEqual(self.store.grok_spent(), 3.10)
        with self.assertRaisesRegex(harness.Stop, "Grok checkpoint"):
            h.run_pilot_step("P7-steered")
        self.assertEqual(len(grok.calls), 1)


if __name__ == "__main__":
    unittest.main()


class ConsoleCurrency(Base):
    def test_console_reading_records_its_currency_defaulting_to_aud(self) -> None:
        h = self.make(Router())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(harness.main(["console", "--before", "17.55"], harness=h), 0)
            self.assertEqual(harness.main(["console", "--after", "7", "--currency", "USD"], harness=h), 0)
        lines = self.store.budget.read_text().splitlines()
        self.assertIn("before=17.55 currency=AUD", lines[-2])
        self.assertIn("after=7.0 currency=USD", lines[-1])
