"""The readable views: each a pure function of one event, so a view never says what events.jsonl does not."""
from __future__ import annotations

from typing import Callable

from ..dto.event import BUG, Event
from ..run_dir import BUG_LOG, GROUPING_AI_LOG, SCREENING_AI_LOG


def seconds(ms: int | None) -> str:
    return "" if ms is None else f"{ms / 1000:.1f}s"


def tokens_text(tokens: dict | None) -> str:
    if not tokens:
        return ""
    return f"tokens {tokens.get('input', 0)}/{tokens.get('output', 0)} cache {tokens.get('cacheRead', 0)}"


def model_line(e: Event) -> str:
    d = e.data
    where = f"s{d['session']}t{d['turn']}" if "session" in d and "turn" in d else ""
    counts = " ".join(f"{k}={v}" for k, v in (d.get("counts") or {}).items())
    parts = [e.ts, e.step, e.event, e.item or "", where, e.outcome or "", seconds(e.durationMs), tokens_text(e.tokens),
             "" if e.costUsd is None else f"${e.costUsd:.4f}", counts, e.detail]
    line = " ".join(p for p in parts if p)
    problems = "".join(f"\n  - {p}" for p in d.get("problems") or ())
    return line + (f" -> {e.ref}" if e.ref else "") + problems


def _model_view(stage: str) -> Callable[[Event], str | None]:
    return lambda e: model_line(e) if e.stage == stage and e.kind == "model" else None


def _bug(e: Event) -> str | None:
    if e.event != BUG:
        return None
    return f"{e.ts} {e.stage} {e.step}: {e.detail}\n{e.data.get('traceback', '').rstrip()}"


VIEWS: tuple[tuple[str, Callable[[Event], str | None]], ...] = (
    (SCREENING_AI_LOG, _model_view("screening")),
    (GROUPING_AI_LOG, _model_view("grouping")),
    (BUG_LOG, _bug),
)


def render(events: list[Event]) -> dict[str, list[str]]:
    """Every view's lines from a list of events: what the sink appends, recomputed."""
    out: dict[str, list[str]] = {}
    for path, view in VIEWS:
        out[path] = [line for line in map(view, events) if line is not None]
    return out
