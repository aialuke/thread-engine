#!/usr/bin/env python3
"""One read-only, structured Grok call. The only way this repo reads X.

Grok runs with a read-only sandbox and no shell, edit or write tools, and must
answer in the given JSON schema. Used by snapshot.py and x_read.py, so skills
work the same from Grok or Claude Code.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROK = Path.home() / ".grok" / "bin" / "grok"


def last_json_object(text: str) -> dict:
    """Grok's structured output can hold partial objects before the final one."""
    decoder = json.JSONDecoder()
    found, i = [], 0
    while (start := text.find("{", i)) >= 0:
        try:
            obj, i = decoder.raw_decode(text, start)
            found.append(obj)
        except json.JSONDecodeError:
            i = start + 1
    if not found:
        raise ValueError("no JSON object in Grok output")
    return found[-1]


def run_structured(prompt: str, schema: dict, *, timeout: int = 900,
                   runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> tuple[dict, float | None]:
    """Return (schema-shaped data, cost in USD or None)."""
    result = runner(
        [str(GROK), "-p", prompt, "--json-schema", json.dumps(schema), "--output-format", "json",
         "--sandbox", "read-only", "--deny", "Bash", "--deny", "Edit", "--deny", "Write", "--effort", "low"],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"grok exited {result.returncode}: {result.stderr.strip()[-300:]}")
    envelope = last_json_object(result.stdout)
    return last_json_object(envelope.get("text", "")), envelope.get("total_cost_usd")
