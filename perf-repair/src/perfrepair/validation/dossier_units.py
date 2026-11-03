"""dossiers.json against units.json: every unit with a member that has options is asked, with the members that stay
and the inverse pairs' interop; a provider-held key on any member keeps every member as `provider_held_key`."""
from __future__ import annotations

from ..dto.site import PROVIDER_HELD_KEY, Scope
from ..dto.unit import Unit
from ..result.unit_dossiers import asked, key_contracts, provider_held


def _held(u: Unit, with_options: set[str], reasons: dict[str, str], by_id: dict[str, Scope], contracts: dict) -> list[str]:
    if any(m in by_id and provider_held(by_id[m], contracts) for m in u.members):
        return [f"unit {u.id}: {m} has a dossier although a member's key is provider-held" for m in u.members
                if m in with_options]
    return [f"unit {u.id}: {m} is {PROVIDER_HELD_KEY} but no member's key is provider-held" for m in u.members
            if reasons.get(m) == PROVIDER_HELD_KEY]


def validate_dossier_units(doc: dict, units: list[Unit], scopes: list[Scope], groups: dict) -> list[str]:
    with_options = {d["scope"]["id"] for d in doc.get("dossiers") or []}
    reasons = {n["scope"]: n["reason"] for n in doc.get("noOptions") or []}
    by_id, contracts = {s.id: s for s in scopes}, key_contracts(groups)
    problems = [p for u in units for p in _held(u, with_options, reasons, by_id, contracts)]
    if problems:
        return problems
    if doc.get("units") != asked(doc, units, scopes, groups)[0]:
        problems.append("units are not the units.json units with a member that has a dossier, their stays and pairs")
    return problems
