"""The one reader of `timeouts.<child>`: the seconds a child process may run, read from the run's settings when it
starts; without settings, or with a bad value (one warning), the row's default."""
from __future__ import annotations

from ..inputs.table import TIMEOUT_CLAUDE, TIMEOUT_PIPELINE, Row
from . import current


def _seconds(row: Row) -> int:
    loaded = current.settings()
    return row.default if loaded is None else loaded.read(row)


def claude_seconds() -> int:
    return _seconds(TIMEOUT_CLAUDE)


def pipeline_seconds() -> int:
    return _seconds(TIMEOUT_PIPELINE)
