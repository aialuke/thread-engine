#!/usr/bin/env python3
"""One Jev vote on a design card. Jev only votes; the agent applies the card's policy.

    python3 scripts/jev_design_vote.py /tmp/jev-card.json

The card is data: {"model", "state", "questions"}. It is checked before anything
is sent, and refused if the model isn't the pinned one or a question is malformed.
The TypeSafe key is read from the Keychain inside this process and is never
printed. Nothing is written: no receipt, no log.

Exit 0 with the answers printed as JSON, 1 when the card is refused, 2 when the
call fails.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from jev_referee import ENDPOINT, PINNED_MODEL, CallFailed, load_base_policy, read_key

TYPES = ("choice", "noul", "score")
MAX_CHOICE_OPTIONS = 255  # docs.typesafe.ai/primitives/choice
SCORE_LEVELS = (2, 10)  # docs.typesafe.ai/api
RETRY_STATUS = (429, 529)  # docs.typesafe.ai/api: back off, don't retry at once
RETRY_WAITS = (1.0, 2.0)


class CardRefused(Exception):
    pass


def _text(value) -> bool:
    return (isinstance(value, str) and value.strip() != "") or (isinstance(value, (dict, list)) and len(value) > 0)


def check_question(name: str, question) -> None:
    if not isinstance(question, dict):
        raise CardRefused(f"question {name} is not an object")
    kind = question.get("type")
    if kind not in TYPES:
        raise CardRefused(f"question {name} has type {kind!r}; expected one of {', '.join(TYPES)}")
    if not _text(question.get("instructions")):
        raise CardRefused(f"question {name} has no instructions")
    criteria = question.get("criteria")
    if kind == "choice":
        if not isinstance(criteria, dict) or len(criteria) < 2:
            raise CardRefused(f"choice {name} needs at least two options in criteria")
        if len(criteria) > MAX_CHOICE_OPTIONS:
            raise CardRefused(f"choice {name} has more than {MAX_CHOICE_OPTIONS} options")
    elif kind == "score":
        low, high = SCORE_LEVELS
        if not isinstance(criteria, list) or not low <= len(criteria) <= high:
            raise CardRefused(f"score {name} needs {low}-{high} levels in criteria")
    elif criteria is not None and (not isinstance(criteria, dict) or set(criteria) - {"true", "false"}):
        raise CardRefused(f"noul {name} criteria may only have true and false")


def load_card(path: Path, policy: dict) -> dict:
    try:
        card = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CardRefused(f"can't read the card: {exc.__class__.__name__}") from None
    if not isinstance(card, dict) or set(card) != {"model", "state", "questions"}:
        raise CardRefused("the card must have exactly model, state and questions")
    if card["model"] != PINNED_MODEL:
        raise CardRefused(f"model is {card['model']!r}; the pin is {PINNED_MODEL}")
    if not _text(card["state"]):
        raise CardRefused("state is empty")
    questions = card["questions"]
    if not isinstance(questions, dict) or not questions:
        raise CardRefused("questions is empty")
    for name, question in questions.items():
        check_question(name, question)
    tokens = policy["tokens"]
    size = len(json.dumps(card, ensure_ascii=False)) // tokens["chars_per_token"]
    if size > tokens["max_request"]:
        raise CardRefused(f"the card is about {size} tokens; the limit is {tokens['max_request']}")
    return card


def post(card: dict, key: str, timeout: float, opener, sleep) -> dict:
    data = json.dumps(card, ensure_ascii=False).encode("utf-8")
    for attempt in range(len(RETRY_WAITS) + 1):
        request = urllib.request.Request(
            ENDPOINT, data=data, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with opener(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in RETRY_STATUS and attempt < len(RETRY_WAITS):
                sleep(RETRY_WAITS[attempt])
                continue
            raise CallFailed(f"http_{exc.code}") from None
        except (TimeoutError, socket.timeout):
            raise CallFailed("timeout") from None
        except urllib.error.URLError as exc:
            timed_out = isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout))
            raise CallFailed("timeout" if timed_out else "network") from None
        except (json.JSONDecodeError, OSError):
            raise CallFailed("bad_response") from None
    raise CallFailed("retries_exhausted")


def _probability(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def check_answers(card: dict, payload) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("answers"), dict):
        raise CallFailed("bad_response")
    answers = payload["answers"]
    for name, question in card["questions"].items():
        got = answers.get(name)
        if not isinstance(got, dict) or got.get("type") != question["type"]:
            raise CallFailed(f"missing_answer_{name}")
        if question["type"] == "noul":
            ok = _probability(got.get("noul"))
        else:
            probs = got.get("probabilities")
            ok = (
                _probability(got.get("confidence"))
                and isinstance(probs, dict)
                and all(_probability(p) for p in probs.values())
                and abs(sum(probs.values()) - 1.0) < 0.02
            )
            if ok and question["type"] == "choice":
                ok = got.get("choice") in question["criteria"] and set(probs) <= set(question["criteria"])
        if not ok:
            raise CallFailed(f"bad_answer_{name}")
    return payload


def main(argv: list[str], runner=subprocess.run, opener=urllib.request.urlopen, sleep=time.sleep) -> int:
    if len(argv) != 1:
        print("usage: python3 scripts/jev_design_vote.py <card.json>", file=sys.stderr)
        return 1
    policy = load_base_policy()
    try:
        card = load_card(Path(argv[0]), policy)
    except CardRefused as exc:
        print(f"card refused: {exc}. Nothing was sent.", file=sys.stderr)
        return 1
    try:
        key = read_key(runner)
        payload = check_answers(card, post(card, key, policy["timeout_seconds"], opener, sleep))
    except CallFailed as exc:
        print(f"Jev call failed: {exc.reason}. No vote.", file=sys.stderr)
        return 2
    print(json.dumps({"model": payload.get("model"), "answers": payload["answers"], "usage": payload.get("usage")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
