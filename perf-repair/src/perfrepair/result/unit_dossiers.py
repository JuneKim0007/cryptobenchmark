"""A dossiers document grouped by unit: a unit is asked when every member has options; otherwise each member with
options becomes a static keep, so a unit is never decided in part."""
from __future__ import annotations

from ..dto.site import UNIT_MEMBER_WITHOUT_OPTION
from ..dto.unit import Unit


def by_unit(doc: dict, units: list[Unit]) -> dict:
    with_options = {d["scope"]["id"] for d in doc["dossiers"]}
    asked = [u for u in units if set(u.members) <= with_options]
    kept = with_options - {m for u in asked for m in u.members}
    return {**doc, "dossiers": [d for d in doc["dossiers"] if d["scope"]["id"] not in kept],
            "noOptions": doc["noOptions"] + [{"scope": s, "reason": UNIT_MEMBER_WITHOUT_OPTION} for s in sorted(kept)],
            "units": [u.to_json() for u in asked]}
