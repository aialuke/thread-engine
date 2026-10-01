"""The shape of each Format: the draft names, the ledger name `other`, the root cap, the root checks, and how many cards.

The gate (scripts/post_thread.py) and the ledger (loop_core/payloads.py) both read this. Skills quote the numbers; they are not a second source.
"""

from __future__ import annotations

import re
from typing import NamedTuple

ROOT_LIMIT = 600
SHORT_LIMIT = 280

SWAP_LABEL = "PAID → FREE"
SWAP_WORDS = ("creator", "productivity", "developer", "privacy", "system", "storage", "diagram", "finance",
              "local AI", "self-hosting", "support")
SWAP_STEM_RE = re.compile(r"Finding free (?:" + "|".join(re.escape(w) for w in SWAP_WORDS)
                          + r") tools that actually hold up\.")
HANDLE_RE = re.compile(r"(?<![\w@])@\w{1,15}")
HASHTAG_RE = re.compile(r"(?<![\w&#])#[^\W\d]\w*")
PART_RE = re.compile(r"^\s*(\d{1,2})/(\d{1,2})\b|\b(\d{1,2})/(\d{1,2})\s*$", re.MULTILINE)
SHOUTOUT_WAIT = "Wait 10–20 minutes after card 1, then post card 2 as a reply (the shout-out)."


class DraftFormat(NamedTuple):
    """One draft Format. root_limit None means the root is not capped. max_cards None means the thread length is free.

    root_checks names the extra root refusals. after_root is said when the draft has a card after the root.
    """

    root_limit: int | None
    max_cards: int | None
    root_checks: tuple[str, ...]
    after_root: str | None


DRAFT_FORMATS = {
    "settings": DraftFormat(ROOT_LIMIT, None, ("setup-day",), None),
    "comparison": DraftFormat(None, None, (), None),
    "tool-swap": DraftFormat(ROOT_LIMIT, 2, ("swap",), SHOUTOUT_WAIT),
    "single-tip": DraftFormat(ROOT_LIMIT, 1, (), None),
    "build-log": DraftFormat(ROOT_LIMIT, 2, (), None),
    "tool-verdict": DraftFormat(ROOT_LIMIT, 2, (), None),
}
LEDGER_FORMATS = frozenset(DRAFT_FORMATS) | {"other"}


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _thread_part(text: str) -> str | None:
    """A thread counter like 1/5 at the start or end of a line; 24/7 is not one."""
    for match in PART_RE.finditer(text):
        first, total = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
        if 1 <= int(first) <= int(total) and int(total) > 1:
            return match.group(0).strip()
    return None


def _setup_day(text: str) -> list[str]:
    if _first_line(text).startswith("Most "):
        return ["REFUSED: hook opens on the setup-day line"]
    return []


def _swap_root(text: str) -> list[str]:
    reasons: list[str] = []
    lines = text.splitlines()
    header_ok = (len(lines) >= 2 and lines[0].strip() == SWAP_LABEL and bool(SWAP_STEM_RE.fullmatch(lines[1].strip())))
    if not header_ok:
        reasons.append(f"REFUSED: a tool-swap root opens with the series header: '{SWAP_LABEL}', then "
                       f"'Finding free <word> tools that actually hold up.' with <word> one of: {', '.join(SWAP_WORDS)}")
    handle = HANDLE_RE.search(text)
    if handle:
        reasons.append(f"REFUSED: {handle.group(0)} in the tool-swap root; handles go in the shout-out card only")
    tag = HASHTAG_RE.search(text)
    if tag:
        reasons.append(f"REFUSED: hashtag {tag.group(0)} in the tool-swap root")
    part = _thread_part(text)
    if part:
        reasons.append(f"REFUSED: thread counter {part!r} in the tool-swap root")
    return reasons


ROOT_CHECKS = {
    "setup-day": _setup_day,
    "swap": _swap_root,
}


def root_reasons(name: str, spec: DraftFormat, text: str, length: int) -> list[str]:
    """Refusals for this format's root: the cap, then each named root check."""
    reasons: list[str] = []
    if spec.root_limit is not None and length > spec.root_limit:
        reasons.append(f"REFUSED: 01-hook.md is {length} characters as X counts them; "
                       f"the {name} format caps the root at {spec.root_limit}")
    for check in spec.root_checks:
        reasons.extend(ROOT_CHECKS[check](text))
    return reasons


def card_count_reason(name: str, spec: DraftFormat, count: int) -> str | None:
    """A draft with more cards than the format allows. None when the count is inside the bound."""
    if spec.max_cards is not None and count > spec.max_cards:
        noun = "card" if spec.max_cards == 1 else "cards"
        return f"REFUSED: {name} allows at most {spec.max_cards} {noun}; this draft has {count}"
    return None


def after_root_note(spec: DraftFormat, count: int) -> str | None:
    """The note after card 1, when this format has one and the draft has a later card."""
    if spec.after_root and count > 1:
        return spec.after_root
    return None
