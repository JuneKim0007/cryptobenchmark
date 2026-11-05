"""A dossiers document grouped by unit: a unit is asked when a member has options, and a member without stays on what
it uses; a member whose current item's key contract is provider-held keeps every member: that key cannot move to another
provider. A `keystore` key source alone is a declared risk, as for a unit of one."""
from __future__ import annotations

from itertools import product

from ..dto.grouping import KEY_PROVIDER_HELD, qualified
from ..dto.interop import pair_status
from ..dto.dossier import PROVIDER_HELD_KEY
from ..dto.site import Scope
from ..dto.unit import INVERSE, PairInterop, Stay, Unit, unit_entry, units_by_scope

def current_item(s: Scope) -> str | None:
    return qualified(s.engineType, s.algorithm, s.provider) if s.algorithm and s.provider else None


def key_contracts(groups: dict) -> dict[str, str | None]:
    return {v["qualified"]: v.get("keyContract") for v in groups["items"].values()}


def provider_held(s: Scope, contracts: dict[str, str | None]) -> bool:
    return contracts.get(current_item(s)) == KEY_PROVIDER_HELD


def _ends(member: str, dossiers: dict[str, dict], scopes: dict[str, Scope]) -> list[str | None]:
    """The items a member ends on in a replace: one of its options, or its current when it stays."""
    d = dossiers.get(member)
    return [o["item"] for o in d["options"]] if d else [current_item(scopes[member])]


def pairs(u: Unit, dossiers: dict[str, dict], scopes: dict[str, Scope], groups: dict) -> tuple[PairInterop, ...]:
    """Every two differing items an inverse link's sides can end on in a replace, with their interop status."""
    found = {}
    for link in (k for k in u.links if k.kind == INVERSE and (k.a in dossiers or k.b in dossiers)):
        a, b = _ends(link.a, dossiers, scopes), _ends(link.b, dossiers, scopes)
        for x, y in product(a, b):
            if x != y and None not in (x, y):
                key = tuple(sorted((x, y)))
                found[key] = PairInterop(*key, pair_status(groups, *key))
    return tuple(found[k] for k in sorted(found))


def asked(doc: dict, units: list[Unit], scopes: list[Scope], groups: dict) -> tuple[list[dict], list[str]]:
    """The asked units' entries, and the members with options a provider-held key keeps."""
    dossiers = {d["scope"]["id"]: d for d in doc["dossiers"]}
    reasons = {n["scope"]: n["reason"] for n in doc["noOptions"]}
    by_id, contracts = {s.id: s for s in scopes}, key_contracts(groups)
    entries, held = [], []
    for u in units:
        decided = [m for m in u.members if m in dossiers]
        if decided and _held(u, by_id, contracts):
            held += decided
        elif decided:
            entries.append(_entry(u, dossiers, reasons, by_id, groups))
    return entries, held


def _held(u: Unit, by_id: dict[str, Scope], contracts: dict[str, str | None]) -> bool:
    return any(provider_held(by_id[m], contracts) for m in u.members)


def _entry(u: Unit, dossiers: dict[str, dict], reasons: dict[str, str], by_id: dict[str, Scope], groups: dict) -> dict:
    stays = tuple(Stay(m, current_item(by_id[m]), reasons[m]) for m in u.members if m not in dossiers)
    return unit_entry(u, stays, pairs(u, dossiers, by_id, groups))


def _with_unit(row: dict, of_scope: dict[str, Unit], contracts: dict[str, str | None]) -> dict:
    """A broken use's unit: its other members must follow an output or key it changes, and a provider-held key cannot move."""
    sid, unit = row["scope"]["id"], of_scope.get(row["scope"]["id"])
    return {**row, "linked": [m for m in unit.members if m != sid] if unit else [],
            "providerHeld": contracts.get(row["current"]) == KEY_PROVIDER_HELD}


def by_unit(doc: dict, units: list[Unit], scopes: list[Scope], groups: dict) -> dict:
    entries, held = asked(doc, units, scopes, groups)
    of_scope, contracts = units_by_scope(units), key_contracts(groups)
    return {**doc, "dossiers": [d for d in doc["dossiers"] if d["scope"]["id"] not in held],
            "noOptions": doc["noOptions"] + [{"scope": s, "reason": PROVIDER_HELD_KEY} for s in sorted(held)],
            "units": entries, "upgrades": [_with_unit(r, of_scope, contracts) for r in doc["upgrades"]]}
