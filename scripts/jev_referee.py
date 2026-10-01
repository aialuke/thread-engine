#!/usr/bin/env python3
"""PreToolUse referee. Code allows, denies, or skips. Jev only votes.

Shadow mode logs the would-be decision and lets the tool run. Hard rules deny
even then. The TypeSafe key is read from the Keychain inside this process and
is never printed, logged, or written into a receipt or the request state.

    python3 scripts/jev_referee.py            # hook: JSON on stdin
    python3 scripts/jev_referee.py --dry-run  # three canned forks, real key
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import NamedTuple

import yaml

ROOT = Path(__file__).resolve().parent.parent
THRESHOLDS = ROOT / "jev" / "thresholds.yaml"
LOCAL_THRESHOLDS = ROOT / "jev" / "thresholds.local.yaml"
QUESTIONS = ROOT / "jev" / "questions.json"
RECEIPTS = ROOT / "receipts" / "decisions.jsonl"
PROMPTS = ROOT / "receipts" / "prompts"

PINNED_MODEL = "jev-1.13.0"
KEYCHAIN_SERVICE = "thread-engine-typesafe"
KEYCHAIN_ACCOUNT = "api_key"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"

SPAWN_TOOLS = {"spawn_subagent", "workflow", "Task", "Agent"}
EDIT_TOOLS = {"search_replace", "Write", "Edit", "StrReplace"}
SHELL_TOOLS = {"run_terminal_command", "Bash"}
SPAWN_CHOICE = "route"
COMMIT_NOULS = ("in_scope", "extra_deletion", "needs_human")
DELETE_CHOICE = "disposition"
DELETE_NOUL = "unused"
SHELLS = {"bash", "sh", "zsh", "dash"}
SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,200}$")
COMMENT_LINE = re.compile(r"^\s*(#|//|/\*|\*|<!--)")
SECRET_PATH = re.compile(
    r"(^|/)(\.env(\.|$)|.*\.pem$|.*credentials.*|.*\.p12$|id_rsa(\.|$)|.*keychain.*)$",
    re.IGNORECASE,
)
OPERATORS = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")


class PolicyError(Exception):
    """The local threshold file tried to loosen a rule."""


class CallFailed(Exception):
    """A Jev call did not return answers. The message is a reason code, never the key."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tool_name(event: dict) -> str:
    return str(event.get("toolName") or event.get("tool_name") or "")


def tool_input(event: dict) -> dict:
    value = event.get("toolInput")
    if value is None:
        value = event.get("tool_input")
    return value if isinstance(value, dict) else {}


def _raw_session(event: dict) -> str:
    return str(event.get("sessionId") or event.get("session_id") or "")


def _raw_prompt(event: dict) -> str:
    return str(event.get("promptId") or event.get("prompt_id") or "")


def _unsafe_id(raw: str) -> bool:
    """`..` or a separator would let the prompt path leave receipts/prompts/."""
    return ".." in raw or "/" in raw or "\\" in raw


def bad_id(event: dict) -> bool:
    return _unsafe_id(_raw_session(event)) or _unsafe_id(_raw_prompt(event))


def session_key(event: dict) -> str:
    raw = _raw_session(event)
    if not raw or _unsafe_id(raw) or not SAFE_ID.fullmatch(raw):
        return ""
    return raw


def prompt_key(event: dict) -> str:
    raw = _raw_prompt(event)
    if not raw or _unsafe_id(raw) or not SAFE_ID.fullmatch(raw):
        return ""
    return raw


def workspace_of(event: dict) -> str:
    return str(event.get("workspaceRoot") or event.get("cwd") or Path.cwd())


# ---------- policy ----------


def _get(tree: dict, path: tuple[str, ...]):
    cursor = tree
    for part in path:
        if not isinstance(cursor, dict) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


def _set(tree: dict, path: tuple[str, ...], value) -> None:
    cursor = tree
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value


# Direction that makes the referee stricter. "max" means a higher number asks
# more or allows less. "min" means a lower number does.
TIGHTER = {
    ("forks", "spawn", "confidence_floor"): "max",
    ("forks", "commit", "extra_deletion_ask"): "min",
    ("forks", "commit", "needs_human_ask"): "min",
    ("forks", "commit", "in_scope_floor"): "max",
    ("forks", "delete", "unused_min"): "max",
    ("forks", "delete", "choice_confidence_min"): "max",
    ("skip", "commit", "max_files"): "min",
    ("skip", "commit", "max_lines"): "min",
    ("delete_edit", "min_removed_feature_lines"): "min",
    ("delete_edit", "removed_over_added"): "min",
    ("timeout_seconds",): "min",
    ("git_timeout_seconds",): "min",
    ("tokens", "max_request"): "min",
    ("tokens", "max_state_plus_longest_question"): "min",
    ("tokens", "prefer_state"): "min",
    ("tokens", "diff_line_cap"): "min",
    ("tokens", "max_file_read_bytes"): "min",
}


def _loosen(direction: str, base: float, local: float) -> bool:
    return local < base if direction == "max" else local > base


