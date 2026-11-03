from __future__ import annotations

import hashlib
import json

from ..dto.grouping import Item
from ..dto.grouping_state import CODE_PREFIX, Group
from ..dto.screen import CODE_GROUPED, Verdict


def screened_out(verdict: Verdict | None) -> bool:
    return verdict is not None and verdict.status in CODE_GROUPED


def _key(item: Item, verdict: Verdict) -> tuple:
    return item.family, verdict.status, verdict.canonical, verdict.providerHeld


def code_group_id(item: Item, verdict: Verdict) -> str:
    return CODE_PREFIX + hashlib.sha256(json.dumps(_key(item, verdict)).encode()).hexdigest()[:10]


def describe(verdict: Verdict) -> str:
    keys = "keys inside the provider" if verdict.providerHeld else "keys the application holds"
    return (f"Code-made group of one algorithm, no model decided it: {verdict.canonical} (any key size), {keys}, "
            f"screened {verdict.status}; its members are that algorithm from each provider.")


def code_groups(items: list[Item], verdicts: dict[int, Verdict] | None) -> dict[str, Group]:
    groups: dict[str, Group] = {}
    for i in items:
        v = (verdicts or {}).get(i.id)
        if screened_out(v):
            groups.setdefault(code_group_id(i, v), Group(i.family, describe(v))).members.append(i.id)
    return groups
