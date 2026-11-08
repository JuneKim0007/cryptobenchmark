"""The real tokens and cost of a job's turns, as their replies' usage gives them."""
from __future__ import annotations

from .ask import Turn

TOKEN_KEYS = ("input", "output", "cacheRead", "cacheWrite")


def tokens(turns: list[Turn]) -> dict | None:
    usages = [t.reply.get("usage") or {} for t in turns if t.reply]
    if not any(usages):
        return None
    return {k: sum(int(u.get(k) or 0) for u in usages) for k in TOKEN_KEYS}


def cost(turns: list[Turn]) -> float | None:
    costs = [(t.reply.get("usage") or {}).get("costUsd") for t in turns if t.reply]
    costs = [c for c in costs if c is not None]
    return round(sum(costs), 6) if costs else None
