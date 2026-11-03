"""After a device run: one energy_invalid per energy case its energy.json files mark invalid, its reasons as the detail."""
from __future__ import annotations

from pathlib import Path

import yaml

from ..data_handler.inbound.energy import InvalidCase, invalid_cases
from ..stop import terminate


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
        terminate("energy_unreadable", f"{type(e).__name__}: {e}", stage="device", step="energy", item=str(manifest), app=app)
        return 0
    for case, rows in cases.items():
        reasons = list(dict.fromkeys(r for c in rows for r in c.reasons))
        terminate("energy_invalid", ", ".join(reasons) or "no reason given", stage="device", step="energy", item=case,
                  app=app, ref=str(rows[0].file), data={"reasons": reasons, "processes": len(rows)})
    return len(cases)
