"""The one reader of `stops.<code>`: each read from the run's settings when its
code fires, through the row's resolver (unset: the default; bad: one warning, then the default); a fixed code set is
one warning, ignored."""
from __future__ import annotations

import logging

from ..inputs.table import STOP_ROWS
from ..stop import policy
from ..stop.codes import Code
from . import current
from .load import Loaded

LOG = logging.getLogger(__name__)


def read_stop(code: Code) -> str | None:
    loaded = current.settings()
    if loaded is None:
        return None
    if code.fixed:
        _fixed(loaded, code)
        return None
    return loaded.read(STOP_ROWS[code.code])


def _fixed(loaded: Loaded, code: Code) -> None:
    key = f"stops.{code.code}"
    value = loaded.settings.get(key)
    # remembered beside the values it chose, so one load warns once
    if value is None or (key, "fixed") in loaded.chosen:
        return
    loaded.chosen[key, "fixed"] = value
    LOG.warning(f"stop_fixed: {key} {value}, {code.code} is fixed ({code.why}); ignored (file {loaded.file})",
                extra={"code": "stop_fixed", "input": key, "source": f"file {loaded.file}"})


def install_stops(loaded: Loaded) -> None:
    """The run's settings, and this module as the stops reader terminate asks."""
    current.install(loaded)
    policy.install(read_stop)
