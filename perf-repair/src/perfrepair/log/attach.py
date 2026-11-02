"""attach(): the handlers a command installs, stderr and the event sink; command_run(): one command's run events."""
from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from ..dto.event import RUN_END, RUN_START
from ..run_dir import BUG_LOG
from .emit import elapsed_ms, emit
from .sink import EventSink
from .stderr import Stderr, stderr_handler

ROOT = "perfrepair"
SINK = EventSink()
_depth = 0


def _run_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{os.getpid()}"


def attach(device_results: Path | None = None) -> None:
    """At a command's start with no folder: handlers, a new run; again once the folder is known: events.jsonl."""
    logger = logging.getLogger(ROOT)
    if not any(isinstance(h, Stderr) for h in logger.handlers):
        logger.addHandler(stderr_handler())
    if SINK not in logger.handlers:
        logger.addHandler(SINK)
    # DEBUG reaches events.jsonl only; stderr keeps INFO
    logger.setLevel(logging.DEBUG)
    # a command another command calls in-process joins the caller's run
    if _depth == 0 and device_results is None:
        SINK.open(_run_id())
    if device_results is not None:
        SINK.bind(Path(device_results))


def bug_log() -> Path | None:
    return SINK.path(BUG_LOG)


def _command() -> str:
    path = Path(sys.argv[0])
    parts = path.parts
    if ROOT in parts and path.stem == "__main__":
        return ".".join(parts[len(parts) - parts[::-1].index(ROOT):-1]) or ROOT
    return path.stem or ROOT


class Run:
    outcome = "failed"


@contextmanager
def command_run():
    """The outermost command of a process emits run_start and run_end, then lets the folder go."""
    global _depth
    outer, run, started = _depth == 0, Run(), time.monotonic()
    command = _command()
    if outer:
        emit("run", command, RUN_START, detail=" ".join([command, *sys.argv[1:]]))
    _depth += 1
    try:
        yield run
    except KeyboardInterrupt:
        run.outcome = "interrupted"
        raise
    finally:
        _depth -= 1
        if outer:
            emit("run", command, RUN_END, outcome=run.outcome, durationMs=elapsed_ms(started))
            SINK.close()
