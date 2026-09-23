#!/usr/bin/env python3
"""UserPromptSubmit hook: the operator types `/approve <slug>` and this writes APPROVED.

Only text a person types reaches this hook as a blockable prompt, so the model
cannot approve its own draft. The prompt is blocked after approval, so the model
never sees it. APPROVED records a digest of the cards; any later card edit makes
the gate refuse until the operator approves again.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

APPROVE_RE = re.compile(r"^/approve\s+([A-Za-z0-9-]+)\s*$")


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def find_draft(root: Path, slug: str) -> list[Path]:
    drafts = root / "drafts"
    exact = drafts / slug
    if exact.is_dir():
        return [exact]
    return sorted(p for p in drafts.glob(f"*-{slug}") if p.is_dir() and not p.name.startswith("_"))


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    match = APPROVE_RE.match(str(event.get("prompt", "")).strip())
    if not match:
        sys.exit(0)
    root = Path(event.get("workspaceRoot") or event.get("cwd") or ".").resolve()
    sys.path.insert(0, str(root / "scripts"))
    import post_thread  # noqa: E402

    slug = match.group(1)
    found = find_draft(root, slug)
    if not found:
        block(f"No draft folder matches '{slug}'. Nothing was approved.")
    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        block(f"'{slug}' matches more than one draft ({names}). Type /approve with the full folder name.")
    draft = found[0]
    cards = post_thread.cards(draft)
    if not cards:
        block(f"{draft.name} has no numbered cards. Nothing was approved.")
    digest = post_thread.cards_digest(cards)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (draft / "APPROVED").write_text(
        f"cards-sha256: {digest}\napproved-at: {stamp}\napproved-by: operator, typed /approve\n",
        encoding="utf-8",
    )
    block(
        f"Approved {draft.name}: {len(cards)} card(s) as they are now. "
        f"If any card changes, approve again. Next: /ready {slug}"
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail closed and visibly: tell the operator, approve nothing
        import traceback
        detail = " | ".join(traceback.format_exception_only(type(exc), exc)).strip()
        block(f"Approval failed, nothing was approved: {detail}")
