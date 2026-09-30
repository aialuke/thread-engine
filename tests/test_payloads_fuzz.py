#!/usr/bin/env python3
"""No wrong-typed Payload field may escape as a traceback: the six payload commands refuse it as a LoopError.

Each field of a valid Payload is replaced in turn (null, a number, text, an empty list, an empty object) or
removed. loop.main only catches LoopError, so anything else that escapes fails the case.
"""

from __future__ import annotations

import copy
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from test_loop import T0, LoopCase, hours

import loop  # noqa: E402  (after test_loop, which puts scripts/ on the path; the loop/ data dir would shadow it)

VARIANTS = [None, 1, "x", [], {}]
ROW = {"views": 1, "likes": 1, "reposts": 0, "quotes": 0, "replies": 0, "bookmarks": 0}
BASE = {
    "record-post": {
        "root_id": "1000000001", "slug": "s", "format": "single-tip", "lane": "main", "posted_at": T0,
        "retrospective": False, "made_in_repo": True, "experiment": None, "arm": "none", "hypothesis": "h",
        "cards": [{"id": "1000000009", "text": "t"}], "media": [], "ai_media": False, "production_minutes": 3,
        "edits": [{"class": "preference"}], "draft": "d", "auto": False},
    "record-snapshot": {
        "root_id": "1000000001", "observed_at": hours(48), "repliers": ["a"], "root": ROW, "organic": {"likes": 1},
        "cards": [{"views": 2}], "followers": 3, "source": "s", "raw_file": "f", "repliers_complete": True},
    "record-activity": {
        "stage": "48h", "observed_at": T0,
        "items": [{"id": "1000000005", "kind": "original", "created_at": T0, "conversation_id": "1000000005",
                   "public": {"likes": 1}, "organic": {"likes": 1}, "topics": ["x"], "text": "t"}],
        "cursor": {"read48_until": T0, "final_until": T0}},
    "record-interactions": {
        "observed_at": T0, "self_ids": ["1"], "since_id": "5",
        "mentions": [{"author_id": "9", "id": "1", "conversation_id": "100", "created_at": T0, "replied_to": "5"}],
        "reply_targets": [{"user_id": "7", "item_id": "200", "at": T0}]},
    "record-followers": {"observed_at": T0, "self_ids": ["1"], "ids": ["2", "3"], "total": 2, "verified": 1},
    "open-experiment": {
        "question": "q", "treatment": "t", "control": "c", "primary": "bookmarks", "effect": 1.5,
        "cohort": ["2000000000", "2000000001", "2000000002"], "reference_facts": []},
}


def paths(obj, prefix=()):
    yield prefix
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from paths(value, prefix + (key,))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from paths(value, prefix + (index,))


def mutate(obj, path, value, delete=False):
    obj = copy.deepcopy(obj)
    if not path:
        return value
    cur = obj
    for key in path[:-1]:
        cur = cur[key]
    if delete:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return obj


class WrongTypedFields(LoopCase):
    def fresh(self, command: str) -> None:
        """A new repo holding whatever the command needs to reach its payload checks."""
        self.tmp.cleanup()
        self.setUp()
        if command == "record-snapshot":
            self.post("1000000001", T0)
        if command == "open-experiment":
            for i in range(3):
                root_id = f"20000000{i:02d}"
                self.post(root_id, hours(-500 + i), retrospective=True, made_in_repo=False)
                self.snap(root_id, hours(-400 + i), 1000, bookmarks=100 * (i + 1))

    def run_case(self, command: str, payload) -> tuple[int, str]:
        args = ["--root", str(self.root), command, "--json", self.payload(payload)]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = loop.main(args)
        return code, err.getvalue()

    def test_the_valid_payloads_are_valid(self) -> None:
        for command, base in BASE.items():
            with self.subTest(command=command):
                self.fresh(command)
                self.assertEqual(self.run_case(command, base)[0], 0)

    def test_no_field_escapes_as_a_traceback(self) -> None:
        escaped = []
        for command, base in BASE.items():
            for path in paths(base):
                cases = [(value, False) for value in VARIANTS]
                cases += [(None, True)] if path and isinstance(path[-1], str) else []
                for value, delete in cases:
                    self.fresh(command)
                    try:
                        code, err = self.run_case(command, mutate(base, path, value, delete))
                    except Exception as exc:  # anything but a LoopError is the bug
                        escaped.append(f"{command} {'.'.join(map(str, path)) or '<payload>'} "
                                       f"{'deleted' if delete else repr(value)}: {type(exc).__name__}: {exc}")
                        continue
                    if code not in (0, 1) or (code == 1 and "error" not in json.loads(err)):
                        escaped.append(f"{command} {path} {value!r}: exit {code}")
        self.assertEqual(escaped, [], f"{len(escaped)} escaped:\n" + "\n".join(escaped[:20]))


if __name__ == "__main__":
    unittest.main()
