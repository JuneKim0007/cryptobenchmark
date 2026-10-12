"""groups.json + rows + measurements → per-group evidence: every configuration the group's members were
measured in, each member's numbers, and every ordered pair's ratios.

A member is a fully qualified primitive (type|name|provider); a measured row belongs to it by (type,
algorithm, provider). Only rows that did the same work compare, so a group is split by operation, key
size, input size and phase.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import permutations

from ..dto import Configuration, GroupEvidence, MemberStats, PairMetrics, PrimitiveRow

WORK_FIELDS = ("operation", "keySize", "inputSize", "phase")


def _pair(a: MemberStats, b: MemberStats) -> PairMetrics:
    ta, tb = a.timeNs, b.timeNs
    alloc = (b.allocations / a.allocations
             if a.allocations not in (None, 0) and b.allocations is not None else None)
    return PairMetrics(a.itemId, b.itemId, tb.median / ta.median,
                       ta.p25 <= tb.p75 and tb.p25 <= ta.p75, alloc)


def build_evidence(groups: dict, rows: list[PrimitiveRow], measurements: dict[str, dict]) -> list[GroupEvidence]:
    member_of = {groups["items"][str(m)]["qualified"]: g["id"] for g in groups["groups"] for m in g["members"]}
    configs: dict[str, dict[tuple, list[MemberStats]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        qualified = f"{r.type}|{r.algorithm}|{r.provider}"
        if qualified not in member_of:
            continue
        m = measurements.get(r.rowId) or {}
        alloc = m.get("allocations")
        configs[member_of[qualified]][tuple(getattr(r, f) for f in WORK_FIELDS)].append(MemberStats(
            r.rowId, qualified, r.provider, r.algorithm, m.get("timeNs"), alloc.median if alloc else None))

    out = []
    for g in sorted(groups["groups"], key=lambda g: g["id"]):
        cs = []
        for key, members in sorted(configs[g["id"]].items(), key=lambda kv: str(kv[0])):
            members = sorted(members, key=lambda s: s.itemId)
            measured = [s for s in members if s.timeNs is not None]
            pairs = tuple(_pair(a, b) for a, b in permutations(measured, 2) if a.itemId != b.itemId)
            cs.append(Configuration(*key, tuple(members), pairs))
        engine = groups["items"][str(g["members"][0])]["qualified"].split("|")[0]
        out.append(GroupEvidence(g["id"], g["description"], engine, g["family"], tuple(cs)))
    return out
