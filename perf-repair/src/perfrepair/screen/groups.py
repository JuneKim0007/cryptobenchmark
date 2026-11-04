from __future__ import annotations

import hashlib
import json

from ..dto.grouping import Item, Profile
from ..dto.grouping_state import CODE_PREFIX, Group
from ..dto.screen import CODE_GROUPED, Verdict
from ..dto.signature import KEY_MATERIAL, UNKNOWN, Signature


def screened_out(verdict: Verdict | None) -> bool:
    return verdict is not None and verdict.status in CODE_GROUPED


def decided_signature(profile: Profile | None) -> Signature | None:
    signature = profile.signature if profile else None
    return signature if signature is not None and signature.decided else None


def grouped_by_code(item: int, verdicts: dict[int, Verdict] | None, profiles: dict[int, Profile]) -> bool:
    """Never without screen.json: runs built before screening ask every item."""
    verdict, profile = (verdicts or {}).get(item), profiles.get(item)
    return verdict is not None and (screened_out(verdict) or decided_signature(profile) is not None
                                    or bool(profile and profile.isolated))


def _key(item: Item, verdict: Verdict, profile: Profile | None) -> tuple:
    key = (item.family, verdict.status, verdict.canonical, verdict.providerHeld)
    signature = profile.signature if profile else None
    # only an item with key material adds it, so no other screened-out group changes its id
    if signature is None or KEY_MATERIAL not in signature.names():
        return key
    return (*key, signature.known().get(KEY_MATERIAL))


def code_group_id(item: Item, verdict: Verdict, profile: Profile | None = None) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps(_key(item, verdict, profile)).encode()).hexdigest()[:10]


def signature_group_id(item: Item, signature: Signature) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps((item.family, "signature", signature.identity)).encode()).hexdigest()[:10]


def describe_signature(signature: Signature) -> str:
    shown = ", ".join(f"{c.name}={c.value}" for c in signature.components if c.status != UNKNOWN)
    assumed = f"; assumed by convention: {', '.join(signature.assumed)}" if signature.assumed else ""
    return (f"Code-made group by signature, no model decided it: {shown}{assumed}; "
            "its members are that function from each provider, at any key size.")


def isolated_group_id(item: Item) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps((item.family, "isolated", item.qualified)).encode()).hexdigest()[:10]


ISOLATED = ("Code-made group of one, no model decided it: a generator whose trial does not show whether its key leaves "
            "the provider, so it joins no group and is offered as no swap.")


def describe(verdict: Verdict) -> str:
    keys = "keys inside the provider" if verdict.providerHeld else "keys the application holds"
    return (f"Code-made group of one algorithm, no model decided it: {verdict.canonical} (any key size), {keys}, "
            f"screened {verdict.status}; its members are that algorithm from each provider.")


def code_groups(items: list[Item], verdicts: dict[int, Verdict] | None, profiles: dict[int, Profile]) -> dict[str, Group]:
    groups: dict[str, Group] = {}
    for i in items:
        v, signature = (verdicts or {}).get(i.id), decided_signature(profiles.get(i.id))
        if v is not None and profiles.get(i.id) is not None and profiles[i.id].isolated:
            groups[isolated_group_id(i)] = Group(i.family, ISOLATED, [i.id])
        elif screened_out(v):
            groups.setdefault(code_group_id(i, v, profiles.get(i.id)), Group(i.family, describe(v))).members.append(i.id)
        elif v is not None and signature is not None:
            groups.setdefault(signature_group_id(i, signature), Group(i.family, describe_signature(signature))).members.append(i.id)
    return groups
