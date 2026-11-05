from __future__ import annotations

import hashlib
import json

from ..catalog.groups import group_catalog, variant
from ..dto.grouping import KEY_PROVIDER_HELD, Item, Profile
from ..dto.grouping_state import CODE_PREFIX, Group
from ..dto.screen import Verdict
from ..dto.signature import KEY_MATERIAL
from ..probe.identified import listed, screened_out


def _key(item: Item, verdict: Verdict, profile: Profile | None) -> tuple:
    key = (item.family, verdict.status, verdict.canonical, verdict.providerHeld)
    signature = profile.signature if profile else None
    # only an item with key material adds it, so no other screened-out group changes its id
    if signature is None or KEY_MATERIAL not in signature.names():
        return key
    return (*key, signature.known().get(KEY_MATERIAL))


def code_group_id(item: Item, verdict: Verdict, profile: Profile | None = None) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps(_key(item, verdict, profile)).encode()).hexdigest()[:10]


def isolated_group_id(item: Item) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps((item.family, "isolated", item.qualified)).encode()).hexdigest()[:10]


ISOLATED = ("Code-made group of one, no model decided it: a generator whose trial does not show whether its key leaves "
            "the provider, so it joins no group and is offered as no swap.")


def describe(verdict: Verdict) -> str:
    keys = "keys inside the provider" if verdict.providerHeld else "keys the application holds"
    return (f"Code-made group of one algorithm, no model decided it: {verdict.canonical} (any key size), {keys}, "
            f"screened {verdict.status}; its members are that algorithm from each provider.")


def code_groups(items: list[Item], verdicts: dict[int, Verdict] | None, profiles: dict[int, Profile]) -> dict[str, Group]:
    """The groups an item is placed in without a model; a catalog group's id is an answer's to join, one code_ id is not."""
    groups: dict[str, Group] = {}
    for i in items:
        v, profile = (verdicts or {}).get(i.id), profiles.get(i.id)
        found = listed(i, v)
        # an unlisted generator of unknown key contract is asked, and gate C keeps it alone
        if profile is not None and profile.isolated and (screened_out(v) or found is not None):
            groups[isolated_group_id(i)] = Group(i.family, ISOLATED, [i.id])
        elif screened_out(v):
            groups.setdefault(code_group_id(i, v, profile), Group(i.family, describe(v))).members.append(i.id)
        elif found is not None:
            place = variant(found, profile is not None and profile.keyContract == KEY_PROVIDER_HELD)
            groups.setdefault(place.id, Group(place.family, place.description)).members.append(i.id)
    return groups


def reserved_catalog_groups(taken: dict[str, Group]) -> dict[str, Group]:
    """Catalog groups with no member here: not shown, their ids kept so no answer reuses one and a record may still name one."""
    return {v.id: Group(v.family, v.description) for v in group_catalog().variants() if v.id not in taken}
