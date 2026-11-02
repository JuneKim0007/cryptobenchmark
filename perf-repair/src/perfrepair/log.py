"""The stderr handler a command attaches when it starts; library code only logs and never configures handlers."""
from __future__ import annotations

import logging
import sys

ROOT = "perfrepair"


class _Stderr(logging.StreamHandler):
    # the current sys.stderr per record, so a replaced stderr (tests, a guide calling a command) still receives it
    @property
    def stream(self):
        return sys.stderr

    @stream.setter
    def stream(self, _):
        pass


def log_to_stderr() -> None:
    logger = logging.getLogger(ROOT)
    if not any(isinstance(h, _Stderr) for h in logger.handlers):
        handler = _Stderr()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
