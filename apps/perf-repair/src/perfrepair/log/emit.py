"""What library code calls: emit() one event; step() a timed step with its counts and the files it wrote."""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path

from ..dto.event import END, START
from ..files import sha256_file

EVENT_ATTR = "perfrepair_event"
LOGGER = logging.getLogger("perfrepair.event")


def emit(stage: str, step: str, event: str, *, kind: str = "static", item: str | None = None, app: str | None = None,
         outcome: str | None = None, durationMs: int | None = None, tokens: dict | None = None,
         costUsd: float | None = None, ref: str | None = None, detail: str = "", data: dict | None = None,
         level: int = logging.INFO) -> None:
    fields = {"stage": stage, "step": step, "event": event, "kind": kind, "item": item, "app": app, "outcome": outcome,
              "durationMs": durationMs, "tokens": tokens, "costUsd": costUsd, "ref": ref, "detail": detail,
              "data": dict(data or {})}
    LOGGER.log(level, detail or f"{stage} {step} {event}", extra={EVENT_ATTR: fields})


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


class Step:
    def __init__(self):
        self.outcome, self.detail, self.counts, self.files = "ok", "", {}, {}

    def count(self, **counts) -> None:
        self.counts.update(counts)

    def wrote(self, *paths: Path) -> None:
        self.files.update({str(p): sha256_file(p) for p in paths})

    def data(self) -> dict:
        return {**({"counts": self.counts} if self.counts else {}), **({"files": self.files} if self.files else {})}


@contextmanager
def step(stage: str, name: str, *, kind: str = "static", item: str | None = None, app: str | None = None,
         detail: str = "", data: dict | None = None):
    s = Step()
    emit(stage, name, START, kind=kind, item=item, app=app, detail=detail, data=data)
    started = time.monotonic()
    try:
        yield s
    except BaseException as e:
        # a terminated failure already has its status line; its end only records it
        reported = {"code": e.code, "reported": True} if getattr(e, "reported", False) else {}
        emit(stage, name, END, kind=kind, item=item, app=app, outcome="failed", durationMs=elapsed_ms(started),
             detail=f"{type(e).__name__}: {e}", data={**s.data(), **reported})
        raise
    emit(stage, name, END, kind=kind, item=item, app=app, outcome=s.outcome, durationMs=elapsed_ms(started),
         detail=s.detail, data=s.data())
