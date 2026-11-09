from __future__ import annotations

from itertools import combinations

import yaml

from .. import run_dir as rd
from cryptobench.catalogue.names import same_engine
from cryptobench.catalogue.grouping import KEY_APP_HELD, KEY_PROVIDER_HELD, Profile, read_profiles
from ..dto.interop import NOT_CHECKABLE, PairResult, PlannedPair, plan_document
from ..dto.screen import Verdict
from ..files import read_json, write_text
from ..validation import require
from ..validation.grouping.interop import validate_plan
from ..run_dir import GroupingPaths
from ..validation.grouping.output import read_groups
from .report.rules import common_key_sizes


ACROSS_KEY_CONTRACTS = "one key is application-held, the other inside the provider: a key cannot cross"


def _across(groups: dict, a: int, b: int) -> bool:
    return {groups["items"][str(m)]["keyContract"] for m in (a, b)} == {KEY_APP_HELD, KEY_PROVIDER_HELD}


def _swappable(g: dict, groups: dict, screen: dict[int, Verdict]) -> bool:
    """False when all members are one engine: no pair of the group is ever an option or an inverse link's end."""
    named = [(groups["items"][str(m)]["qualified"], screen[m].canonical if m in screen else None) for m in g["runnable"]]
    return any(not same_engine(a, b, ca, cb) for (a, ca), (b, cb) in combinations(named, 2))


def _candidates(groups: dict, screen: dict[int, Verdict], sites: frozenset[str] | None) -> list[tuple[dict, int, int]]:
    """Every two runnable members of a swappable group once; with sites, only pairs with a member an app site resolves to."""
    name = lambda m: groups["items"][str(m)]["qualified"]
    return [(g, a, b) for g in sorted(groups["groups"], key=lambda g: g["id"]) if _swappable(g, groups, screen)
            for a, b in combinations(sorted(g["runnable"]), 2) if sites is None or {name(a), name(b)} & sites]


def _key_size(a: int, b: int, profiles: dict[int, Profile], screen: dict[int, Verdict]) -> int | None:
    """The size a member's name fixes, else the two's smallest common prepared size: an unmeasured member prepares none."""
    fixed = [screen[m].keySize for m in (a, b) if m in screen and screen[m].keySize]
    sizes = common_key_sizes([a, b], profiles)
    return fixed[0] if fixed else min(sizes) if sizes else None


def plan(groups: dict, profiles: dict[int, Profile], screen: dict[int, Verdict],
         sites: frozenset[str] | None = None) -> list[PlannedPair]:
    """The candidates within one key contract, each at its own key size; the oracle checks both directions of each."""
    pairs = []
    for g, a, b in _candidates(groups, screen, sites):
        if not _across(groups, a, b):
            pairs.append(PlannedPair(len(pairs) + 1, g["id"], groups["items"][str(a)]["qualified"],
                                     groups["items"][str(b)]["qualified"], _key_size(a, b, profiles, screen)))
    return pairs


def across_key_contracts(groups: dict, first_id: int, screen: dict[int, Verdict],
                         sites: frozenset[str] | None = None) -> tuple[PairResult, ...]:
    """The candidates across key contracts, numbered after the planned pairs."""
    found = [(g["id"], a, b) for g, a, b in _candidates(groups, screen, sites) if _across(groups, a, b)]
    return tuple(PairResult(first_id + n, gid, groups["items"][str(a)]["qualified"], groups["items"][str(b)]["qualified"],
                            NOT_CHECKABLE, ACROSS_KEY_CONTRACTS) for n, (gid, a, b) in enumerate(found))


def plan_for(paths: GroupingPaths, sites: frozenset[str] | None = None) -> dict:
    groups, screen = read_groups(paths), rd.load_screen(paths) or {}
    pairs = plan(groups, read_profiles(read_json(paths.profiles)), screen, sites)
    return plan_document(pairs, across_key_contracts(groups, len(pairs) + 1, screen, sites))


def write_plan(paths: GroupingPaths, sites: frozenset[str] | None = None) -> list[PlannedPair]:
    document = plan_for(paths, sites)
    require("grouping/interop_plan.yaml", validate_plan(document, read_groups(paths)))
    write_text(paths.interop_plan, yaml.safe_dump(document, sort_keys=False))
    return [PlannedPair.from_json(p) for p in document["pairs"]]
