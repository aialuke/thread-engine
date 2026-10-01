#!/usr/bin/env python3
"""Write a post run sheet for an approved draft, and copy one card at a time.

The numbered cards are the posts. This script does not rewrite them.
--dry-run is the default and matches a plain run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import durable
import formats

CARD_RE = re.compile(r"^[0-9]{2}-.+\.md$")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
MEDIA_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4"}
HOOK_MEDIA = "images/hook-before-after.jpg"
LONG_POST = (
    "Long posts. X Premium can send these (up to 25,000 characters). "
    "A free account stops at 280."
)
LEAD_NUMBER_RE = re.compile(r"^(?:Setting\s+(\d+)\b|(\d+)\.\s)")
VERIFY_RE = re.compile(r"\bVERIFY\b")
FORMATS = set(formats.DRAFT_FORMATS)
ROOT_LIMIT = formats.ROOT_LIMIT
SHORT_LIMIT = formats.SHORT_LIMIT
# X's weighted length (twitter-text v3): these code points count 1, every other one 2 (so → ▷ and emoji
# count 2), and a link counts 23. X cut post 1 of PAID → FREE at 277 by this count, 270 by Python's.
X_ONE_WEIGHT = ((0, 4351), (8192, 8205), (8208, 8223), (8242, 8247))
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
X_URL_LENGTH = 23
DIGEST_RE = re.compile(r"^cards-sha256:\s*([0-9a-f]{64})\s*$", re.MULTILINE)
THOUGHTS_RE = re.compile(r"your thoughts", re.IGNORECASE)
# X's Original Content Rewards rules: "Do not solicit engagements: repeatedly instructing users to engage
# with posts, such as asking to like, reply, bookmark, follow, or repost." Instructions only; a real
# question ("Which model is yours?") is fine. Tuned so tech wording ("drop a frame", "save this preset") passes.
SOLICIT_RE = re.compile(
    r"\bdrop (?:a|an) (?:hi|hello|comment|reply|link|👋)"
    r"|\bdrop (?:it|them|yours|your \w+) (?:below|here|in the comments)"
    r"|\bfollow (?:me )?for (?:more|part)"
    r"|\blike (?:and|&|\+) (?:repost|retweet|share|follow|comment)"
    r"|\b(?:repost|retweet|bookmark) this\b"
    r"|\bsave this (?:post|thread|tweet|for later|before)"
    r"|\bcomment below\b|\breply with\b|\btag (?:a friend|someone|your)",
    re.IGNORECASE)
BANNED_RE = re.compile(r"game changer|most people don['’]?t know|wait for it|🚨|🔥|👇"
                       r"|juggernaut|neural graph|zero server dependenc(?:y|ies)|hollywood[- ]grade"
                       r"|drop-in replacement|let['’]?s grow together", re.IGNORECASE)


def x_length(text: str) -> int:
    """Characters as X counts them. Emoji sequences are approximate (counted per code point)."""
    links = URL_RE.findall(text)
    rest = URL_RE.sub("", text)
    weight = sum(1 if any(lo <= ord(ch) <= hi for lo, hi in X_ONE_WEIGHT) else 2 for ch in rest)
    return weight + X_URL_LENGTH * len(links)


def _add_hint(hints: list[str], seen: set[str], raw: str) -> None:
    path = raw.strip()
    if not path or path.startswith(("http://", "https://", "data:")):
        return
    if path in seen:
        return
    seen.add(path)
    hints.append(path)


def media_hints(draft: Path, card: Path, text: str) -> list[str]:
    hints: list[str] = []
    seen: set[str] = set()
    for match in IMAGE_RE.finditer(text):
        _add_hint(hints, seen, match.group(1))
    for match in CODE_RE.finditer(text):
        token = match.group(1).strip()
        if Path(token).suffix.lower() in MEDIA_EXTS:
            _add_hint(hints, seen, token)
    if (
        card.name == "01-hook.md"
        and not hints
        and attach_hook_fallback(draft)
        and (draft / HOOK_MEDIA).is_file()
    ):
        hints.append(HOOK_MEDIA)
    return hints


def attach_hook_fallback(draft: Path) -> bool:
    notes = draft / "images.md"
    if not notes.is_file():
        return True
    for line in notes.read_text(encoding="utf-8").splitlines():
        if line.strip() == "Attach: none":
            return False
    return True


def sources_media(hint: str) -> bool:
    posix = Path(hint.strip()).as_posix()
    if posix.startswith("./"):
        posix = posix[2:]
    return posix.startswith("images/sources/") or "/images/sources/" in f"/{posix}"


def draft_format(draft: Path) -> str:
    marker = draft / "FORMAT"
    if not marker.is_file():
        return "settings"
    return marker.read_text(encoding="utf-8").strip()


def cards_digest(found: list[Path]) -> str:
    digest = hashlib.sha256()
    for card in found:
        digest.update(card.name.encode("utf-8") + b"\0")
        digest.update(card.read_bytes() + b"\0")
    return digest.hexdigest()


def approval_refusal(draft: Path, found: list[Path]) -> str | None:
    approved = draft / "APPROVED"
    match = DIGEST_RE.search(approved.read_text(encoding="utf-8"))
    if match:
        if match.group(1) != cards_digest(found):
            return "REFUSED: cards changed after approval. Type /approve again after re-reading them"
        return None
    approved_at = approved.stat().st_mtime
    newer = [card.name for card in found if card.stat().st_mtime > approved_at]
    if newer:
        return "REFUSED: edited after approval: " + ", ".join(newer) + ". Type /approve again after re-reading them"
    return None


def card_refusals(draft: Path, found: list[Path]) -> list[str]:
    reasons: list[str] = []
    numbers: dict[str, str] = {}
    fmt = draft_format(draft)
    spec = formats.DRAFT_FORMATS.get(fmt)
    if spec is None:
        reasons.append(f"REFUSED: unknown FORMAT {fmt!r}; expected one of {', '.join(sorted(FORMATS))}")
    else:
        count = formats.card_count_reason(fmt, spec, len(found))
        if count:
            reasons.append(count)
    for card in found:
        text = tweet_text(card)
        if spec is not None and card.name == "01-hook.md":
            reasons.extend(formats.root_reasons(fmt, spec, text, x_length(text)))
        if VERIFY_RE.search(text):
            reasons.append(f"REFUSED: VERIFY in {card.name}")
        if "💬" in text:
            reasons.append(f"REFUSED: 💬 in {card.name}")
        if THOUGHTS_RE.search(text):
            reasons.append(f"REFUSED: thoughts CTA in {card.name}")
        solicit = SOLICIT_RE.search(text)
        if solicit:
            reasons.append(f"REFUSED: asks for engagement ({solicit.group(0)!r}) in {card.name}; "
                           "ask a real question instead (X's rewards rules ban engagement solicitation)")
        banned = BANNED_RE.search(text)
        if banned:
            reasons.append(f"REFUSED: banned phrase {banned.group(0)!r} in {card.name}")
        match = LEAD_NUMBER_RE.match(first_line(text))
        if match:
            number = match.group(1) or match.group(2)
            prior = numbers.get(number)
            if prior:
                reasons.append(f"REFUSED: duplicate {number} on {prior} and {card.name}")
            else:
                numbers[number] = card.name
        for hint in media_hints(draft, card, text):
            if sources_media(hint):
                reasons.append(f"REFUSED: sources media in {card.name}: {hint}")
    return reasons


def tweet_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.endswith("\n"):
        text = text[:-1]
    return text


def first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def cards(draft: Path) -> list[Path]:
    found = [path for path in draft.iterdir() if path.is_file() and CARD_RE.fullmatch(path.name)]
    return sorted(found, key=lambda path: path.name)


def payload(draft: Path, found: list[Path]) -> dict:
    tweets = []
    for card in found:
        text = tweet_text(card)
        tweets.append({"text": text, "media": media_hints(draft, card, text)})
    return {"dry_run": True, "tweets": tweets}


def media_files(draft: Path, hints: list[str]) -> list[Path]:
    found: list[Path] = []
    for hint in hints:
        path = Path(hint)
        candidate = path if path.is_absolute() else draft / path
        if candidate.is_file():
            found.append(candidate)
    return found


def run_sheet(draft: Path, found: list[Path]) -> str:
    lines = [
        "Run sheet. Do not paste this file. Re-run post_thread.py after a card edit.",
        f"Copy with: python3 scripts/post_thread.py {draft} --copy 1",
    ]
    rows: list[str] = []
    over_short_limit = False
    for index, card in enumerate(found, start=1):
        text = tweet_text(card)
        if x_length(text) > SHORT_LIMIT:
            over_short_limit = True
        row = f"{index}  {x_length(text)}  {card.name}"
        hints = media_hints(draft, card, text)
        if hints:
            row += "  attach " + ", ".join(hints)
        rows.append(row)
    if over_short_limit:
        lines.append(LONG_POST)
    spec = formats.DRAFT_FORMATS.get(draft_format(draft))
    note = formats.after_root_note(spec, len(found)) if spec else None
    if note:
        lines.append(note)
    lines.append("")
    lines.extend(rows)
    return "\n".join(lines) + "\n"


def count_sheet(draft: Path, found: list[Path]) -> str:
    name = draft_format(draft)
    spec = formats.DRAFT_FORMATS.get(name)
    rows = ["Characters as X counts them (→, ▷ and emoji count 2; a link counts 23)."]
    for card in found:
        length = x_length(tweet_text(card))
        notes = []
        if length > SHORT_LIMIT:
            notes.append("over 280: a free account can't post it, and the feed shows the start then 'Show more'")
        if spec is not None and spec.root_limit is not None and card.name == "01-hook.md" and length > spec.root_limit:
            notes.append(f"over the {name} root cap of {spec.root_limit}")
        rows.append(f"{length}  {card.name}" + (f"  ({'; '.join(notes)})" if notes else ""))
    return "\n".join(rows) + "\n"


def copy_utf8(data: bytes) -> None:
    subprocess.run(["pbcopy"], input=data, check=True)


def reveal_in_finder(path: Path) -> None:
    subprocess.run(["open", "-R", str(path)], check=True)


def copy_message(draft: Path, found: list[Path], number: int) -> str:
    card = found[number - 1]
    text = tweet_text(card)
    hints = media_hints(draft, card, text)
    line = f"copied post {number} of {len(found)} from {card.name}"
    if hints:
        line += ". attach " + ", ".join(hints)
    rows = [line]
    if number == 1:
        opening = first_line(text)
        if opening:
            rows.append("open: " + opening)
    spec = formats.DRAFT_FORMATS.get(draft_format(draft))
    note = formats.after_root_note(spec, len(found)) if spec and number == 1 else None
    if note:
        rows.append("wait: " + note)
    if number < len(found):
        rows.append(f"next: python3 scripts/post_thread.py {draft} --copy {number + 1}")
    else:
        rows.append("next: none")
    return "\n".join(rows) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write POST.txt for an approved draft."
    )
    parser.add_argument("draft", type=Path, help="Path to a draft folder")
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Write the run sheet and do not post (default).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the JSON payload to stdout. Still writes POST.txt.",
    )
    parser.add_argument(
        "--count",
        action="store_true",
        help="Print each card's length as X counts it. Needs no approval and writes nothing.",
    )
    parser.add_argument(
        "--copy",
        type=int,
        default=None,
        metavar="N",
        help="Copy post N to the clipboard. Reads the card, not POST.txt.",
    )
    return parser


def request_refusal(args: argparse.Namespace, draft: Path, found: list) -> int | None:
    if args.copy is not None and not 1 <= args.copy <= len(found):
        print(f"REFUSED: no post {args.copy}", file=sys.stderr)
        return 1
    refused = card_refusals(draft, found)
    stale = approval_refusal(draft, found)
    if stale:
        refused.insert(0, stale)
    if refused:
        print("\n".join(refused), file=sys.stderr)
        return 1
    if not args.dry_run:
        print("v1 does not call the X API", file=sys.stderr)
        return 1
    return None


def main(
    argv: list[str] | None = None,
    *,
    copy_text: Callable[[bytes], None] = copy_utf8,
    reveal: Callable[[Path], None] = reveal_in_finder,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    draft = args.draft
    if not draft.is_dir():
        print(f"REFUSED: not a draft folder {draft}", file=sys.stderr)
        return 1

    if args.count:
        counted = cards(draft)
        if not counted:
            print(f"REFUSED: no numbered cards in {draft}", file=sys.stderr)
            return 1
        sys.stdout.write(count_sheet(draft, counted))
        return 0

    if not (draft / "APPROVED").is_file():
        print("human gate")
        return 2

    found = cards(draft)
    if not found:
        print(f"REFUSED: no numbered cards in {draft}", file=sys.stderr)
        return 1

    refusal = request_refusal(args, draft, found)
    if refusal is not None:
        return refusal

    sheet = run_sheet(draft, found)
    durable.atomic_write(draft / "POST.txt", sheet)

    if args.copy is not None:
        card = found[args.copy - 1]
        text = tweet_text(card)
        hints = media_hints(draft, card, text)
        copy_text(text.encode("utf-8"))
        sys.stdout.write(copy_message(draft, found, args.copy))
        for path in media_files(draft, hints):
            reveal(path)
        return 0

    if args.json:
        sys.stdout.write(json.dumps(payload(draft, found), ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
        return 0

    sys.stdout.write(sheet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
