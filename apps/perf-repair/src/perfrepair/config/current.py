"""The run's settings: the first command of a run that loads them installs them; a command it runs in-process joins
that run and keeps them. What is read when a code fires or a child starts (stops, timeouts) reads them here."""
from __future__ import annotations

from ..log.attach import current_run
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


def reset() -> None:
    global _loaded, _run
    _loaded, _run = None, None
