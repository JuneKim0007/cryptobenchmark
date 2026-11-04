"""--outcome: what the caller of a guide run needs afterwards, the device folder, the run's id, its exit and code."""
from __future__ import annotations

from pathlib import Path

from ..failure import Failed
from ..files import write_json
from .state import Guide


def write_outcome(path: Path, guide: Guide | None, code: int, failure: Failed | None) -> None:
    write_json(path, {"device": str(guide.device) if guide and guide.device else None,
                      "run": guide.record.id if guide and guide.record else None,
                      "exit": code,
                      "code": (guide.stop_code if guide else None) or (failure.code if failure else None)})