def _tighten(merged: dict, local: dict) -> None:
    """Apply each TIGHTER number from the local file; a number that would loosen the policy is an error."""
    for path, direction in TIGHTER.items():
        value = _get(local, path)
        if value is None:
            continue
        current = _get(merged, path)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise PolicyError(f"{'.'.join(path)} must be a number")
        if _loosen(direction, float(current), float(value)):
            raise PolicyError(f"{'.'.join(path)} would loosen {current} to {value}")
        _set(merged, path, value)


def _drop_only(base: dict, local: dict, merged: dict, path: tuple[str, ...], noun: str) -> None:
    """A local list may only remove entries from the committed one."""
    value = _get(local, path)
    if value is None:
        return
    allowed = list(_get(base, path))
    if not isinstance(value, list) or any(item not in allowed for item in value):
        raise PolicyError(f"{path[-1]} can only drop {noun}")
    _set(merged, path, value)


def merge_policy(base: dict, local: dict | None) -> dict:
    """Apply a local file. Loosening, or a key this file does not know, is an error."""
    merged = json.loads(json.dumps(base))
    merged["model"] = PINNED_MODEL
    if not local:
        return merged
    unknown = set(local) - set(base) - {"mode"}
    if unknown:
        raise PolicyError(f"unknown local keys: {sorted(unknown)}")
    if "mode" in local:
        if local["mode"] not in {"shadow", "active"}:
            raise PolicyError("mode must be shadow or active")
        merged["mode"] = local["mode"]
    if "model" in local and local["model"] != PINNED_MODEL:
        merged["model"] = PINNED_MODEL
    _tighten(merged, local)
    _drop_only(base, local, merged, ("skip", "commit", "message_prefixes"), "a prefix")
    _drop_only(base, local, merged, ("skip", "delete_dirs"), "a directory")
    if "policy_version" in local:
        if not isinstance(local["policy_version"], int) or local["policy_version"] < base["policy_version"]:
            raise PolicyError("policy_version cannot go backwards")
        merged["policy_version"] = local["policy_version"]
    return merged


def load_policy(base_path: Path = THRESHOLDS, local_path: Path = LOCAL_THRESHOLDS) -> dict:
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    local = yaml.safe_load(local_path.read_text(encoding="utf-8")) if local_path.is_file() else None
    policy = merge_policy(base, local)
    policy["model"] = PINNED_MODEL
    return policy


def load_questions(path: Path = QUESTIONS) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_base_policy(base_path: Path = THRESHOLDS) -> dict:
    """Committed thresholds, with the model pin forced. Ignores a bad local file."""
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    return merge_policy(base, None)


# ---------- command parsing ----------


def command_pieces(command: str) -> list[list[str]]:
    """Top-level shell pieces, plus one level of `sh -c` so a quoted wipe is still seen."""
    found: list[list[str]] = []

    def take(text: str, nested: bool) -> None:
        for part in OPERATORS.split(text):
            part = part.strip()
            if not part:
                continue
            try:
                argv = shlex.split(part)
            except ValueError:
                continue
            if not argv:
                continue
            found.append(argv)
            if nested:
                continue
            name = PurePosixPath(argv[0]).name
            if name in SHELLS and "-c" in argv:
                index = argv.index("-c")
                if index + 1 < len(argv):
                    take(argv[index + 1], True)

    take(command, False)
    return found


def _rm_invocation(argv: list[str]) -> tuple[bool, list[str]] | None:
    if PurePosixPath(argv[0]).name != "rm":
        return None
    recursive = force = False
    args: list[str] = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            args.extend(argv[index + 1:])
            break
        if token == "--recursive":
            recursive = True
        elif token == "--force":
            force = True
        elif token.startswith("-") and not token.startswith("--"):
            letters = token[1:]
            recursive = recursive or ("r" in letters or "R" in letters)
            force = force or ("f" in letters)
        else:
            args.append(token)
        index += 1
    return (recursive and force, args)


def _is_git_path(path: str) -> bool:
    return ".git" in PurePosixPath(path).parts


def _lexical(path: str) -> str:
    """Collapse `.`, `..`, and extra slashes without reading the disk. `//` becomes `/`."""
    if path in {"~", "~/"}:
        return "~"
    home = path == "~" or path.startswith("~/")
    rest = path[1:] if home else path
    absolute = rest.startswith("/")
    parts: list[str] = []
    for part in rest.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            elif not absolute:
                parts.append("..")
            continue
        parts.append(part)
    if home:
        return "~" if not parts else "~/" + "/".join(parts)
    if absolute:
        return "/" + "/".join(parts) if parts else "/"
    return "/".join(parts) if parts else "."


def _same_dir(left: str, right: str) -> bool:
    return _lexical(left).rstrip("/") == _lexical(right).rstrip("/")


def _is_wipe(path: str, workspace: str, cwd: str) -> bool:
    normal = _lexical(path)
    if normal in {"/", "/*", "/.", "~", "~/", ".", "./"}:
        return True
    if workspace and _same_dir(normal, workspace):
        return True
    if normal in {"*", "./*"} and cwd and (_lexical(cwd) in {"/", "~"} or _same_dir(cwd, workspace)):
        return True
    return False


