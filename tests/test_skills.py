#!/usr/bin/env python3
"""Static checks for .claude/skills: frontmatter, names, size, script references."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / ".claude" / "skills"
MAX_LINES = 500
SCRIPT_REF = re.compile(r"scripts/[A-Za-z0-9_/]+\.py")
LIMIT_REF = re.compile(r"(?:under|over|at most)[ -](\d{3})[ -]characters?|never over (\d{3})", re.I)


def skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


def frontmatter(text: str) -> dict[str, str]:
    """Top-level keys of the leading --- block; values are the raw first line."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    keys: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        match = re.match(r"^([A-Za-z][A-Za-z0-9-]*):\s*(.*)$", line)
        if match:
            keys[match.group(1)] = match.group(2).strip()
    return {}  # never closed


class SkillChecks(unittest.TestCase):
    def test_skills_exist(self):
        self.assertTrue(skill_files(), "no skills found")

    def test_frontmatter_name_and_description(self):
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                fm = frontmatter(path.read_text(encoding="utf-8"))
                self.assertTrue(fm, "missing or unclosed frontmatter")
                self.assertEqual(fm.get("name"), path.parent.name)
                self.assertIn("description", fm)

    def test_skill_md_under_line_limit(self):
        for path in skill_files():
            with self.subTest(skill=path.parent.name):
                count = len(path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(count, MAX_LINES)

    def test_referenced_scripts_exist(self):
        for path in skill_files():
            for md in sorted(path.parent.glob("*.md")):
                refs = set(SCRIPT_REF.findall(md.read_text(encoding="utf-8")))
                for ref in sorted(refs):
                    with self.subTest(file=f"{path.parent.name}/{md.name}", ref=ref):
                        self.assertTrue((REPO / ref).is_file(), f"{ref} does not exist")

    def test_no_grok_mentions_in_skills(self):
        """D88 dropped Grok; no skill file may bring it back."""
        for md in sorted(SKILLS.glob("*/*.md")):
            with self.subTest(file=f"{md.parent.name}/{md.name}"):
                self.assertNotIn("grok", md.read_text(encoding="utf-8").lower())

    def test_next_uses_api_search_syntax(self):
        """x_read.py refuses website operators, so the skill's examples must not use them."""
        text = (SKILLS / "next" / "SKILL.md").read_text(encoding="utf-8")
        for operator in ("-filter:", "min_faves:", "min_retweets:", "within_time:"):
            self.assertNotIn(operator, text)

    def test_stated_character_limits_match_the_gate(self):
        """The gate's constants are the source; skills restate them, so a changed limit fails here."""
        sys.path.insert(0, str(REPO / "scripts"))
        import post_thread

        allowed = {post_thread.ROOT_LIMIT, post_thread.SHORT_LIMIT}
        files = 0
        for md in sorted(SKILLS.glob("*/*.md")):
            stated = {int(n) for pair in LIMIT_REF.findall(md.read_text(encoding="utf-8")) for n in pair if n}
            if stated:
                files += 1
            with self.subTest(file=f"{md.parent.name}/{md.name}"):
                self.assertLessEqual(stated, allowed)
        self.assertGreaterEqual(files, 6, "the limit pattern no longer finds the skills that state it")


if __name__ == "__main__":
    unittest.main()
