from __future__ import annotations


class LoopError(Exception):
    pass


def need(cond: bool, message: str) -> None:
    if not cond:
        raise LoopError(message)