def _split_ops(text: str) -> list[tuple[str, str]]:
    """Split on shell operators outside quotes. The first piece has an empty operator."""
    pieces: list[tuple[str, str]] = []
    buf: list[str] = []
    quote = ""
    operator = ""
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            buf.append(char)
            if char == quote and text[index - 1] != "\\":
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            index += 1
            continue
        found = ""
        if text.startswith("&&", index):
            found = "&&"
        elif text.startswith("||", index):
            found = "||"
        elif char in {";", "|"}:
            found = char
        if found:
            pieces.append((operator, "".join(buf).strip()))
            buf = []
            operator = found
            index += len(found)
            continue
        buf.append(char)
        index += 1
    pieces.append((operator, "".join(buf).strip()))
    return [(op, segment) for op, segment in pieces if segment]


SUDO_TAKES = frozenset({"-u", "-g", "-U", "-h", "-p", "-C", "-D", "-r", "-t", "-T",
                        "--user", "--group", "--host", "--prompt", "--chdir"})
ENV_TAKES = frozenset({"-u", "--unset", "-C", "--chdir", "-S", "--split-string"})


def _after_options(argv: list[str], takes: frozenset[str] = frozenset(), skip_assignments: bool = False) -> list[str]:
    """argv past a wrapper's own options. `--` ends them, a flag in `takes` also eats its value."""
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            return argv[index + 1:]
        if token in takes:
            index += 2
        elif token.startswith("-") or (skip_assignments and "=" in token):
            index += 1
        else:
            return argv[index:]
    return []


def _drop_sudo(argv: list[str]) -> list[str]:
    return _after_options(argv, SUDO_TAKES)


def _drop_command(argv: list[str]) -> list[str]:
    return _after_options(argv)


def _drop_env(argv: list[str]) -> list[str]:
    return _after_options(argv, ENV_TAKES, skip_assignments=True)


def _strip_wrappers(argv: list[str]) -> list[str]:
    for _ in range(6):
        if not argv:
            return argv
        name = PurePosixPath(argv[0]).name
        if name == "sudo":
            argv = _drop_sudo(argv)
        elif name == "command":
            argv = _drop_command(argv)
        elif name == "env":
            argv = _drop_env(argv)
        else:
            return argv
    return argv


def _shell_script(argv: list[str]) -> str | None:
    if PurePosixPath(argv[0]).name not in SHELLS:
        return None
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            return None
        if token == "-c":
            return argv[index + 1] if index + 1 < len(argv) else None
        if token.startswith("-") and not token.startswith("--") and "c" in token[1:]:
            return argv[index + 1] if index + 1 < len(argv) else None
        if token.startswith("-"):
            index += 1
            continue
        return None
    return None


def _cd_target(argv: list[str]) -> str | None:
    if PurePosixPath(argv[0]).name != "cd":
        return None
    args: list[str] = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--":
            args.extend(argv[index + 1:])
            break
        if token.startswith("-"):
            index += 1
            continue
        args.append(token)
        index += 1
    return args[0] if args else "~"


def _join_cwd(cwd: str, target: str) -> str:
    if target == "~" or target.startswith("~/") or target.startswith("/"):
        return _lexical(target)
    base = cwd or "."
    if base == "~":
        return _lexical("~/" + target)
    return _lexical(base.rstrip("/") + "/" + target)


def _argv_hard(argv: list[str], cwd: str, workspace: str) -> str | None:
    removed = _rm_invocation(argv)
    if removed is not None:
        wiping, args = removed
        if any(_is_git_path(arg) for arg in args):
            return "git_dir"
        if wiping and any(_is_wipe(arg, workspace, cwd) for arg in args):
            return "wipe"
    if _force_push(argv):
        return "force_push"
    return None


def _scan_shell(text: str, cwd: str, workspace: str, depth: int) -> str | None:
    if depth > 8 or not text:
        return None
    carry = cwd
    origin = cwd
    pending: str | None = None
    for operator, segment in _split_ops(text):
        if operator in {"||", "|"}:
            carry = origin
            pending = None
        elif pending is not None and operator in {"&&", ";"}:
            carry = pending
            pending = None
        try:
            argv = shlex.split(segment)
        except ValueError:
            continue
        argv = _strip_wrappers(argv)
        if not argv:
            continue
        script = _shell_script(argv)
        if script is not None:
            found = _scan_shell(script, carry, workspace, depth + 1)
        else:
            found = _argv_hard(argv, carry, workspace)
            target = _cd_target(argv)
            if target is not None:
                pending = _join_cwd(carry, target)
        if found:
            return found
    return None


def hard_rule(command: str, workspace: str) -> str | None:
    """A reason code, or None. This does not ask Jev."""
    start = _lexical(workspace) if workspace else ""
    return _scan_shell(command, start, start, 0)


def _git_rest(argv: list[str]) -> tuple[str, list[str]] | None:
    if PurePosixPath(argv[0]).name != "git":
        return None
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token, argv[index + 1:]
    return None


