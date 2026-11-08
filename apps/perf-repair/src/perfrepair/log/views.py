"""The readable views: each a pure function of one event, so a view never says what events.jsonl does not."""
from __future__ import annotations

from typing import Callable

from ..dto.event import BUG, Event
from ..run_dir import BUG_LOG, STATUS_LOG
from .status import status_line


def seconds(ms: int | None) -> str:
    return "" if ms is None else f"{ms / 1000:.1f}s"


def tokens_text(tokens: dict | None) -> str:
    if not tokens:
        return ""
    return f"tokens {tokens.get('input', 0)}/{tokens.get('output', 0)} cache {tokens.get('cacheRead', 0)}"


def counts_text(data: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in (data.get("counts") or {}).items())


def _bug(e: Event) -> str | None:
    if e.event != BUG:
        return None
    return f"{e.ts} {e.stage} {e.step}: {e.detail}\n{e.data.get('traceback', '').rstrip()}"


VIEWS: tuple[tuple[str, Callable[[Event], str | None]], ...] = (
    (BUG_LOG, _bug),
    (STATUS_LOG, status_line),
)


def render(events: list[Event]) -> dict[str, list[str]]:
    """Every view's lines from a list of events: what the sink appends, recomputed."""
    out: dict[str, list[str]] = {}
    for path, view in VIEWS:
        out[path] = [line for line in map(view, events) if line is not None]
    return out
