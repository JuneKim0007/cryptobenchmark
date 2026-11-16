"""attach(): the handlers a command installs under its root logger, stderr and the event sink; command_run(): one command's run events."""
from __future__ import annotations

import logging
import secrets
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from cryptobench.shared.paths import BUG_LOG
from .emit import LOGGER, elapsed_ms, emit
from .event import RUN_END, RUN_START
from .sink import EventSink, Views
from .stderr import Stderr, stderr_handler

SINK = EventSink(())
_root: str | None = None
_depth, _opened = 0, time.monotonic()


def _run_id() -> str:
    return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{secrets.token_hex(3)}"


def _sink(root: str, views: Views) -> None:
    # one sink per process; another root or views replaces it
    global SINK, _root
    if (root, views) == (_root, SINK.views):
        return
    for logger in ([logging.getLogger(_root)] if _root is not None else []) + [LOGGER]:
        logger.removeHandler(SINK)
    SINK, _root = EventSink(views), root


def attach(root: str, views: Views, device_results: Path | None = None) -> None:
    """At a command's start with no folder: handlers on the root logger, a new run; again once the folder is known:
    events.jsonl."""
    _sink(root, views)
    logger = logging.getLogger(root)
    if not any(isinstance(h, Stderr) for h in logger.handlers):
        logger.addHandler(stderr_handler())
    # the root's own records and the library's events (which a root above them already receives); DEBUG reaches
    # events.jsonl only, stderr keeps INFO
    for target in (logger,) if LOGGER.name.startswith(f"{root}.") else (logger, LOGGER):
        if SINK not in target.handlers:
            target.addHandler(SINK)
        target.setLevel(logging.DEBUG)
    # a command another command calls in-process joins the caller's run
    global _opened
    if _depth == 0 and device_results is None:
        _opened = time.monotonic()
        SINK.open(_run_id())
        command = _command()
        emit("run", command, RUN_START, detail=" ".join([command, *sys.argv[1:]]))
    if device_results is not None:
        SINK.bind(Path(device_results))


def nested() -> bool:
    """Inside command_run, whether another command's run encloses this one: a command it calls in-process."""
    return _depth > 1


def current_run() -> str | None:
    return SINK.run


def run_id() -> str:
    """The attached run's id; a call outside any command run gets one of its own."""
    return SINK.run or _run_id()


def bug_log() -> Path | None:
    return SINK.path(BUG_LOG)


def _command() -> str:
    path = Path(sys.argv[0])
    parts = path.parts
    if _root in parts and path.stem == "__main__":
        return ".".join(parts[len(parts) - parts[::-1].index(_root):-1]) or _root
    return path.stem or _root or ""


class Run:
    outcome = "failed"


@contextmanager
def command_run():
    """The outermost command of a process emits run_end, then lets the folder go; attach() emitted its run_start."""
    global _depth
    outer, run = _depth == 0, Run()
    _depth += 1
    try:
        yield run
    except KeyboardInterrupt:
        run.outcome = "interrupted"
        raise
    finally:
        _depth -= 1
        if outer:
            emit("run", _command(), RUN_END, outcome=run.outcome, durationMs=elapsed_ms(_opened))
            SINK.close()
