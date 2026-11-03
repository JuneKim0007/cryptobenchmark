"""After a device run: one finding per energy case its energy.json files mark invalid, keyed by the first reason."""
from __future__ import annotations

from pathlib import Path

import yaml

from ..data_handler.inbound.energy import InvalidCase, invalid_cases
from ..dto.event import FINDING
from ..log import emit

ENERGY_INVALID, ENERGY_UNREADABLE = "energy_invalid", "energy_unreadable"


def _per_case(found: list[InvalidCase]) -> dict[str, list[InvalidCase]]:
    cases: dict[str, list[InvalidCase]] = {}
    for c in found:
        cases.setdefault(c.case, []).append(c)
    return cases


def report_invalid(manifest: Path, app: str | None = None) -> int:
    # the measured run is already paid for: a report that cannot read its energy says so and never fails it
    try:
        cases = _per_case(invalid_cases(manifest))
    except (OSError, ValueError, AttributeError, yaml.YAMLError) as e:
        emit("device", "energy", FINDING, item=str(manifest), app=app, outcome=ENERGY_UNREADABLE, detail=f"{type(e).__name__}: {e}")
        return 0
    for case, rows in cases.items():
        reasons = list(dict.fromkeys(r for c in rows for r in c.reasons))
        emit("device", "energy", FINDING, item=case, app=app, outcome=reasons[0] if reasons else ENERGY_INVALID,
             ref=str(rows[0].file), detail=f"{ENERGY_INVALID}: {', '.join(reasons) or 'no reason given'}",
             data={"reasons": reasons, "processes": len(rows)})
    return len(cases)
