"""dossiers.json against units.json: the asked units are those whose members all have options; a member of any other
unit is in noOptions, under `unit_member_without_option` unless it lacks options of its own."""
from __future__ import annotations

from ..dto.site import UNIT_MEMBER_WITHOUT_OPTION
from ..dto.unit import Unit


def _unit(u: Unit, with_options: set[str], reasons: dict[str, str]) -> list[str]:
    own = [m for m in u.members if m in reasons and reasons[m] != UNIT_MEMBER_WITHOUT_OPTION]
    if own:
        return [f"unit {u.id}: {m} has a dossier although {own[0]} has no option" for m in u.members if m in with_options]
    return [f"unit {u.id}: {m} is {UNIT_MEMBER_WITHOUT_OPTION} but every member has options" for m in u.members
            if reasons.get(m) == UNIT_MEMBER_WITHOUT_OPTION]


def validate_dossier_units(doc: dict, units: list[Unit]) -> list[str]:
    with_options = {d["scope"]["id"] for d in doc.get("dossiers") or []}
    reasons = {n["scope"]: n["reason"] for n in doc.get("noOptions") or []}
    problems = [p for u in units for p in _unit(u, with_options, reasons)]
    want = [u.to_json() for u in units if set(u.members) <= with_options]
    if doc.get("units") != want:
        problems.append("units are not the units.json units whose members all have dossiers")
    return problems
