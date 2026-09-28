#!/usr/bin/env python3
"""The design-card vote, with no network. Jev is a fake opener, the Keychain a fake runner."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import jev_design_vote as vote  # noqa: E402

KEY = "sk-test-not-a-real-key"


def card(**over) -> dict:
    base = {
        "model": vote.PINNED_MODEL,
        "state": {"decision": "When the app reads X live."},
        "questions": {
            "live_reads": {
                "type": "choice",
                "instructions": "When should the app read X live?",
                "criteria": {"read_on_open": "On open.", "poll": "On a timer.", "ask_luke": "None fit."},
            }
        },
    }
    base.update(over)
    return base


def answer(choice="read_on_open", probs=None) -> dict:
    probs = probs or {"read_on_open": 0.74, "poll": 0.04, "ask_luke": 0.22}
    return {
        "model": vote.PINNED_MODEL,
        "answers": {"live_reads": {"type": "choice", "choice": choice, "confidence": 0.65, "probabilities": probs}},
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }


class Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def keychain(args, **kwargs):
    return subprocess.CompletedProcess(args, 0, stdout=KEY + "\n", stderr="")


def no_key(args, **kwargs):
    return subprocess.CompletedProcess(args, 44, stdout="", stderr="not found")


class Opener:
    def __init__(self, *results) -> None:
        self.results = list(results)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return Response(json.dumps(result).encode("utf-8"))


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(vote.ENDPOINT, code, "err", {}, io.BytesIO(b"{}"))


def run(card_obj, opener, runner=keychain) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "card.json"
        path.write_text(json.dumps(card_obj) if not isinstance(card_obj, str) else card_obj, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = vote.main([str(path)], runner=runner, opener=opener, sleep=lambda s: None)
    return code, out.getvalue(), err.getvalue()


class Vote(unittest.TestCase):
    def test_good_vote_prints_answers_and_sends_the_card_as_is(self):
        opener = Opener(answer())
        code, out, err = run(card(), opener)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["answers"]["live_reads"]["choice"], "read_on_open")
        sent = opener.requests[0]
        self.assertEqual(sent.full_url, vote.ENDPOINT)
        self.assertEqual(sent.get_header("Authorization"), f"Bearer {KEY}")
        self.assertEqual(json.loads(sent.data), card())

    def test_key_never_printed(self):
        for opener in (Opener(answer()), Opener(http_error(401)), Opener(answer(choice="invented"))):
            code, out, err = run(card(), opener)
            self.assertNotIn(KEY, out + err)

    def test_retries_429_and_529_then_succeeds(self):
        opener = Opener(http_error(429), http_error(529), answer())
        code, _, err = run(card(), opener)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(opener.requests), 3)

    def test_gives_up_after_retries(self):
        code, out, err = run(card(), Opener(http_error(529), http_error(529), http_error(529)))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("http_529", err)

    def test_other_http_errors_fail_without_retry(self):
        opener = Opener(http_error(422))
        code, _, err = run(card(), opener)
        self.assertEqual(code, 2)
        self.assertIn("http_422", err)
        self.assertEqual(len(opener.requests), 1)

    def test_missing_key_sends_nothing(self):
        opener = Opener()
        code, _, err = run(card(), opener, runner=no_key)
        self.assertEqual(code, 2)
        self.assertIn("missing_key", err)
        self.assertEqual(opener.requests, [])

    def test_answer_outside_the_card_is_no_vote(self):
        code, out, err = run(card(), Opener(answer(choice="invented")))
        self.assertEqual(code, 2)
        self.assertEqual(out, "")

    def test_probabilities_must_sum_to_one(self):
        code, _, _ = run(card(), Opener(answer(probs={"read_on_open": 0.5, "poll": 0.1, "ask_luke": 0.1})))
        self.assertEqual(code, 2)

    def test_missing_answer_is_no_vote(self):
        payload = answer()
        payload["answers"] = {}
        code, _, _ = run(card(), Opener(payload))
        self.assertEqual(code, 2)


class Card(unittest.TestCase):
    def refused(self, card_obj) -> str:
        opener = Opener()
        code, out, err = run(card_obj, opener)
        self.assertEqual(code, 1)
        self.assertEqual(opener.requests, [])
        return err

    def test_wrong_model_refused(self):
        self.assertIn("pin", self.refused(card(model="jev-latest")))

    def test_extra_top_level_field_refused(self):
        bad = card()
        bad["policy"] = "lean"
        self.refused(bad)

    def test_bad_json_refused(self):
        self.refused("{not json")

    def test_empty_state_refused(self):
        self.refused(card(state=""))

    def test_choice_needs_two_options(self):
        self.refused(card(questions={"q": {"type": "choice", "instructions": "x", "criteria": {"a": "only"}}}))

    def test_unknown_type_refused(self):
        self.refused(card(questions={"q": {"type": "rank", "instructions": "x", "criteria": {}}}))

    def test_score_level_count(self):
        self.refused(card(questions={"q": {"type": "score", "instructions": "x", "criteria": ["one"]}}))

    def test_noul_criteria_keys(self):
        self.refused(card(questions={"q": {"type": "noul", "instructions": "x", "criteria": {"maybe": "y"}}}))

    def test_noul_without_criteria_is_fine(self):
        noul = {"q": {"type": "noul", "instructions": "Is it ready?"}}
        payload = {"model": vote.PINNED_MODEL, "answers": {"q": {"type": "noul", "noul": 0.8}}}
        code, _, err = run(card(questions=noul), Opener(payload))
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
