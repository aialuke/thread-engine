#!/usr/bin/env python3
"""Print the grok command that drafts a thread.

Run /plan in that grok session first. This script does not start grok
and does not pass any flag that skips Plan mode.

    grok -p "/draft-thread {slug}"
"""

from __future__ import annotations

import argparse
import re
import sys

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the grok /draft-thread command. Does not run grok."
    )
    parser.add_argument("slug")
    args = parser.parse_args(argv)

    if not SLUG_RE.fullmatch(args.slug):
        print(f"REFUSED: invalid slug {args.slug!r}", file=sys.stderr)
        return 1

    print(f'grok -p "/draft-thread {args.slug}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
