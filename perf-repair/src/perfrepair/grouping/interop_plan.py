from __future__ import annotations

from itertools import combinations

import yaml

from ..dto.interop import PlannedPair, plan_document
from ..files import write_text
from ..validation import require
from ..validation.grouping.interop import validate_plan
from .paths import GroupingPaths
from .report.checks import read_groups


def plan(groups: dict) -> list[PlannedPair]:
    """Every two runnable members of a group, once; the oracle checks both directions of each."""
    pairs = []
    for g in sorted(groups["groups"], key=lambda g: g["id"]):
        key_size = min(g["keySizes"]) if g["keySizes"] else None
        for a, b in combinations(sorted(g["runnable"]), 2):
            pairs.append(PlannedPair(len(pairs) + 1, g["id"], groups["items"][str(a)]["qualified"],
                                     groups["items"][str(b)]["qualified"], key_size))
    return pairs


def write_plan(paths: GroupingPaths) -> list[PlannedPair]:
    groups = read_groups(paths)
    pairs = plan(groups)
    document = plan_document(pairs)
    require("grouping/interop_plan.yaml", validate_plan(document, groups))
    write_text(paths.interop_plan, yaml.safe_dump(document, sort_keys=False))
    return pairs