def _protected_destination(spec: str) -> bool:
    name = spec[1:] if spec.startswith("+") else spec
    if ":" in name:
        name = name.split(":", 1)[1]
    if name.startswith("refs/heads/"):
        name = name[len("refs/heads/"):]
    return name in {"main", "master"}


def _force_push(argv: list[str]) -> bool:
    parsed = _git_rest(argv)
    if parsed is None or parsed[0] != "push":
        return False
    rest = parsed[1]
    forced = False
    positionals: list[str] = []
    index = 0
    while index < len(rest):
        token = rest[index]
        if token == "--":
            positionals.extend(rest[index + 1:])
            break
        if token == "--force":
            forced = True
        elif token.startswith("-") and not token.startswith("--") and "f" in token[1:]:
            forced = True
        elif token.startswith("-"):
            if token in {"--repo", "--receive-pack", "--exec"}:
                index += 1
        else:
            positionals.append(token)
        index += 1
    refs = positionals[1:] if len(positionals) > 1 else positionals
    for spec in refs:
        plus = spec.startswith("+")
        if (forced or plus) and _protected_destination(spec):
            return True
    return False


def _commit_args(command: str) -> list[str] | None:
    for argv in command_pieces(command):
        parsed = _git_rest(argv)
        if parsed is not None and parsed[0] == "commit":
            return parsed[1]
    return None


def parse_commit(args: list[str]) -> tuple[str | None, bool]:
    """(message, include_unstaged). Message is None when the command has no -m."""
    parts: list[str] = []
    include = False
    index = 0
    while index < len(args):
        token = args[index]
        if token in {"-m", "--message"}:
            index += 1
            if index < len(args):
                parts.append(args[index])
        elif token.startswith("--message="):
            parts.append(token.split("=", 1)[1])
        elif token == "--all":
            include = True
        elif token.startswith("-") and not token.startswith("--"):
            letters = token[1:]
            cursor = 0
            while cursor < len(letters):
                letter = letters[cursor]
                if letter == "a":
                    include = True
                elif letter == "m":
                    rest = letters[cursor + 1:]
                    if rest:
                        parts.append(rest)
                    else:
                        index += 1
                        if index < len(args):
                            parts.append(args[index])
                    break
                cursor += 1
        index += 1
    return ("\n\n".join(parts) if parts else None), include


def _git_rm_paths(argv: list[str]) -> list[str] | None:
    parsed = _git_rest(argv)
    if parsed is None or parsed[0] != "rm":
        return None
    paths = []
    for token in parsed[1]:
        if token == "--":
            continue
        if token.startswith("-"):
            continue
        paths.append(token)
    return paths


def _rm_paths(command: str) -> list[str] | None:
    paths: list[str] = []
    saw = False
    for argv in command_pieces(command):
        removed = _rm_invocation(argv)
        if removed is not None:
            saw = True
            paths.extend(removed[1])
            continue
        git_paths = _git_rm_paths(argv)
        if git_paths is not None:
            saw = True
            paths.extend(git_paths)
    return paths if saw else None


def under_junk(path: str, dirs: list[str]) -> bool:
    """True only when the path still sits inside a junk directory after `..` is resolved."""
    resolved = _lexical(path)
    parts = PurePosixPath(resolved).parts
    if ".." in parts:
        return False
    return any(part in dirs for part in parts)


def feature_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        if not line.strip() or COMMENT_LINE.match(line):
            continue
        lines.append(line)
    return lines


def edit_is_deletion(old: str, new: str, policy: dict) -> bool:
    removed = len(feature_lines(old))
    added = len(feature_lines(new))
    rule = policy["delete_edit"]
    return removed >= rule["min_removed_feature_lines"] and removed > rule["removed_over_added"] * added


# ---------- classification ----------


def classify(event: dict, policy: dict) -> str | None:
    """spawn, commit, delete, or None. None means this tool is not a fork."""
    name = tool_name(event)
    incoming = tool_input(event)
    if name in SPAWN_TOOLS or name == "commit":
        return "spawn" if name in SPAWN_TOOLS else "commit"
    if name in SHELL_TOOLS:
        command = str(incoming.get("command", ""))
        if _commit_args(command) is not None:
            return "commit"
        if _rm_paths(command) is not None:
            return "delete"
        return None
    if name not in EDIT_TOOLS:
        return None
    if "old_string" in incoming or "old_str" in incoming:
        old = str(incoming.get("old_string", incoming.get("old_str", "")))
        new = str(incoming.get("new_string", incoming.get("new_str", "")))
        return "delete" if edit_is_deletion(old, new, policy) else None
    if "content" in incoming:
        path = str(incoming.get("file_path") or incoming.get("path") or "")
        previous = _read_existing(path, event, policy)
        if previous is None:
            return None
        return "delete" if edit_is_deletion(previous, str(incoming.get("content", "")), policy) else None
    return None


def _read_existing(path: str, event: dict, policy: dict) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(workspace_of(event)) / path
    try:
        if not candidate.is_file():
            return None
        if candidate.stat().st_size > policy["tokens"]["max_file_read_bytes"]:
            return None
        return candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


