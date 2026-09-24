#!/usr/bin/env python3
"""Stdlib checks for draft.py and post_thread.py."""

from __future__ import annotations

import ast
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

FORBIDDEN_TOP = {
    "urllib",
    "http",
    "socket",
    "ssl",
    "requests",
    "httpx",
    "tweepy",
    "aiohttp",
    "urllib3",
    "ftplib",
    "smtplib",
}


def _imported_tops(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _reads_environ(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {"environ", "getenv"}:
            return True
        if isinstance(node, ast.Name) and node.id == "getenv":
            return True
    return False


SWAP_HEADER = "PAID → FREE\nFinding free creator tools that actually hold up."
POST_ONE = SWAP_HEADER + """

Photoshop → Photopea
▷ Browser editor. Opens PSDs.

Premiere Pro → DaVinci Resolve
▷ Edit, colour, and audio. No watermark.

After Effects → Blender
▷ 3D and motion. Modelling, animation, render.

Streamlabs Ultra → OBS Studio
▷ Record and stream. Scenes, camera, separate audio.

Procreate → Krita
▷ Painting and illustration. Desktop and Android."""


class ImportGate(unittest.TestCase):
    def test_post_thread_has_no_http_imports(self) -> None:
        tops = _imported_tops(SCRIPTS / "post_thread.py")
        self.assertEqual(FORBIDDEN_TOP & tops, set())

    def test_draft_has_no_http_imports(self) -> None:
        tops = _imported_tops(SCRIPTS / "draft.py")
        self.assertEqual(FORBIDDEN_TOP & tops, set())

    def test_draft_does_not_import_subprocess(self) -> None:
        tops = _imported_tops(SCRIPTS / "draft.py")
        self.assertNotIn("subprocess", tops)

    def test_post_thread_does_not_read_environ(self) -> None:
        self.assertFalse(_reads_environ(SCRIPTS / "post_thread.py"))


class ScriptBehavior(unittest.TestCase):
    def setUp(self) -> None:
        import importlib.util

        def load(name: str):
            spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod

        self.draft = load("draft")
        self.post = load("post_thread")
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run(self, func, argv: list[str], **kwargs: object) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = func(argv, **kwargs)
        return code, out.getvalue(), err.getvalue()

    def test_draft_prints_grok_command(self) -> None:
        code, out, err = self._run(self.draft.main, ["smart-tv"])
        self.assertEqual(code, 0)
        self.assertEqual(out, 'grok -p "/draft-thread smart-tv"\n')
        self.assertEqual(err, "")
        self.assertFalse((self.root / "drafts").exists())

    def test_draft_rejects_bad_slug(self) -> None:
        code, out, err = self._run(self.draft.main, ["Not A Slug"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("invalid slug", err)

    def test_post_refuses_without_approved(self) -> None:
        draft = self.root / "demo"
        draft.mkdir()
        (draft / "01-hook.md").write_text("SECRET HOOK\n", encoding="utf-8")
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 2)
        self.assertEqual(out, "human gate\n")
        self.assertNotIn("SECRET HOOK", out)
        self.assertEqual(err, "")
        self.assertFalse((draft / "POST.txt").exists())
        self.assertFalse((self.root / "shipped").exists())

    def test_post_missing_folder(self) -> None:
        code, out, _err = self._run(self.post.main, [str(self.root / "missing")])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")

    def test_post_refuses_approved_folder_with_no_cards(self) -> None:
        draft = self.root / "empty"
        draft.mkdir()
        (draft / "APPROVED").write_text("", encoding="utf-8")
        (draft / "thread.md").write_text("NOT A CARD\n", encoding="utf-8")
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("no numbered cards", err)

    def _approved_draft(self) -> Path:
        draft = self.root / "topic"
        draft.mkdir()
        (draft / "02-card.md").write_text("CARD\nline\n", encoding="utf-8")
        (draft / "01-hook.md").write_text(
            "Same TV. The film stopped looking like a soap.\n",
            encoding="utf-8",
        )
        (draft / "thread.md").write_text("IGNORE\n", encoding="utf-8")
        images = draft / "images"
        images.mkdir()
        (images / "hook-before-after.jpg").write_bytes(b"jpg")
        (images / "hook-master.jpg").write_bytes(b"jpg")
        (self.root / "shipped").mkdir()
        self._approve(draft)
        return draft

    def _approve(self, draft: Path) -> None:
        """What the /approve hook writes: the digest of the cards as they are now."""
        digest = self.post.cards_digest(self.post.cards(draft))
        (draft / "APPROVED").write_text(f"cards-sha256: {digest}\n", encoding="utf-8")

    def test_post_writes_run_sheet(self) -> None:
        draft = self._approved_draft()
        thread_before = (draft / "thread.md").read_text(encoding="utf-8")
        code, out, err = self._run(self.post.main, [str(draft)])
        sheet = (draft / "POST.txt").read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, sheet)
        self.assertIn("01-hook.md", sheet)
        self.assertIn("images/hook-before-after.jpg", sheet)
        self.assertNotIn("Hook open:", sheet)
        self.assertNotIn("Most", sheet)
        self.assertNotIn("IGNORE", sheet)
        self.assertNotIn("hook-master.jpg", sheet)
        self.assertNotIn("Long posts.", sheet)
        self.assertEqual((draft / "thread.md").read_text(encoding="utf-8"), thread_before)
        self.assertEqual(list((self.root / "shipped").iterdir()), [])

    def test_long_post_note(self) -> None:
        draft = self._approved_draft()
        (draft / "02-card.md").write_text("y" * 281, encoding="utf-8")
        self._approve(draft)
        _code, out, _err = self._run(self.post.main, [str(draft)])
        self.assertIn("Long posts.", out)
        self.assertNotIn("yyy", out)

    def test_json_still_parses_and_refreshes_sheet(self) -> None:
        draft = self._approved_draft()
        code, out, err = self._run(self.post.main, [str(draft), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(
            payload["tweets"],
            [
                {
                    "text": "Same TV. The film stopped looking like a soap.",
                    "media": ["images/hook-before-after.jpg"],
                },
                {"text": "CARD\nline", "media": []},
            ],
        )
        sheet = (draft / "POST.txt").read_text(encoding="utf-8")
        self.assertIn("01-hook.md", sheet)
        self.assertNotIn("Hook open:", sheet)
        self.assertNotIn("Most", sheet)

    def test_explicit_dry_run_matches_default(self) -> None:
        draft = self._approved_draft()
        code_default, out_default, _err = self._run(self.post.main, [str(draft)])
        code_flag, out_flag, _err = self._run(self.post.main, [str(draft), "--dry-run"])
        self.assertEqual(code_default, 0)
        self.assertEqual(code_flag, 0)
        self.assertEqual(out_default, out_flag)

    def test_no_dry_run_writes_nothing(self) -> None:
        draft = self._approved_draft()
        code, out, err = self._run(self.post.main, [str(draft), "--no-dry-run"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("v1 does not call the X API", err)
        self.assertFalse((draft / "POST.txt").exists())
        self.assertEqual(list((self.root / "shipped").iterdir()), [])

    def test_card_media_hints_and_hook_override(self) -> None:
        draft = self._approved_draft()
        (draft / "01-hook.md").write_text(
            "HOOK ![shot](images/custom.png) and `notes.txt`\n",
            encoding="utf-8",
        )
        (draft / "02-card.md").write_text(
            "See `images/menu.png` and `Settings`.\n",
            encoding="utf-8",
        )
        self._approve(draft)
        code, out, _err = self._run(self.post.main, [str(draft), "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["tweets"][0]["media"], ["images/custom.png"])
        self.assertEqual(payload["tweets"][1]["media"], ["images/menu.png"])

    def test_copy_hook_text_and_reveal_image(self) -> None:
        draft = self._approved_draft()
        copied: list[bytes] = []
        revealed: list[Path] = []
        code, out, err = self._run(
            self.post.main,
            [str(draft), "--copy", "1"],
            copy_text=copied.append,
            reveal=revealed.append,
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(
            copied, ["Same TV. The film stopped looking like a soap.".encode("utf-8")]
        )
        self.assertEqual(revealed, [draft / "images" / "hook-before-after.jpg"])
        self.assertEqual(
            out,
            "copied post 1 of 2 from 01-hook.md. "
            "attach images/hook-before-after.jpg\n"
            "open: Same TV. The film stopped looking like a soap.\n"
            f"next: python3 scripts/post_thread.py {draft} --copy 2\n",
        )
        sheet = (draft / "POST.txt").read_text(encoding="utf-8")
        self.assertNotIn("Hook open:", sheet)
        self.assertNotIn("Most", sheet)

    def test_result_open_skips_setup_day_warning(self) -> None:
        draft = self._approved_draft()
        opening = (
            "Same TV. The film stopped looking like a soap.\n"
            "\n"
            "Most 4K TVs get set up on delivery day and Picture is never opened again.\n"
        )
        (draft / "01-hook.md").write_text(opening, encoding="utf-8")
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertNotIn("Hook open:", out)
        self.assertNotIn("Same TV.", out)
        copied: list[bytes] = []
        code, copy_out, err = self._run(
            self.post.main,
            [str(draft), "--copy", "1"],
            copy_text=copied.append,
            reveal=lambda _path: None,
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertEqual(copied, [opening[:-1].encode("utf-8")])
        self.assertIn("open: Same TV. The film stopped looking like a soap.\n", copy_out)
        self.assertNotIn("open: Most ", copy_out)
        self.assertNotIn("Hook open:", copy_out)
        sheet = (draft / "POST.txt").read_text(encoding="utf-8")
        self.assertNotIn("Hook open:", sheet)
        self.assertNotIn("Same TV.", sheet)
        self.assertNotIn("Most 4K TVs", sheet)

    def test_neglect_without_most_stays_silent(self) -> None:
        draft = self._approved_draft()
        (draft / "01-hook.md").write_text(
            "Gateway plugged in on install day.\n",
            encoding="utf-8",
        )
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertNotIn("Hook open:", out)
        self.assertNotIn("Gateway plugged in on install day.", out)

    def test_copy_last_post_has_no_next(self) -> None:
        draft = self._approved_draft()
        copied: list[bytes] = []
        code, out, _err = self._run(
            self.post.main,
            [str(draft), "--copy", "2"],
            copy_text=copied.append,
            reveal=lambda _path: None,
        )
        self.assertEqual(code, 0)
        self.assertEqual(copied, [b"CARD\nline"])
        self.assertIn("copied post 2 of 2 from 02-card.md\n", out)
        self.assertIn("next: none\n", out)

    def test_copy_past_the_end_exits(self) -> None:
        draft = self._approved_draft()
        copied: list[bytes] = []
        code, out, err = self._run(
            self.post.main,
            [str(draft), "--copy", "3"],
            copy_text=copied.append,
            reveal=lambda _path: None,
        )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(copied, [])
        self.assertIn("no post 3", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_setup_day_open_writes_nothing(self) -> None:
        draft = self._approved_draft()
        (draft / "01-hook.md").write_text(
            "Most 4K TVs get set up on delivery day.\n",
            encoding="utf-8",
        )
        copied: list[bytes] = []
        self._approve(draft)
        code, out, err = self._run(
            self.post.main,
            [str(draft), "--copy", "1"],
            copy_text=copied.append,
            reveal=lambda _path: None,
        )
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(copied, [])
        self.assertIn("setup-day", err)
        self.assertNotIn("Most 4K TVs", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_verify_thoughts_and_mark_write_nothing(self) -> None:
        draft = self._approved_draft()
        (draft / "02-card.md").write_text(
            "VERIFY the histogram label.\nReply with your thoughts.\n💬\n",
            encoding="utf-8",
        )
        (draft / "PATHS.md").write_text("Confidence VERIFY\n", encoding="utf-8")
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("VERIFY in 02-card.md", err)
        self.assertIn("thoughts CTA in 02-card.md", err)
        self.assertIn("💬 in 02-card.md", err)
        self.assertNotIn("PATHS.md", err)
        self.assertNotIn("histogram", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_unverified_word_is_not_verify(self) -> None:
        draft = self._approved_draft()
        (draft / "02-card.md").write_text("An UNVERIFIED label stays in PATHS.\n", encoding="utf-8")
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("02-card.md", out)

    def test_duplicate_card_number_writes_nothing(self) -> None:
        draft = self._approved_draft()
        (draft / "02-card.md").write_text("3. Dual Neural Engine.\n", encoding="utf-8")
        (draft / "03-card.md").write_text("3. Improved battery life.\n", encoding="utf-8")
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("duplicate 3 on 02-card.md and 03-card.md", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_sources_media_writes_nothing(self) -> None:
        draft = self._approved_draft()
        (draft / "02-card.md").write_text(
            "Plate `images/sources/apple-18-battery.jpg`\n",
            encoding="utf-8",
        )
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft), "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("sources media in 02-card.md: images/sources/apple-18-battery.jpg", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_attach_none_skips_hook_fallback(self) -> None:
        draft = self._approved_draft()
        (draft / "images.md").write_text(
            "Generated concept.\n\nAttach: none\n",
            encoding="utf-8",
        )
        code, out, err = self._run(self.post.main, [str(draft), "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(payload["tweets"][0]["media"], [])
        sheet = (draft / "POST.txt").read_text(encoding="utf-8")
        self.assertNotIn("hook-before-after.jpg", sheet)
        self.assertNotIn("Attach: none", sheet)


class FormatAndApproval(unittest.TestCase):
    setUp = ScriptBehavior.setUp
    tearDown = ScriptBehavior.tearDown
    _run = ScriptBehavior._run
    _approve = ScriptBehavior._approve

    def _single(self, fmt: str | None, text: str) -> Path:
        draft = self.root / f"single-{fmt}"
        draft.mkdir()
        (draft / "01-hook.md").write_text(text, encoding="utf-8")
        if fmt is not None:
            (draft / "FORMAT").write_text(fmt + "\n", encoding="utf-8")
        self._approve(draft)
        return draft

    def test_most_refused_for_settings_only(self) -> None:
        for fmt, expected in (("settings", 1), (None, 1), ("single-tip", 0), ("comparison", 0),
                              ("build-log", 0), ("tool-verdict", 0)):
            draft = self._single(fmt, "Most free editors hold up.\n")
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, expected, (fmt, err))

    def test_root_over_600_refused_where_the_format_caps_it(self) -> None:
        long_root = "A result. " * 61  # 610 characters
        for fmt, expected in (("settings", 1), ("single-tip", 1), ("build-log", 1), ("tool-verdict", 1),
                              ("comparison", 0), ("tool-swap", 1)):
            text = long_root.strip() + "\n"
            if fmt == "tool-swap":
                text = SWAP_HEADER + "\n" + text
            draft = self._single(fmt, text)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, expected, (fmt, err))
            if expected:
                self.assertIn("caps the root at 600", err)

    def test_engagement_solicitation_refused_but_questions_and_tech_wording_pass(self) -> None:
        cases = (("Drop a hi and let's connect.", 1), ("What is your current project? Drop it below.", 1),
                 ("Reply with your router model.", 1), ("Save this before you book the repair.", 1),
                 ("Like and repost if this helped.", 1), ("Follow for more tips.", 1),
                 ("Which model is yours? The menu differs.", 0), ("Motion smoothing can drop a frame.", 0),
                 ("Tap Save this preset, then Done.", 0), ("The router replies with its firmware version.", 0))
        for i, (text, expected) in enumerate(cases):
            draft = self.root / f"solicit-{i}"
            draft.mkdir()
            (draft / "FORMAT").write_text("single-tip\n", encoding="utf-8")
            (draft / "01-hook.md").write_text(text + "\n", encoding="utf-8")
            self._approve(draft)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, expected, (text, err))

    def test_banned_phrases_refused_but_unlock_allowed(self) -> None:
        cases = (("This is a game changer.", 1), ("Most people don’t know this.", 1),
                 ("Big news 🔥", 1), ("Turn on Face ID unlock.", 0))
        for i, (text, expected) in enumerate(cases):
            draft = self.root / f"banned-{i}"
            draft.mkdir()
            (draft / "FORMAT").write_text("single-tip\n", encoding="utf-8")
            (draft / "01-hook.md").write_text(text + "\n", encoding="utf-8")
            self._approve(draft)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, expected, (text, err))

    def test_root_cap_counts_as_x_does(self) -> None:
        # 300 arrows are 300 characters to Python and 600 to X; one more is over the cap.
        self.assertEqual(self.post.x_length("→" * 300), 600)
        self.assertEqual(self.post.x_length("a–b’c"), 5)  # en dash and curly quote count 1
        self.assertEqual(self.post.x_length("…"), 2)  # the ellipsis is outside X's one-weight ranges
        self.assertEqual(self.post.x_length("see https://example.com/a/very/long/path/indeed ok"), 4 + 23 + 3)
        self.assertEqual(self.post.x_length("🔥"), 2)
        self.assertEqual(self._run(self.post.main, [str(self._single("single-tip", "→" * 300 + "\n"))])[0], 0)
        code, _out, err = self._run(self.post.main, [str(self._single("build-log", "→" * 301 + "\n"))])
        self.assertEqual(code, 1)
        self.assertIn("602 characters as X counts them", err)

    def test_post_one_cut_point_matches_x(self) -> None:
        # X's API cut post 1's text here: 270 characters to Python, 277 to X; " Ultra" would make 283.
        self.assertEqual(self.post.x_length(POST_ONE[:270]), 277)
        self.assertTrue(POST_ONE[:270].endswith("Streamlabs"))
        self.assertEqual(self.post.x_length(POST_ONE), 422)

    def test_tool_swap_root_needs_the_series_header(self) -> None:
        cases = ((POST_ONE, 0),
                 (POST_ONE.replace("creator", "local AI"), 0),
                 (POST_ONE.replace("creator", "video"), 1),
                 (POST_ONE.replace("PAID → FREE", "Stop paying for subscriptions."), 1),
                 ("Stop paying for these. Here are 10 FREE alternatives.\n", 1))
        for i, (text, expected) in enumerate(cases):
            draft = self.root / f"swap-header-{i}"
            draft.mkdir()
            (draft / "FORMAT").write_text("tool-swap\n", encoding="utf-8")
            (draft / "01-hook.md").write_text(text + "\n", encoding="utf-8")
            self._approve(draft)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, expected, (text[:40], err))
            if expected:
                self.assertIn("opens with the series header", err)

    def test_tool_swap_root_refuses_handles_hashtags_and_counters(self) -> None:
        cases = (("Photoshop → Photopea @photopeacom", "@photopeacom"), ("Free tools #free", "hashtag #free"),
                 ("🧵 1/5", "thread counter"), ("Runs 24/7 on a Pi", None), ("C# and F# both work", None),
                 ("Mail a@b.com for help", None))
        for i, (line, refusal) in enumerate(cases):
            draft = self.root / f"swap-root-{i}"
            draft.mkdir()
            (draft / "FORMAT").write_text("tool-swap\n", encoding="utf-8")
            (draft / "01-hook.md").write_text(SWAP_HEADER + "\n\n" + line + "\n", encoding="utf-8")
            (draft / "02-shoutout.md").write_text("@photopeacom thanks for answering people.\n", encoding="utf-8")
            self._approve(draft)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, 1 if refusal else 0, (line, err))
            if refusal:
                self.assertIn(refusal, err)

    def test_brochure_and_flyer_phrases_refused_in_every_format(self) -> None:
        for i, text in enumerate(("An open-source juggernaut.", "A neural graph of notes.",
                                  "Zero server dependency.", "Hollywood-grade colour.", "A drop-in replacement.",
                                  "Hey, let's grow together.")):
            draft = self.root / f"brochure-{i}"
            draft.mkdir()
            (draft / "FORMAT").write_text(("comparison", "settings", "single-tip")[i % 3] + "\n", encoding="utf-8")
            (draft / "01-hook.md").write_text(text + "\n", encoding="utf-8")
            self._approve(draft)
            code, _out, err = self._run(self.post.main, [str(draft)])
            self.assertEqual(code, 1, text)
            self.assertIn("banned phrase", err)

    def test_tool_swap_run_sheet_and_copy_say_to_wait_for_the_shoutout(self) -> None:
        draft = self.root / "swap"
        draft.mkdir()
        (draft / "FORMAT").write_text("tool-swap\n", encoding="utf-8")
        (draft / "01-hook.md").write_text(POST_ONE + "\n", encoding="utf-8")
        (draft / "02-shoutout.md").write_text("@photopeacom still ships features and answers people.\n",
                                              encoding="utf-8")
        self._approve(draft)
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 0, err)
        self.assertIn("Wait 10–20 minutes after card 1", out)
        self.assertIn("1  422  01-hook.md", out)
        copied: list[bytes] = []
        code, out, _err = self._run(self.post.main, [str(draft), "--copy", "1"],
                                    copy_text=copied.append, reveal=lambda _p: None)
        self.assertEqual(code, 0)
        self.assertIn("wait: Wait 10–20 minutes", out)
        single = self._single("single-tip", "One tip.\n")
        self.assertNotIn("Wait 10–20", self._run(self.post.main, [str(single)])[1])

    def test_count_needs_no_approval_and_writes_nothing(self) -> None:
        draft = self.root / "counted"
        draft.mkdir()
        (draft / "FORMAT").write_text("tool-swap\n", encoding="utf-8")
        (draft / "01-hook.md").write_text(SWAP_HEADER + "\n" + "→" * 300 + "\n", encoding="utf-8")
        before = sorted(p.name for p in draft.iterdir())
        code, out, err = self._run(self.post.main, [str(draft), "--count"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("  01-hook.md", out)
        self.assertIn("over the tool-swap root cap of 600", out)
        self.assertEqual(sorted(p.name for p in draft.iterdir()), before)

    def test_unknown_format_refused(self) -> None:
        draft = self._single("meme", "A result.\n")
        code, _out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertIn("unknown FORMAT", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_single_card_draft_passes(self) -> None:
        draft = self._single("single-tip", "One tip, whole payoff.\n")
        code, out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 0, err)
        self.assertIn("01-hook.md", out)

    def test_card_edit_after_digest_approval_refused(self) -> None:
        draft = self._single("single-tip", "Approved text.\n")
        (draft / "01-hook.md").write_text("Changed after approval.\n", encoding="utf-8")
        code, _out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertIn("changed after approval", err)
        self.assertFalse((draft / "POST.txt").exists())

    def test_legacy_empty_approval_uses_file_times(self) -> None:
        import os
        draft = self.root / "legacy"
        draft.mkdir()
        (draft / "01-hook.md").write_text("A result.\n", encoding="utf-8")
        (draft / "APPROVED").write_text("", encoding="utf-8")
        os.utime(draft / "01-hook.md", (1_000_000, 1_000_000))
        os.utime(draft / "APPROVED", (2_000_000, 2_000_000))
        self.assertEqual(self._run(self.post.main, [str(draft)])[0], 0)
        os.utime(draft / "01-hook.md", (3_000_000, 3_000_000))
        code, _out, err = self._run(self.post.main, [str(draft)])
        self.assertEqual(code, 1)
        self.assertIn("edited after approval: 01-hook.md", err)


if __name__ == "__main__":
    unittest.main()
