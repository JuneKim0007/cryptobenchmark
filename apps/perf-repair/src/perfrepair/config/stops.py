"""The one reader of `stops.<code>` and its alias `device.bundled.onMissing`: each read from the run's settings when its
code fires, through the row's resolver (unset: the default; bad: one warning, then the default); a fixed code set is
one warning, ignored."""
from __future__ import annotations

import logging

from ..inputs.table import BUNDLED_ON_MISSING, STOP_ROWS
from ..stop import policy
from ..stop.codes import Code
from . import current
from .load import Loaded

LOG = logging.getLogger(__name__)
ALIASES = {"bundled_missing": BUNDLED_ON_MISSING}


def read_stop(code: Code) -> str | None:
    loaded = current.settings()
    if loaded is None:
        return None
    if code.fixed:
        _fixed(loaded, code)
        return None
    row = STOP_ROWS[code.code]
    value = loaded.read(row)
    alias = ALIASES.get(code.code)
    # the stops key wins; the older key is read only when the stops key is unset
    if alias is not None and loaded.sources.get(row.key) == "default":
        return loaded.read(alias)
    return value


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
