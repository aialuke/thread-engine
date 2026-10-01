#!/usr/bin/env python3
"""Checks for scripts/durable.py. Stdlib only."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import durable  # noqa: E402


def dead_pid() -> int:
    pid = 1 << 22
    while durable.pid_alive(pid):
        pid += 1
    return pid


class Writes(unittest.TestCase):
    def test_a_dead_temp_is_removed_on_the_next_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "state.json"
            stale = root / f".state.json.{dead_pid()}.abc"
            stale.write_text("torn", encoding="utf-8")
            durable.atomic_write(target, "ok\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "ok\n")
            self.assertFalse(stale.exists())

    def test_a_stale_lock_is_replaced_and_a_live_one_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / ".write.lock"
            lock.write_text(f"{dead_pid()}\n", encoding="utf-8")
            held = durable.acquire_write_lock(root)
            self.assertTrue(held.owned)
            self.assertEqual(lock.read_text(encoding="utf-8").strip(), str(os.getpid()))
            again = durable.acquire_write_lock(root)
            self.assertFalse(again.owned)
            held.release()
            self.assertFalse(lock.exists())

    def test_a_live_lock_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / ".write.lock"
            proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
            self.addCleanup(lambda: (proc.kill(), proc.wait()))
            lock.write_text(f"{proc.pid}\n", encoding="utf-8")
            with self.assertRaises(durable.LockBusy):
                durable.acquire_write_lock(root)
            self.assertEqual(lock.read_text(encoding="utf-8").strip(), str(proc.pid))


if __name__ == "__main__":
    unittest.main()
