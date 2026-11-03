"""After a device run: one finding per energy case its energy.json marks invalid, keyed by the first reason."""
from __future__ import annotations

from pathlib import Path

from ..data_handler.inbound.energy import invalid_cases
from ..dto.event import FINDING
from ..log import emit

ENERGY_INVALID = "energy_invalid"


def report_invalid(manifest: Path, app: str | None = None) -> int:
    found = invalid_cases(manifest)
    for c in found:
        emit("device", "energy", FINDING, item=c.case, app=app, outcome=c.reasons[0] if c.reasons else ENERGY_INVALID,
             ref=str(c.file), detail=f"{ENERGY_INVALID}: {', '.join(c.reasons) or 'no reason given'}",
             data={"reasons": list(c.reasons)})
    return len(found)
