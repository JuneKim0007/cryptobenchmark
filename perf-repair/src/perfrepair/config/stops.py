"""The one reader of `stops.<code>`: each read when its code fires, through the row's resolver (unset: the default;
bad: one warning, then the default); a fixed code set is one warning, ignored."""
from __future__ import annotations

import logging

from ..inputs.table import STOP_ROWS
from ..stop import policy
from ..stop.codes import Code
from .load import Loaded

LOG = logging.getLogger(__name__)
ALIASES: dict = {}


class StopReader:

    def __init__(self, loaded: Loaded):
        self.loaded, self.warned = loaded, set()

    def __call__(self, code: Code) -> str | None:
        if code.fixed:
            self._fixed(code)
            return None
        row = STOP_ROWS[code.code]
        value = self.loaded.read(row)
        alias = ALIASES.get(code.code)
        # the stops key wins; the older key is read only when the stops key is unset
        if alias is not None and self.loaded.sources.get(row.key) == "default":
            return self.loaded.read(alias)
        return value

    def _fixed(self, code: Code) -> None:
        key = f"stops.{code.code}"
        value = self.loaded.settings.get(key)
        if value is None or key in self.warned:
            return
        self.warned.add(key)
        LOG.warning(f"stop_fixed: {key} {value}, {code.code} is fixed ({code.why}); ignored (file {self.loaded.file})",
                    extra={"code": "stop_fixed", "input": key, "source": f"file {self.loaded.file}"})


def install_stops(loaded: Loaded) -> None:
    policy.install(StopReader(loaded))