# ---------- state ----------


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


def _token_len(value, chars: int) -> int:
    return len(json.dumps(value, ensure_ascii=False)) // chars


def _secret_path(path: str) -> bool:
    return SECRET_PATH.search(path.replace("\\", "/")) is not None


def redact_diff(diff: str) -> str:
    """Replace hunks of secret files. The path stays; the body does not."""
    if not diff:
        return diff
    chunks = re.split(r"(?=^diff --git )", diff, flags=re.MULTILINE)
    kept = []
    for chunk in chunks:
        match = re.search(r"^diff --git a/(\S+)", chunk, re.MULTILINE)
        if match and _secret_path(match.group(1)):
            kept.append(f"diff --git a/{match.group(1)} b/{match.group(1)}\n[redacted]\n")
        else:
            kept.append(chunk)
    return "".join(kept)


def redact_key(value, key: str | None):
    if not key:
        return value
    if isinstance(value, str):
        return value.replace(key, "[redacted]")
    if isinstance(value, list):
        return [redact_key(item, key) for item in value]
    if isinstance(value, dict):
        return {k: redact_key(v, key) for k, v in value.items()}
    return value


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def state_hash(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def read_prompt(event: dict, prompts: Path) -> str | None:
    """The prompt saved for this session. None when the id is missing or unsafe."""
    if bad_id(event):
        return None
    session = session_key(event)
    if not session:
        return None
    folder = prompts / session
    prompt_id = prompt_key(event)
    path = folder / prompt_id if prompt_id else folder / "prompt.txt"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def save_prompt(event: dict, prompts: Path) -> None:
    if bad_id(event):
        return
    session = session_key(event)
    text = event.get("prompt")
    if not session or not isinstance(text, str):
        return
    folder = prompts / session
    folder.mkdir(parents=True, exist_ok=True)
    name = prompt_key(event) or "prompt.txt"
    (folder / name).write_text(text, encoding="utf-8")


def _field_limit(policy: dict) -> int:
    tokens = policy["tokens"]
    return int(tokens["prefer_state"]) * int(tokens["chars_per_token"]) // 2


def _git(root: str, args: list[str], policy: dict, runner) -> str:
    if runner is None:
        try:
            result = subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True, check=False,
                timeout=policy["git_timeout_seconds"],
            )
        except (subprocess.TimeoutExpired, OSError):
            return ""
    else:
        result = runner(args)
    if getattr(result, "returncode", 1) != 0:
        return ""
    return result.stdout or ""


def _numstat_rows(text: str) -> list[tuple[int, int, str]]:
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        if added == "-" or deleted == "-":
            rows.append((1, 1, path))
        else:
            try:
                rows.append((int(added), int(deleted), path))
            except ValueError:
                continue
    return rows


def commit_is_skippable(command: str, policy: dict, root: str, runner) -> bool:
    args = _commit_args(command)
    if args is None:
        return False
    message, include = parse_commit(args)
    prefixes = tuple(policy["skip"]["commit"]["message_prefixes"])
    if message is None or not message.startswith(prefixes):
        return False
    cached = _numstat_rows(_git(root, ["diff", "--cached", "--numstat"], policy, runner))
    rows = cached
    if include:
        rows = cached + _numstat_rows(_git(root, ["diff", "--numstat"], policy, runner))
    totals: dict[str, list[int]] = {}
    for added, deleted, path in rows:
        bucket = totals.setdefault(path, [0, 0])
        bucket[0] += added
        bucket[1] += deleted
    rule = policy["skip"]["commit"]
    if not totals or len(totals) > rule["max_files"]:
        return False
    added = sum(pair[0] for pair in totals.values())
    deleted = sum(pair[1] for pair in totals.values())
    return deleted == 0 and added + deleted <= rule["max_lines"]


def delete_is_junk(command: str, policy: dict) -> bool:
    paths = _rm_paths(command) or []
    dirs = policy["skip"]["delete_dirs"]
    return bool(paths) and all(under_junk(path, dirs) for path in paths)


def _spawn_state(event: dict, request: str, policy: dict) -> dict:
    incoming = tool_input(event)
    limit = _field_limit(policy)
    why = incoming.get("prompt")
    if why is None:
        source = incoming.get("source")
        why = json.dumps(source, ensure_ascii=False) if source is not None else ""
    files = []
    for key in ("files", "file_path", "path"):
        value = incoming.get(key)
        if isinstance(value, str):
            files.append(value)
        elif isinstance(value, list):
            files.extend(str(item) for item in value)
    return {
        "user_request": _clip(request, limit),
        "proposed_spawn": {
            "tool": tool_name(event),
            "model": incoming.get("model"),
            "why": _clip(str(why), limit),
        },
        "files_involved": files[:20],
        "goal": _clip(str(incoming.get("description") or ""), limit),
    }


