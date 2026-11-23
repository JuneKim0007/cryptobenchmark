"""The one reader of `timeouts.<child>`: the seconds a child process may run, read from the run's settings when it
starts; without settings, or with a bad value (one warning), the row's default."""
from __future__ import annotations

from ..inputs.check import UNLIMITED
from ..inputs.table import TIMEOUT_CLAUDE, TIMEOUT_PIPELINE
from . import current


def claude_seconds() -> int:
    return current.read(TIMEOUT_CLAUDE)


def pipeline_seconds() -> int | None:
    """None waits with no cap."""
    seconds = current.read(TIMEOUT_PIPELINE)
    return None if seconds == UNLIMITED else seconds
