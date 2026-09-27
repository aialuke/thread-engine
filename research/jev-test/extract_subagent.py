#!/usr/bin/env python3
"""Collect a Claude rater's JSON lines from subagent transcripts (Claude subagents can't write files in plan mode).

    python3 research/jev-test/extract_subagent.py --corpus C --out FILE TRANSCRIPT.jsonl...
    python3 research/jev-test/extract_subagent.py --corpus C --out FILE --session ID_OR_DIR --match "TEXT"

A subagent hands its answers back in its final reply: the `message` of its last SubagentHandback call, or
else the text of its last assistant turn. With --session, the transcripts are the subagents whose
description (agent-*.meta.json) contains --match. The lines are parsed as raters.py ingest parses them.

Fails closed: an unreadable line, an id not in the corpus, an id answered twice, or a corpus id missing,
and nothing is written. An existing --out is never overwritten. The file then goes to raters.py ingest,
which checks every answer. Output belongs in private/ (other people's posts; delete by 26 Mar 2027).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import raters  # noqa: E402  (the same line parser ingest uses)

PROJECTS = Path.home() / ".claude" / "projects" / "-Users-lukemckenzie-src-thread-engine"
HANDBACK = "SubagentHandback"


def final_reply(transcript: Path) -> str:
    """The subagent's final reply: its last SubagentHandback message, else its last assistant text."""
    handback, text = None, None
    for line in transcript.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("type") != "assistant":
            continue
        content = (row.get("message") or {}).get("content") or []
        for part in content if isinstance(content, list) else []:
            if part.get("type") == "tool_use" and part.get("name") == HANDBACK:
                handback = str((part.get("input") or {}).get("message") or "")
        texts = [p.get("text", "") for p in content if isinstance(content, list) and p.get("type") == "text"]
        if texts:
            text = "\n".join(texts)
    return handback if handback is not None else (text or "")


def session_transcripts(session: str, match: str, projects: Path = PROJECTS) -> list[Path]:
    folder = Path(session).expanduser()
    if not folder.is_dir():
        folder = projects / session
    folder = folder if folder.name == "subagents" else folder / "subagents"
    if not folder.is_dir():
        raise SystemExit(f"stopped: no subagents folder at {folder}")
    picked = []
    for meta in sorted(folder.glob("agent-*.meta.json")):
        if match in str(json.loads(meta.read_text(encoding="utf-8")).get("description") or ""):
            picked.append(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    if not picked:
        raise SystemExit(f"stopped: no subagent in {folder} has {match!r} in its description")
    return picked


def extract(transcripts: list[Path], corpus: dict, out: Path) -> dict:
    if out.exists():
        raise SystemExit(f"stopped: {out} already exists; nothing written")
    parsed, problems = [], []
    for path in transcripts:
        got, bad = raters.parse_lines(final_reply(path))
        parsed += got
        problems += [f"{path.name} {b}" for b in bad]
        if not got:
            problems.append(f"{path.name}: no answer lines in its final reply")
    counts = Counter(r["id"] for r in parsed)
    problems += [f"{i}: not in the corpus" for i in counts if i not in corpus]
    problems += [f"{i}: answered {n} times" for i, n in counts.items() if n > 1]
    problems += [f"{i}: missing" for i in corpus if i not in counts]
    if problems:
        raise SystemExit(f"stopped: nothing written, {len(problems)} problem(s):\n" + "\n".join(problems[:50]))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in parsed), encoding="utf-8")
    tmp.replace(out)
    return {"transcripts": len(transcripts), "lines": len(parsed), "of": len(corpus), "file": str(out)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect a Claude rater's JSON lines from subagent transcripts.")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--session", help="a session id under the project's transcripts, or its folder")
    parser.add_argument("--match", help="with --session: text in the subagents' descriptions")
    parser.add_argument("transcripts", nargs="*")
    args = parser.parse_args(argv)
    if bool(args.session) != bool(args.match):
        parser.error("--session and --match go together")
    if bool(args.session) == bool(args.transcripts):
        parser.error("give transcripts, or --session with --match, not both")
    paths = session_transcripts(args.session, args.match) if args.session else [Path(t) for t in args.transcripts]
    print(json.dumps(extract(paths, raters.load_corpus(Path(args.corpus)), Path(args.out)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
