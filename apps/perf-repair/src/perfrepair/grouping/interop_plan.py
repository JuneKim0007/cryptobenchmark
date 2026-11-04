from __future__ import annotations

from itertools import combinations

import yaml

from ..dto.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD
from ..dto.interop import NOT_CHECKABLE, PairResult, PlannedPair, plan_document
from ..files import write_text
from ..validation import require
from ..validation.grouping.interop import validate_plan
from ..run_dir import GroupingPaths
from ..validation.grouping.output import read_groups


ACROSS_KEY_CONTRACTS = "one key is application-held, the other inside the provider: a key cannot cross"


def _across(groups: dict, a: int, b: int) -> bool:
    return {groups["items"][str(m)]["keyContract"] for m in (a, b)} == {KEY_APP_HELD, KEY_PROVIDER_HELD}


def plan(groups: dict) -> list[PlannedPair]:
    """Every two runnable members of a group within one key contract, once; the oracle checks both directions of each."""
    pairs = []
    for g in sorted(groups["groups"], key=lambda g: g["id"]):
        key_size = min(g["keySizes"]) if g["keySizes"] else None
        for a, b in combinations(sorted(g["runnable"]), 2):
            if not _across(groups, a, b):
                pairs.append(PlannedPair(len(pairs) + 1, g["id"], groups["items"][str(a)]["qualified"],
                                         groups["items"][str(b)]["qualified"], key_size))
    return pairs


def across_key_contracts(groups: dict, first_id: int) -> tuple[PairResult, ...]:
    """Every two runnable members of a group across key contracts, numbered after the planned pairs."""
    found = [(g["id"], a, b) for g in sorted(groups["groups"], key=lambda g: g["id"])
             for a, b in combinations(sorted(g["runnable"]), 2) if _across(groups, a, b)]
    return tuple(PairResult(first_id + n, gid, groups["items"][str(a)]["qualified"], groups["items"][str(b)]["qualified"],
                            NOT_CHECKABLE, ACROSS_KEY_CONTRACTS) for n, (gid, a, b) in enumerate(found))


def write_plan(paths: GroupingPaths) -> list[PlannedPair]:
    groups = read_groups(paths)
    pairs = plan(groups)
    document = plan_document(pairs, across_key_contracts(groups, len(pairs) + 1))
    require("grouping/interop_plan.yaml", validate_plan(document, groups))
    write_text(paths.interop_plan, yaml.safe_dump(document, sort_keys=False))
    return pairs
