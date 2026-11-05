"""The readable views: each a pure function of one event, so a view never says what events.jsonl does not."""
from __future__ import annotations

from typing import Callable

from ..dto.event import BUG, Event
from ..run_dir import (AI_CLASSIFY_LOG, AI_GROUPING_LOG, AI_REPLACE_LOG, AI_SCREENING_LOG,
                       AI_WORTHINESS_LOG, BUG_LOG, STATUS_LOG)
from .status import status_line


def seconds(ms: int | None) -> str:
    return "" if ms is None else f"{ms / 1000:.1f}s"


def tokens_text(tokens: dict | None) -> str:
    if not tokens:
        return ""
    return f"tokens {tokens.get('input', 0)}/{tokens.get('output', 0)} cache {tokens.get('cacheRead', 0)}"


def cost_text(cost: float | None) -> str:
    return "" if cost is None else f"${cost:.4f}"


def counts_text(data: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in (data.get("counts") or {}).items())


def model_line(e: Event) -> str:
    d = e.data
    where = f"s{d['session']}t{d['turn']}" if "session" in d and "turn" in d else ""
    parts = [e.ts, e.step, e.event, e.item, where, e.outcome, seconds(e.durationMs), tokens_text(e.tokens),
             cost_text(e.costUsd), counts_text(d), e.detail]
    line = " ".join(p for p in parts if p)
    problems = "".join(f"\n  - {p}" for p in d.get("problems") or ())
    return line + (f" -> {e.ref}" if e.ref else "") + problems


# (stage, step) → its file; a step of None takes the stage's other model steps
AI_LOGS: dict[tuple[str, str | None], str] = {
    ("screening", "classify"): AI_CLASSIFY_LOG, ("screening", None): AI_SCREENING_LOG, ("grouping", None): AI_GROUPING_LOG,
    ("worthiness", None): AI_WORTHINESS_LOG, ("replace", None): AI_REPLACE_LOG}


def ai_log(e: Event) -> str | None:
    if e.kind != "model":
        return None
    return AI_LOGS.get((e.stage, e.step)) or AI_LOGS.get((e.stage, None))


def _model_view(path: str) -> Callable[[Event], str | None]:
    return lambda e: model_line(e) if ai_log(e) == path else None


def _bug(e: Event) -> str | None:
    if e.event != BUG:
        return None
    return f"{e.ts} {e.stage} {e.step}: {e.detail}\n{e.data.get('traceback', '').rstrip()}"


VIEWS: tuple[tuple[str, Callable[[Event], str | None]], ...] = (
    *((path, _model_view(path)) for path in dict.fromkeys(AI_LOGS.values())),
    (BUG_LOG, _bug),
    (STATUS_LOG, status_line),
)


def render(events: list[Event]) -> dict[str, list[str]]:
    """Every view's lines from a list of events: what the sink appends, recomputed."""
    out: dict[str, list[str]] = {}
    for path, view in VIEWS:
        out[path] = [line for line in map(view, events) if line is not None]
    return out