def _commit_state(event: dict, request: str, policy: dict, runner) -> dict | None:
    incoming = tool_input(event)
    command = str(incoming.get("command", ""))
    message, include = ("", False)
    args = _commit_args(command)
    if args is not None:
        message, include = parse_commit(args)
    root = workspace_of(event)
    limit = _field_limit(policy)
    status = _git(root, ["status", "--short"], policy, runner)
    diff_args = ["diff", "--cached"]
    if include:
        diff_args = ["diff", "HEAD"]
    diff = redact_diff(_git(root, diff_args, policy, runner))
    state = {
        "user_request": _clip(request, limit),
        "git_status": _clip(status, limit),
        "diff_or_stat": _clip(diff, limit * 2),
        "commit_message_draft": message or "",
    }
    tokens = policy["tokens"]
    lines = diff.count("\n")
    if lines > tokens["diff_line_cap"] or _token_len(state, tokens["chars_per_token"]) > tokens["prefer_state"]:
        stat = _git(root, ["diff", "--cached", "--stat"], policy, runner)
        names = _git(root, ["diff", "--cached", "--name-only"], policy, runner)
        state["diff_or_stat"] = {"stat": _clip(stat, limit), "files": names.splitlines()[:200]}
    return state


def _edit_change(event: dict, policy: dict) -> tuple[list[str], str]:
    incoming = tool_input(event)
    path = str(incoming.get("file_path") or incoming.get("path") or "")
    limit = _field_limit(policy)
    if "content" in incoming:
        previous = _read_existing(path, event, policy) or ""
        change = previous + "\n---\n" + str(incoming.get("content", ""))
    else:
        old = str(incoming.get("old_string", incoming.get("old_str", "")))
        new = str(incoming.get("new_string", incoming.get("new_str", "")))
        change = old + "\n---\n" + new
    return ([path] if path else []), _clip(change, limit)


def _delete_state(event: dict, request: str, policy: dict) -> dict:
    incoming = tool_input(event)
    limit = _field_limit(policy)
    if tool_name(event) in SHELL_TOOLS:
        command = str(incoming.get("command", ""))
        paths = _rm_paths(command) or []
        change = command
    else:
        paths, change = _edit_change(event, policy)
    return {
        "user_request": _clip(request, limit),
        "paths": paths,
        "change": _clip(redact_diff(change) if change.startswith("diff --git") else change, limit),
    }


def build_state(fork: str, event: dict, request: str, policy: dict, runner) -> dict:
    if fork == "spawn":
        return _spawn_state(event, request, policy)
    if fork == "commit":
        return _commit_state(event, request, policy, runner) or {}
    return _delete_state(event, request, policy)


def within_budget(state: dict, questions: dict, policy: dict) -> bool:
    tokens = policy["tokens"]
    chars = tokens["chars_per_token"]
    longest = max(_token_len(question, chars) for question in questions.values())
    state_tokens = _token_len(state, chars)
    if state_tokens + longest > tokens["max_state_plus_longest_question"]:
        return False
    request = {"state": state, "model": PINNED_MODEL, "questions": questions}
    return _token_len(request, chars) <= tokens["max_request"]


# ---------- Jev ----------


