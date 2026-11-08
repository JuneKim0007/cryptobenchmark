"""What watch prints for each event: one line per finished step, a running counter per model step."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from ..dto.event import BUG, DECISION, END, ERROR, FINDING, LOG, RUN_END, RUN_START, START, Event
from .status import status_line
from .views import counts_text, seconds

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


def _end(e: Event) -> str:
    name = " ".join(p for p in (e.stage, e.step, e.app) if p)
    said = " ".join(p for p in (e.outcome, e.detail, counts_text(e.data)) if p)
    took = f" ({seconds(e.durationMs)})" if e.durationMs is not None else ""
    return f"{name}: {said}{took}" if said else f"{name}{took}"


TEXTS: dict[str, Callable[[Event], str | None]] = {
    END: _end,
    RUN_START: lambda e: f"run {e.detail or e.step}: started",
    RUN_END: lambda e: f"run {e.step}: {e.outcome} ({seconds(e.durationMs)})",
    ERROR: lambda e: f"error {e.detail}",
    BUG: lambda e: f"bug {e.detail}",
    FINDING: status_line,
    LOG: lambda e: f"{e.outcome}: {e.detail}" if e.outcome in SHOWN_LEVELS else None,
}


class Progress:

    def __init__(self):
        self.counters: dict[tuple, Counter] = {}

    def feed(self, e: Event) -> list[Line]:
        if e.kind == "model":
            return self._model(e)
        if e.event == RUN_START:
            # a step a killed run left open never ends; the next run starts its counters afresh
            self.counters.clear()
        text = TEXTS[e.event](e) if e.event in TEXTS else None
        return [] if text is None else [Line(text)]

    def _model(self, e: Event) -> list[Line]:
        key = (e.stage, e.step, e.app)
        if e.event == START:
            self.counters[key] = Counter(e.ts, int(e.data.get("pending") or 0))
            return [self._line(key, e)]
        c = self.counters.get(key)
        if c is None:
            c = self.counters[key] = Counter(e.ts, 0)
        if e.event == DECISION:
            c.done += 1
            c.rejected += e.data.get("rejected") or 0
            if e.costUsd is not None:
                c.cost, c.priced = c.cost + e.costUsd, True
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
