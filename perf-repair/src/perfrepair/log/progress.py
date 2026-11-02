"""What watch prints for each event: one line per finished step, a running counter per model step."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..dto.event import BUG, DECISION, END, ERROR, LOG, RUN_END, RUN_START, START, TURN, Event
from .views import seconds

SHOWN_LEVELS = ("warning", "error", "critical")


@dataclass
class Counter:
    started: str
    total: int
    done: int = 0
    rejected: int = 0
    cost: float = 0.0
    priced: bool = False


@dataclass(frozen=True)
class Line:
    text: str
    transient: bool = False  # a counter a terminal may overwrite in place


def _ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _counts(e: Event) -> str:
    return " ".join(f"{k}={v}" for k, v in (e.data.get("counts") or {}).items())


class Progress:

    def __init__(self):
        self.counters: dict[tuple, Counter] = {}

    def feed(self, e: Event) -> list[Line]:
        if e.kind == "model":
            return self._model(e)
        if e.event == END:
            name = " ".join(p for p in (e.stage, e.step, e.app) if p)
            text = ": ".join(p for p in (name, " ".join(p for p in (e.outcome, e.detail, _counts(e)) if p)) if p)
            return [Line(text + (f" ({seconds(e.durationMs)})" if e.durationMs is not None else ""))]
        if e.event == RUN_START:
            return [Line(f"run {e.detail or e.step}: started")]
        if e.event == RUN_END:
            return [Line(f"run {e.step}: {e.outcome} ({seconds(e.durationMs)})")]
        if e.event in (ERROR, BUG):
            return [Line(f"{e.event} {e.detail}")]
        if e.event == LOG and e.outcome in SHOWN_LEVELS:
            return [Line(f"{e.outcome}: {e.detail}")]
        return []

    def _model(self, e: Event) -> list[Line]:
        key = (e.stage, e.step, e.app)
        if e.event == START:
            self.counters[key] = Counter(e.ts, int(e.data.get("pending") or 0))
            return [self._line(key, e)]
        c = self.counters.get(key)
        if c is None:
            c = self.counters[key] = Counter(e.ts, 0)
        if e.event == TURN:
            c.rejected += e.outcome != "accepted"
            if e.costUsd is not None:
                c.cost, c.priced = c.cost + e.costUsd, True
        elif e.event == DECISION:
            c.done += 1
        elif e.event == END:
            line = self._line(key, e, final=True)
            del self.counters[key]
            return [line]
        return [self._line(key, e)]

    def _line(self, key: tuple, e: Event, final: bool = False) -> Line:
        c = self.counters[key]
        name = " ".join(p for p in key if p)
        parts = [f"{name} {c.done}/{max(c.total, c.done)}", f"{c.rejected} rejected"]
        parts += [f"${c.cost:.4f}"] if c.priced else []
        parts.append(f"{(_ts(e.ts) - _ts(c.started)).total_seconds():.0f}s")
        return Line(" · ".join(parts) + (" · done" if final else ""), transient=not final)
