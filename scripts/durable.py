"""Writes that finish in one state whether they run once, twice, or die halfway.

Stdlib only. Callers keep their own rules for what is written; this module only
makes the write itself converge.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path


class LockBusy(Exception):
    pass


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _drop_stale_temps(path: Path) -> None:
    """Remove this file's leftover temp files when the process that made them is gone.

    A hard kill skips the cleanup in atomic_write. The name carries that process's pid.
    Temps from before pid names are removed once they are an hour old.
    """
    prefix = f".{path.name}."
    if not path.parent.is_dir():
        return
    for candidate in path.parent.iterdir():
        if not candidate.is_file() or not candidate.name.startswith(prefix):
            continue
        rest = candidate.name[len(prefix):]
        pid_text = rest.split(".", 1)[0]
        if pid_text.isdigit():
            if not pid_alive(int(pid_text)):
                candidate.unlink(missing_ok=True)
            continue
        try:
            age = time.time() - candidate.stat().st_mtime
        except OSError:
            continue
        if age > 3600:
            candidate.unlink(missing_ok=True)


def atomic_write(path: Path, text: str) -> None:
    """Write the whole text or leave the previous file unchanged."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _drop_stale_temps(path)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.{os.getpid()}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def write_new_text(directory: Path, stem: str, suffix: str, text: str) -> Path:
    """Write text to a new file. A second caller in the same second gets its own name."""
    directory.mkdir(parents=True, exist_ok=True)
    names = (f"{stem}{suffix}", f"{stem}-{os.getpid()}{suffix}",
             f"{stem}-{os.getpid()}-{time.time_ns()}{suffix}")
    path = None
    for name in names:
        candidate = directory / name
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            continue
        os.close(fd)
        path = candidate
        break
    if path is None:
        raise OSError(f"could not claim a new file in {directory}")
    atomic_write(path, text)
    return path


def append_line(path: Path, line: str) -> None:
    """Append one complete line. Two writers cannot split a line between them."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = line if line.endswith("\n") else line + "\n"
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(text)
            handle.flush()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_json_line(path: Path, row: dict, same) -> bool:
    """Append one JSON row unless `same(existing, row)` is already true. Returns whether it wrote.

    The check and the append hold one lock, so two retries of the same row write it once.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.seek(0)
            for existing in handle:
                existing = existing.strip()
                if not existing:
                    continue
                try:
                    old = json.loads(existing)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path} has a line that is not JSON") from exc
                if same(old, row):
                    return False
            handle.seek(0, os.SEEK_END)
            handle.write(line)
            handle.flush()
            return True
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class WriteLock:
    """A pid file at .write.lock. The owner deletes it; a child of the owner does not."""

    def __init__(self, path: Path, owned: bool) -> None:
        self.path = path
        self.owned = owned

    def release(self) -> None:
        if not self.owned:
            return
        try:
            current = int(self.path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return
        if current == os.getpid():
            self.path.unlink(missing_ok=True)


def _holder(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def acquire_write_lock(root: Path) -> WriteLock:
    """Take the repo write lock, or share the one this process or its parent already holds.

    A lock whose pid is not running is stale and is replaced. A live other pid raises LockBusy.
    """
    path = root / ".write.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    me = os.getpid()
    for _ in range(3):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            holder = _holder(path)
            if holder in {me, os.getppid()}:
                return WriteLock(path, owned=False)
            if holder is not None and pid_alive(holder):
                raise LockBusy(f"another writer is running (pid {holder})")
            path.unlink(missing_ok=True)
            continue
        try:
            os.write(fd, f"{me}\n".encode())
        finally:
            os.close(fd)
        return WriteLock(path, owned=True)
    raise LockBusy("could not take the write lock")
