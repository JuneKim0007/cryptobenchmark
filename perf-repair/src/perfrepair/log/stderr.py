"""The stderr handler: the log lines a command prints; event records stay in events.jsonl."""
from __future__ import annotations

import logging
import sys

from .emit import EVENT_ATTR


class Stderr(logging.StreamHandler):
    # the current sys.stderr per record, so a replaced stderr (tests, a guide calling a command) still receives it
    @property
    def stream(self):
        return sys.stderr

    @stream.setter
    def stream(self, _):
        pass


def stderr_handler() -> Stderr:
    handler = Stderr()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(lambda record: not hasattr(record, EVENT_ATTR))
    return handler
