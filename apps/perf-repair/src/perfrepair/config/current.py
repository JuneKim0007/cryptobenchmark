"""The run's settings: the first command of a run that loads them installs them; a command it runs in-process joins
that run and keeps them. What is read when a code fires or a child starts (stops, timeouts) or an app tree is walked
(apps.copies) reads them here."""
from __future__ import annotations

from typing import Any

from cryptobench.shared.log.attach import current_run
from ..inputs.table import Row
from .load import Loaded

_loaded: Loaded | None = None
_run: str | None = None


def install(loaded: Loaded) -> None:
    global _loaded, _run
    if _loaded is not None and _run is not None and _run == current_run():
        return
    _loaded, _run = loaded, current_run()


def settings() -> Loaded | None:
    return _loaded


def read(row: Row) -> Any:
    """A row's value from the run's settings; without settings, its default."""
    return row.default if _loaded is None else _loaded.read(row)


def reset() -> None:
    global _loaded, _run
    _loaded, _run = None, None
