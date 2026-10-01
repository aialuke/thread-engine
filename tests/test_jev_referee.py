#!/usr/bin/env python3
"""The Jev referee, with no network. Jev is a fake opener."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import jev_referee as referee  # noqa: E402

MISSING_LOCAL = REPO / "jev" / "no-such-local.yaml"


def policy() -> dict:
    return referee.load_policy(local_path=MISSING_LOCAL)


def run(event: dict, deps: dict) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = referee.dispatch(event, deps)
    return code, out.getvalue(), err.getvalue()


class Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args) -> bool:
        return False


class Transport:
    def __init__(self, answers: dict) -> None:
        self.answers = answers
        self.calls: list[dict] = []

    def __call__(self, request, timeout):
        self.calls.append(json.loads(request.data.decode("utf-8")))
        body = json.dumps({
            "model": "jev-1.13.0",
            "answers": self.answers,
            "usage": {"input_tokens": 20, "output_tokens": 8},
        }).encode("utf-8")
        return Response(body)


def completed(text: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=text, stderr="")


class Side:
    """Git, Keychain and HTTP stand-ins. Each records a call and can raise."""

    def __init__(self) -> None:
        self.git_calls: list[list[str]] = []
        self.key_calls = 0
        self.http_calls = 0

    def git(self, args):
        self.git_calls.append(list(args))
        raise AssertionError(f"git {args}")

    def key(self, *args, **kwargs):
        self.key_calls += 1
        raise AssertionError("keychain")

    def http(self, *args, **kwargs):
        self.http_calls += 1
        raise AssertionError("http")


def deps(tmp: Path, side: Side | None = None, **extra) -> dict:
    side = side or Side()
    base = {
        "policy": policy(),
        "questions": referee.load_questions(),
        "prompts": tmp / "prompts",
        "receipts": tmp / "decisions.jsonl",
        "git": side.git,
        "key_runner": side.key,
        "opener": side.http,
    }
    base.update(extra)
    return base


def receipts(tmp: Path) -> list[dict]:
    path = tmp / "decisions.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def shell(command: str, **extra) -> dict:
    event = {"toolName": "run_terminal_command", "toolInput": {"command": command},
             "workspaceRoot": "/tmp/repo"}
    event.update(extra)
    return event


class PolicyFile(unittest.TestCase):
    def test_latest_alias_is_ignored(self) -> None:
        base = yaml.safe_load((REPO / "jev" / "thresholds.yaml").read_text(encoding="utf-8"))
        base["model"] = "jev-latest"
        self.assertEqual(referee.merge_policy(base, {"model": "jev-latest"})["model"], "jev-1.13.0")

    def test_local_cannot_loosen_the_delete_bar(self) -> None:
        base = yaml.safe_load((REPO / "jev" / "thresholds.yaml").read_text(encoding="utf-8"))
        with self.assertRaises(referee.PolicyError):
            referee.merge_policy(base, {"forks": {"delete": {"unused_min": 0.5}}})
        with self.assertRaises(referee.PolicyError):
            referee.merge_policy(base, {"forks": {"delete": {"choice_confidence_min": 0.2}}})
        with self.assertRaises(referee.PolicyError):
            referee.merge_policy(base, {"skip": {"delete_dirs": ["node_modules", "src"]}})
        tightened = referee.merge_policy(base, {"forks": {"delete": {"unused_min": 0.9}}})
        self.assertEqual(tightened["forks"]["delete"]["unused_min"], 0.9)

    def test_hook_is_registered_once_for_tools(self) -> None:
        settings = (REPO / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.assertEqual(settings.count("scripts/jev_referee.py"), 2)
        self.assertEqual(settings.count('"matcher"'), 1)
        self.assertIn("spawn_subagent|Task|Agent|workflow", settings)
        self.assertFalse((REPO / ".grok" / "hooks").exists())


class EarlyExit(unittest.TestCase):
    def test_comment_edit_and_plain_bash_touch_nothing(self) -> None:
        events = (
            {"toolName": "search_replace", "toolInput": {
                "file_path": "a.py", "old_string": "# note", "new_string": "# note 2"}},
            shell("python3 -m unittest discover -s tests"),
            {"tool_name": "Edit", "tool_input": {
                "file_path": "a.py", "old_string": "# only a comment", "new_string": ""}},
        )
        for event in events:
            with self.subTest(tool=event.get("toolName") or event.get("tool_name")):
                side = Side()
                tmp = Path(self._tmp())
                code, out, _err = run(event, deps(tmp, side))
                self.assertEqual((code, out, side.git_calls, side.key_calls, side.http_calls), (0, "", [], 0, 0))
                self.assertEqual(receipts(tmp), [])

    def _tmp(self) -> str:
        import tempfile
        self.addCleanup(lambda: None)
        directory = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        return directory

    def test_small_replacement_is_not_a_delete(self) -> None:
        """A same-size rewrite is not a deletion. Moving ten lines down to one import is."""
        old = "def kept():\n    return 1\n"
        new = "def kept():\n    return 2\n"
        self.assertFalse(referee.edit_is_deletion(old, new, policy()))
        old_move = "\n".join(f"line {n}" for n in range(10))
        self.assertTrue(referee.edit_is_deletion(old_move, "from pkg import moved", policy()))


class HardRules(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.side = Side()

    def deny(self, command: str, words: str) -> None:
        code, out, err = run(shell(command, workspaceRoot=str(self.tmp)), deps(self.tmp, self.side))
        self.assertEqual(code, 2, command)
        self.assertIn(words, out)
        self.assertIn(words, err)
        self.assertNotIn("\n", json.loads(out)["reason"])
        row = receipts(self.tmp)[-1]
        self.assertEqual((row["would_allow"], row["did_allow"], row["fork"]), (False, False, "hard"))
        self.assertEqual(self.side.http_calls, 0)
        self.assertEqual(self.side.key_calls, 0)

    def test_wipe_is_denied_in_shadow_even_after_cd(self) -> None:
        self.deny("cd /tmp && rm -rf .", "rm -rf of workspace")
        self.deny("rm -rf /", "rm -rf of workspace")
        self.deny("rm -rf /*", "rm -rf of workspace")
        self.deny("rm -rf ~", "rm -rf of workspace")
        self.deny("rm -rf ~/", "rm -rf of workspace")
        self.deny("rm -rf .", "rm -rf of workspace")
        self.deny("rm -rf ./", "rm -rf of workspace")
        self.deny("rm -rf /.", "rm -rf of workspace")
        self.deny(f"rm -rf {self.tmp}", "rm -rf of workspace")
        self.deny("bash -c 'rm -rf /'", "rm -rf of workspace")

    def test_wrapped_and_split_wipes_still_deny(self) -> None:
        root = str(self.tmp)
        for command in (
            "bash -c 'rm -rf /'",
            "bash -c 'cd / && rm -rf /'",
            "bash -lc 'rm -rf /'",
            "env rm -rf /",
            "command rm -rf /",
            "sudo rm -rf /",
            "cd / && rm -rf *",
            "cd ~ && rm -rf *",
            f"cd {root} && rm -rf *",
            "rm -rf //",
            "rm -rf /usr/..",
        ):
            self.deny(command, "rm -rf of workspace")
        self.assertIsNone(referee.hard_rule("rm -rf ./node_modules", root))
        self.assertIsNone(referee.hard_rule("git push --force", root))
        self.assertIsNone(referee.hard_rule("cd /tmp && rm -rf *", root))

    def test_git_dir_and_force_push(self) -> None:
        self.deny("rm -rf .git", "deleting .git")
        self.deny("rm .git/config", "deleting .git")
        self.deny("git push --force origin main", "force push")
        self.deny("git push -f origin master", "force push")
        self.deny("git push origin +main", "force push")
        self.deny("git push --force origin HEAD:main", "force push")

    def test_lease_and_other_branches_are_not_this_rule(self) -> None:
        for command in ("git push --force-with-lease origin main", "git push --force origin feature"):
            side = Side()
            code, out, _err = run(shell(command), deps(self.tmp, side))
            self.assertEqual(code, 0, command)
            self.assertNotIn("deny", out)
            self.assertEqual(side.http_calls, 0)


class SkipAndForks(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    def remember(self, text: str = "Wire the referee.", session: str = "session-a", prompt_id: str = "turn-1") -> None:
        code, out, _err = run({
            "prompt": text, "sessionId": session, "promptId": prompt_id,
        }, deps(self.tmp))
        self.assertEqual((code, out), (0, ""))

    def git_with(self, files: dict[tuple[str, ...], str]):
        def runner(args):
            return completed(files.get(tuple(args), ""))
        return runner

    def test_trivial_commit_skips_and_scoped_prefix_does_not(self) -> None:
        numstat = {("diff", "--cached", "--numstat"): "15\t0\tfile.py\n"}
        side_skip = self.git_with(numstat)
        code, _out, _err = run(shell('git commit -m "fix: typo"'), deps(self.tmp, git=side_skip))
        self.assertEqual(code, 0)
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "trivial_commit")

        for message in ('docs: readme', 'chore: tidy'):
            code, _out, _err = run(shell(f'git commit -m "{message}"'), deps(self.tmp, git=self.git_with(numstat)))
            self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "trivial_commit", message)

        self.remember()
        transport = Transport(self._commit_answers(0.1, 0.1, 0.9))
        diff = {("diff", "--cached", "--numstat"): "15\t0\tfile.py\n",
                ("status", "--short"): "M file.py\n",
                ("diff", "--cached"): "+ a line\n"}
        code, _out, _err = run(
            shell('git commit -m "fix(scope): typo"', sessionId="session-a", promptId="turn-1"),
            deps(self.tmp, git=self.git_with(diff), opener=transport, key="test-key"),
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(set(transport.calls[0]["questions"]), {"in_scope", "extra_deletion", "needs_human"})
        self.assertEqual(transport.calls[0]["model"], "jev-1.13.0")
        self.assertIsNone(receipts(self.tmp)[-1]["skipped_reason"])

    def test_line_and_deletion_bounds(self) -> None:
        def skipped(numstat: str, message: str = "fix: typo") -> str | None:
            runner = self.git_with({("diff", "--cached", "--numstat"): numstat})
            run(shell(f'git commit -m "{message}"'), deps(self.tmp, git=runner))
            return receipts(self.tmp)[-1]["skipped_reason"]

        self.assertEqual(skipped("20\t0\tone.py\n"), "trivial_commit")
        self.assertNotEqual(skipped("21\t0\tone.py\n"), "trivial_commit")
        self.assertNotEqual(skipped("10\t1\tone.py\n"), "trivial_commit")
        self.assertNotEqual(skipped("1\t0\ta.py\n1\t0\tb.py\n"), "trivial_commit")

    def test_junk_delete_skips_and_a_mixed_rm_calls_once(self) -> None:
        code, _out, _err = run(shell("rm -rf node_modules/pkg .cache/x"), deps(self.tmp))
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "junk_delete")
        self.assertEqual(code, 0)

        self.remember("Remove the sample helper.")
        transport = Transport(self._delete_answers("keep", 0.2, 0.2))
        code, _out, _err = run(
            shell("rm node_modules/pkg src/app.py", sessionId="session-a", promptId="turn-1"),
            deps(self.tmp, opener=transport, key="test-key"),
        )
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(set(transport.calls[0]["questions"]), {"disposition", "unused"})
        self.assertIn("Remove the sample helper.", transport.calls[0]["state"]["user_request"])

    def test_junk_dotdot_is_not_a_skip(self) -> None:
        self.remember("Remove the helper.")
        transport = Transport(self._delete_answers("keep", 0.2, 0.2))
        for command in ("rm -rf node_modules/../../src/app.py", "rm -rf src/__pycache__/../secret.py"):
            code, out, _err = run(
                shell(command, sessionId="session-a", promptId="turn-1"),
                deps(self.tmp, opener=transport, key="test-key"),
            )
            self.assertEqual(code, 0, command)
            self.assertNotEqual(receipts(self.tmp)[-1]["skipped_reason"], "junk_delete", command)
            self.assertEqual(out, "")
        self.assertEqual(len(transport.calls), 2)
        code, _out, _err = run(shell("rm -rf ./node_modules"), deps(self.tmp))
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "junk_delete")
        self.assertIsNone(referee.hard_rule("rm -rf ./node_modules", str(self.tmp)))

    def test_dotdot_session_id_fails_open(self) -> None:
        planted = self.tmp / "prompt.txt"
        planted.write_text("stolen-prompt")
        transport = Transport(self._delete_answers("keep", 0.2, 0.2))
        code, out, _err = run({
            "prompt": "do not store this", "sessionId": "...", "promptId": "turn-1",
        }, deps(self.tmp, opener=transport))
        self.assertEqual((code, out), (0, ""))
        self.assertFalse((self.tmp / "prompts" / "...").exists())
        code, out, _err = run({
            "toolName": "spawn_subagent", "sessionId": "...", "promptId": "turn-1",
            "toolInput": {"prompt": "go", "description": "go"},
        }, deps(self.tmp, opener=transport, key="test-key"))
        self.assertEqual(code, 0)
        self.assertEqual(transport.calls, [])
        self.assertEqual(out, "")
        row = receipts(self.tmp)[-1]
        self.assertEqual(row["skipped_reason"], "bad_id")
        self.assertTrue(row["did_allow"])
        self.assertNotIn("stolen-prompt", (self.tmp / "decisions.jsonl").read_text(encoding="utf-8"))

    def test_spawn_low_confidence_is_shadow_allow(self) -> None:
        self.remember("Add the referee here.")
        transport = Transport({"route": {"type": "choice", "choice": "cheap_explore", "confidence": 0.42,
                                          "probabilities": {"cheap_explore": 0.4, "no_spawn": 0.3,
                                                            "main_default": 0.2, "careful_plan": 0.1}}})
        code, out, _err = run({
            "toolName": "spawn_subagent", "sessionId": "session-a", "promptId": "turn-1",
            "toolInput": {"prompt": "write the hook", "description": "implement"},
        }, deps(self.tmp, opener=transport, key="test-key"))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(set(transport.calls[0]["questions"]["route"]["criteria"]),
                         {"main_default", "cheap_explore", "careful_plan", "no_spawn"})
        row = receipts(self.tmp)[-1]
        self.assertEqual((row["would_allow"], row["did_allow"], row["mode"]), (False, True, "shadow"))
        self.assertEqual(row["answers"]["route"]["choice"], "cheap_explore")
        self.assertIn("Who should do this work?", row["questions"]["route"])

    def test_spawn_active_denies_in_one_line(self) -> None:
        self.remember()
        chosen = policy()
        chosen["mode"] = "active"
        transport = Transport({"route": {"type": "choice", "choice": "cheap_explore", "confidence": 0.42,
                                          "probabilities": {}}})
        code, out, err = run({
            "toolName": "spawn_subagent", "sessionId": "session-a", "promptId": "turn-1",
            "toolInput": {"prompt": "write it", "description": "implement"},
        }, deps(self.tmp, policy=chosen, opener=transport, key="test-key"))
        self.assertEqual(code, 2)
        reason = json.loads(out)["reason"]
        self.assertEqual(reason, "spawn no_spawn confidence=0.42")
        self.assertNotIn("\n", reason)
        self.assertEqual(err.strip(), reason)
        self.assertFalse(receipts(self.tmp)[-1]["did_allow"])

    def test_commit_nouls_and_delete_thresholds(self) -> None:
        rules = policy()
        allow, line = referee.apply_policy("commit", self._commit_answers(0.1, 0.1, 0.9), rules)
        self.assertTrue(allow)
        self.assertIn("ask_luke", line)
        ask, _line = referee.apply_policy("commit", self._commit_answers(0.7, 0.1, 0.9), rules)
        self.assertFalse(ask)
        ask, _line = referee.apply_policy("commit", self._commit_answers(0.1, 0.7, 0.9), rules)
        self.assertFalse(ask)
        ask, _line = referee.apply_policy("commit", self._commit_answers(0.1, 0.1, 0.49), rules)
        self.assertFalse(ask)

        delete, _line = referee.apply_policy("delete", self._delete_answers("delete", 0.85, 0.80), rules)
        self.assertTrue(delete)
        keep, line = referee.apply_policy("delete", self._delete_answers("delete", 0.84, 0.99), rules)
        self.assertFalse(keep)
        self.assertIn("keep", line)
        keep, line = referee.apply_policy("delete", self._delete_answers("delete", 0.99, 0.79), rules)
        self.assertFalse(keep)
        ask, line = referee.apply_policy("delete", self._delete_answers("ask_luke", 0.99, 0.99), rules)
        self.assertFalse(ask)
        self.assertIn("ask_luke", line)

    def test_prompt_is_this_session_only(self) -> None:
        self.remember("alpha-token-7f3a", session="session-a", prompt_id="turn-1")
        self.remember("beta-token-9c2e", session="session-b", prompt_id="turn-9")
        names = {path.name for path in (self.tmp / "prompts").rglob("*") if path.is_file()}
        self.assertNotIn("latest", names)
        transport = Transport({"route": {"type": "choice", "choice": "no_spawn", "confidence": 0.9,
                                          "probabilities": {}}})
        run({
            "toolName": "spawn_subagent", "sessionId": "session-a", "promptId": "turn-1",
            "toolInput": {"prompt": "go", "description": "go"},
        }, deps(self.tmp, opener=transport, key="test-key"))
        self.assertIn("alpha-token-7f3a", transport.calls[0]["state"]["user_request"])
        self.assertNotIn("beta-token-9c2e", json.dumps(transport.calls[0]["state"]))

    def test_missing_session_does_not_call(self) -> None:
        transport = Transport({})
        code, out, _err = run({
            "toolName": "spawn_subagent", "toolInput": {"prompt": "go", "description": "go"},
        }, deps(self.tmp, opener=transport, key="test-key"))
        self.assertEqual(code, 0)
        self.assertEqual(transport.calls, [])
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "missing_session")
        self.assertEqual(out, "")

    def test_missing_key_and_timeout_fail_open(self) -> None:
        self.remember()
        event = {
            "toolName": "spawn_subagent", "sessionId": "session-a", "promptId": "turn-1",
            "toolInput": {"prompt": "go", "description": "go"},
        }

        def no_key(*_args, **_kwargs):
            return subprocess.CompletedProcess([], 1, stdout="", stderr="locked")

        code, out, _err = run(event, deps(self.tmp, key_runner=no_key))
        self.assertEqual(out, "")
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "missing_key")
        self.assertTrue(receipts(self.tmp)[-1]["did_allow"])

        def time_out(_request, timeout):
            raise TimeoutError

        code, out, _err = run(event, deps(self.tmp, opener=time_out, key="test-key"))
        self.assertEqual(out, "")
        self.assertEqual(receipts(self.tmp)[-1]["skipped_reason"], "timeout")

    def test_secret_does_not_leave_the_process(self) -> None:
        secret = "super-secret-key-value"
        diff = (
            "diff --git a/.env b/.env\n"
            "--- a/.env\n+++ b/.env\n"
            "@@ -1 +1 @@\n-API_TOKEN=hide-me\n+API_TOKEN=hide-me-2\n"
            "diff --git a/scripts/jev_referee.py b/scripts/jev_referee.py\n"
            "+token = \"super-secret-key-value\"\n"
        )
        files = {("diff", "--cached"): diff, ("status", "--short"): "M scripts/jev_referee.py\n"}
        self.remember("Commit the referee.")
        transport = Transport(self._commit_answers(0.1, 0.1, 0.9))
        run(shell('git commit -m "feat: referee"', sessionId="session-a", promptId="turn-1"),
            deps(self.tmp, git=self.git_with(files), opener=transport, key=secret))
        posted = json.dumps(transport.calls[0])
        stored = (self.tmp / "decisions.jsonl").read_text(encoding="utf-8")
        for blob in (posted, stored):
            self.assertNotIn(secret, blob)
            self.assertNotIn("hide-me", blob)
        self.assertIn("[redacted]", posted)

    def _commit_answers(self, extra: float, human: float, scope: float) -> dict:
        return {
            "extra_deletion": {"type": "noul", "noul": extra},
            "needs_human": {"type": "noul", "noul": human},
            "in_scope": {"type": "noul", "noul": scope},
        }

    def _delete_answers(self, choice: str, unused: float, confidence: float) -> dict:
        return {
            "disposition": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": {}},
            "unused": {"type": "noul", "noul": unused},
        }


class DryRun(unittest.TestCase):
    def test_dry_run_writes_one_complete_receipt_per_fork_without_a_key(self) -> None:
        """--dry-run builds receipts too; a changed receipt shape must not break it unnoticed."""
        import shutil
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        saved = (referee.RECEIPTS, referee.read_key)
        self.addCleanup(lambda: (setattr(referee, "RECEIPTS", saved[0]), setattr(referee, "read_key", saved[1])))

        def no_key(*_args, **_kwargs):
            raise referee.CallFailed("keychain_missing")

        referee.RECEIPTS = tmp / "decisions.jsonl"
        referee.read_key = no_key
        with contextlib.redirect_stdout(io.StringIO()):
            referee.dry_run()
        rows = receipts(tmp)
        self.assertEqual([row["fork"] for row in rows], ["spawn", "commit", "delete"])
        for row in rows:
            self.assertEqual(
                set(row),
                {"ts", "fork", "model", "mode", "tool", "state_hash", "state_token_estimate", "questions",
                 "answers", "policy_version", "would_allow", "did_allow", "skipped_reason"},
            )
            self.assertEqual((row["tool"], row["skipped_reason"]), ("dry_run", "keychain_missing"))


if __name__ == "__main__":
    unittest.main()