def read_key(runner=subprocess.run) -> str:
    result = runner(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT, "-w"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 or not (result.stdout or "").strip():
        raise CallFailed("missing_key")
    return result.stdout.strip()


def post_jev(state: dict, questions: dict, policy: dict, key: str, opener) -> dict:
    body = {"state": state, "model": PINNED_MODEL, "questions": questions}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT, data=data, method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=policy["timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise CallFailed("429" if exc.code == 429 else "api_error") from None
    except (TimeoutError, socket.timeout):
        raise CallFailed("timeout") from None
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise CallFailed("timeout") from None
        raise CallFailed("api_error") from None
    except (json.JSONDecodeError, OSError):
        raise CallFailed("api_error") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("answers"), dict):
        raise CallFailed("api_error")
    return payload


def _probability(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def answers_usable(fork: str, questions: dict, answers: dict) -> bool:
    if fork == "spawn":
        got = answers.get(SPAWN_CHOICE)
        return isinstance(got, dict) and got.get("choice") in questions[SPAWN_CHOICE]["criteria"] and _probability(got.get("confidence"))
    if fork == "commit":
        return all(isinstance(answers.get(name), dict) and _probability(answers[name].get("noul")) for name in COMMIT_NOULS)
    choice = answers.get(DELETE_CHOICE)
    noul = answers.get(DELETE_NOUL)
    return (
        isinstance(choice, dict)
        and choice.get("choice") in questions[DELETE_CHOICE]["criteria"]
        and _probability(choice.get("confidence"))
        and isinstance(noul, dict)
        and _probability(noul.get("noul"))
    )


def apply_policy(fork: str, answers: dict, policy: dict) -> tuple[bool, str]:
    """(would_allow, one line). would_allow is whether this tool should run."""
    if fork == "spawn":
        choice = answers[SPAWN_CHOICE]
        option = str(choice["choice"])
        confidence = float(choice["confidence"])
        floor = policy["forks"]["spawn"]["confidence_floor"]
        if confidence < floor:
            option = policy["forks"]["spawn"]["low_confidence_option"]
        allow = option in {"cheap_explore", "careful_plan"}
        return allow, f"spawn {option} confidence={confidence:.2f}"
    if fork == "commit":
        extra = float(answers["extra_deletion"]["noul"])
        human = float(answers["needs_human"]["noul"])
        scope = float(answers["in_scope"]["noul"])
        rules = policy["forks"]["commit"]
        ask = extra >= rules["extra_deletion_ask"] or human >= rules["needs_human_ask"] or scope < rules["in_scope_floor"]
        line = f"commit ask_luke extra_deletion={extra:.2f} needs_human={human:.2f} in_scope={scope:.2f}"
        return (not ask), line
    choice = answers[DELETE_CHOICE]
    option = str(choice["choice"])
    confidence = float(choice["confidence"])
    unused = float(answers[DELETE_NOUL]["noul"])
    rules = policy["forks"]["delete"]
    if option == "ask_luke":
        decision = "ask_luke"
        allow = False
    elif option == "delete" and unused >= rules["unused_min"] and confidence >= rules["choice_confidence_min"]:
        decision = "delete"
        allow = True
    else:
        decision = "keep"
        allow = False
    return allow, f"delete {decision} unused={unused:.2f} confidence={confidence:.2f}"


def question_record(questions: dict) -> dict:
    return {key: question.get("instructions", "") for key, question in questions.items()}


# ---------- receipts and hook output ----------


def append_receipt(path: Path, row: dict, key: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(row, ensure_ascii=False)
    if key and key in text:
        text = text.replace(key, "[redacted]")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text + "\n")


@dataclass(frozen=True)
class Outcome:
    """What a request came to: the verdict, whether it was let through, and why it was skipped."""
    would: bool
    did: bool
    reason: str | None
    questions: dict = field(default_factory=dict)
    answers: dict = field(default_factory=dict)


def _receipt(fork: str, event: dict, policy: dict, state, outcome: Outcome) -> dict:
    return {
        "ts": now_iso(),
        "fork": fork,
        "model": PINNED_MODEL,
        "mode": policy.get("mode", "shadow"),
        "tool": tool_name(event),
        "state_hash": state_hash(state),
        "state_token_estimate": _token_len(state, policy["tokens"]["chars_per_token"]),
        "questions": outcome.questions,
        "answers": outcome.answers,
        "policy_version": policy["policy_version"],
        "would_allow": outcome.would,
        "did_allow": outcome.did,
        "skipped_reason": outcome.reason,
    }


def _allow() -> int:
    # No output: a bare exit 0 lets the tool run under the normal permission
    # prompts. Claude Code rejects a top-level "decision": "allow", and
    # permissionDecision "allow" would skip the prompts.
    return 0


def _deny(reason: str) -> int:
    print(json.dumps({"decision": "deny", "reason": reason}))
    print(reason, file=sys.stderr)
    return 2


HARD_LINES = {
    "wipe": "blocked: rm -rf of workspace",
    "git_dir": "blocked: deleting .git",
    "force_push": "blocked: force push to main or master",
}


@dataclass
class Deps:
    """What dispatch may be handed instead of reading the machine. None uses the real source."""

    policy: dict | None = None
    questions: dict | None = None
    key: str | None = None
    key_runner: Callable | None = None
    opener: Callable | None = None
    git: Callable | None = None
    prompts: Path | None = None
    receipts: Path | None = None


def _deps(given: dict | Deps | None) -> Deps:
    if isinstance(given, Deps):
        return given
    return Deps(**(given or {}))


def _config(deps: Deps) -> tuple[dict, dict] | None:
    """(policy, questions), or None when a config file cannot be read."""
    try:
        policy = deps.policy if deps.policy is not None else load_policy()
        questions = deps.questions if deps.questions is not None else load_questions()
    except PolicyError:
        return load_base_policy(), load_questions()
    except (OSError, yaml.YAMLError, json.JSONDecodeError):
        return None
    return policy, questions


def _early_skip(fork: str, event: dict, command: str, policy: dict, runner) -> tuple[str, dict] | None:
    """(reason, state) for a request the policy waves through before any prompt lookup, else None."""
    if fork == "commit" and command and commit_is_skippable(command, policy, workspace_of(event), runner):
        return "trivial_commit", {"command": command}
    if fork == "delete" and command and delete_is_junk(command, policy):
        return "junk_delete", {"command": command}
    if bad_id(event):
        return "bad_id", {"user_request": ""}
    return None


class Verdict(NamedTuple):
    state: dict
    key: str | None
    would: bool
    line: str
    reason: str | None
    answers: dict


def _ask_jev(fork: str, state: dict, fork_questions: dict, policy: dict, deps: Deps) -> Verdict:
    """Ask Jev, and fall back to "would allow" with the failure as the reason when the call cannot be used.

    The size check runs once, after the key is redacted.
    """
    key = None
    try:
        key = deps.key if deps.key is not None else read_key(deps.key_runner or subprocess.run)
        state = redact_key(state, key)
        if not within_budget(state, fork_questions, policy):
            raise CallFailed("state_too_large")
        payload = post_jev(state, fork_questions, policy, key, deps.opener or urllib.request.urlopen)
        got = payload["answers"]
        if not answers_usable(fork, fork_questions, got):
            raise CallFailed("api_error")
        would, line = apply_policy(fork, got, policy)
        return Verdict(state, key, would, line, None, got)
    except CallFailed as exc:
        return Verdict(state, key, True, "", exc.reason, {})


def dispatch(event: dict, deps: dict | Deps | None = None) -> int:
    deps = _deps(deps)
    prompts = Path(deps.prompts or PROMPTS)
    receipts = Path(deps.receipts or RECEIPTS)
    if not tool_name(event) and "prompt" in event:
        save_prompt(event, prompts)
        return 0

    command = str(tool_input(event).get("command", "")) if tool_name(event) in SHELL_TOOLS else ""
    rule = hard_rule(command, workspace_of(event)) if command else None
    config = _config(deps)
    if config is None:
        return _deny(HARD_LINES[rule]) if rule else 0
    policy, questions = config

    if rule:
        append_receipt(receipts, _receipt(
            "hard", event, policy, {"command": command}, Outcome(False, False, rule),
        ), None)
        return _deny(HARD_LINES[rule])

    fork = classify(event, policy)
    if fork is None:
        return 0

    def skip(state, reason, question_rows=None):
        append_receipt(receipts, _receipt(
            fork, event, policy, state, Outcome(True, True, reason, question_rows or {}),
        ), None)
        return _allow()

    runner = deps.git
    early = _early_skip(fork, event, command, policy, runner)
    if early:
        return skip(early[1], early[0])

    request = read_prompt(event, prompts)
    if request is None:
        return skip({"user_request": ""}, "missing_session")

    state = build_state(fork, event, request, policy, runner)
    fork_questions = questions[fork]
    verdict = _ask_jev(fork, state, fork_questions, policy, deps)
    active = policy.get("mode") == "active"
    did = verdict.would if active else True
    append_receipt(receipts, _receipt(
        fork, event, policy, verdict.state,
        Outcome(verdict.would, did, verdict.reason, question_record(fork_questions), verdict.answers),
    ), verdict.key)
    if active and not verdict.would:
        return _deny(verdict.line)
    return _allow()


def dry_run() -> int:
    """Three canned forks through the real key. Does not read the live git tree."""
    policy = load_policy()
    questions = load_questions()
    cases = [
        ("spawn", {
            "user_request": "Add a shadow referee. Do not spawn a helper for it.",
            "proposed_spawn": {"tool": "spawn_subagent", "model": None, "why": "Write the hook in a side agent."},
            "files_involved": ["scripts/jev_referee.py"],
            "goal": "implement the referee",
        }),
        ("commit", {
            "user_request": "Wire the Jev referee.",
            "git_status": "M scripts/jev_referee.py",
            "diff_or_stat": "diff --git a/scripts/jev_referee.py b/scripts/jev_referee.py\n+def dispatch():\n+    return 0\n",
            "commit_message_draft": "feat: add the shadow Jev referee",
        }),
        ("delete", {
            "user_request": "Remove the unused sample helper.",
            "paths": ["scripts/sample_helper.py"],
            "change": "def sample_helper():\n    return 1\n---\n",
        }),
    ]
    try:
        key = read_key()
    except CallFailed as exc:
        key = None
        failed = exc.reason
    else:
        failed = None
    opener = urllib.request.urlopen
    written = 0
    for fork, state in cases:
        fork_questions = questions[fork]
        answers: dict = {}
        reason = failed
        would = True
        redacted = redact_key(state, key) if key else state
        if key and within_budget(redacted, fork_questions, policy):
            try:
                payload = post_jev(redacted, fork_questions, policy, key, opener)
                answers = payload.get("answers") or {}
                if answers_usable(fork, fork_questions, answers):
                    would, _line = apply_policy(fork, answers, policy)
                    reason = None
                else:
                    reason = "api_error"
                    answers = {}
            except CallFailed as exc:
                reason = exc.reason
        elif key:
            reason = "state_too_large"
        outcome = Outcome(would, True, reason, question_record(fork_questions) if not reason else {}, answers)
        row = _receipt(fork, {"toolName": "dry_run"}, policy, state, outcome)
        append_receipt(RECEIPTS, row, key)
        written += 1
    leaked = _key_in_tree(key) if key else False
    print(f"dry-run receipts={written} key_absent={'false' if leaked else 'true'}")
    return 1 if leaked else 0


def _key_in_tree(key: str) -> bool:
    roots = [ROOT / "receipts" / "decisions.jsonl", ROOT / "jev"]
    for path in roots:
        files = [path] if path.is_file() else list(path.rglob("*")) if path.is_dir() else []
        for candidate in files:
            if not candidate.is_file():
                continue
            try:
                if key in candidate.read_text(encoding="utf-8", errors="replace"):
                    return True
            except OSError:
                continue
    return False


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--dry-run"]:
        return dry_run()
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(event, dict):
        return 0
    return dispatch(event)


if __name__ == "__main__":
    sys.exit(main())
