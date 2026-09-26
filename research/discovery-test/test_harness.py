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
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
        self.store.append(self.store.requests, {"stage": "stage1", "estimated_cost": 3.6})
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
        first = [{"id": f"p{n}", "opening": texts[n][:30], "relevant": r, "real": 2, "useful": 1, "type": "genuine"}
                 for n, r in enumerate([2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])]
        path = self.root / "first.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in first))
        out = h.ingest_scores(2, path, seed=1)
        self.assertEqual(out["second_score"]["positives_and_unclear"], 3)
        second_ids = {r["id"] for r in h.store.rows(h.store.root / "second-stage2.jsonl")}
        self.assertTrue({"p0", "p1", "p2"} <= second_ids)
        self.assertNotIn("relevant", h.store.rows(h.store.root / "second-stage2.jsonl")[0])   # blind to the first scores
        second = [{"id": i, "opening": texts[int(i[1:])][:30], "relevant": 0 if i == "p1" else
                   [r for r in first if r["id"] == i][0]["relevant"], "real": 2, "useful": 1, "type": "genuine"} for i in second_ids]
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
        rows = [{"id": "p61864f", "opening": "@Alexfeinberg What do you use i", "relevant": 1, "real": 2, "useful": 2},
                {"id": "p5af09d", "opening": "Still have Apple devices and so", "relevant": 2, "real": 2, "useful": 2},
                {"id": "p5af09d", "opening": "Still have Apple devices and so", "relevant": 0, "real": 0, "useful": 0},
                {"id": "pzzzzzz", "opening": "nothing like any post at all xx", "relevant": 2, "real": 2, "useful": 2}]
        kept, problems = harness.check_scores(corpus, rows)
        self.assertEqual([(r["id"], r.get("corrected_from")) for r in kept], [("p61864d", "p61864f"), ("p5af09d", None)])
        self.assertTrue(any("corrected" in p for p in problems))
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
            self.assertEqual(set(line), {"id", "idea", "text"})
            self.assertNotEqual(line["id"], "5")
            key = json.loads((Path(tmp) / "corpus-key-stage1.json").read_text())
            self.assertEqual(key[line["id"]]["post_id"], "5")


if __name__ == "__main__":
    unittest.main()
