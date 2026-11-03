from __future__ import annotations

from collections import defaultdict
from itertools import permutations

from ..dto import Configuration, GroupEvidence, MemberStats, MetricComparison, PairMetrics, PrimitiveRow, Summary
from ..dto.grouping import parse_qualified, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.metrics import ALLOCATIONS, METRICS, TIME, Metric
from ..dto.screen import Verdict, lowers_status
from ..dto.site import ENERGY_KINDS_DIFFER
from .confidence import level
from .estimate import p_improve

WORK_FIELDS = ("operation", "keySize", "inputSize", "phase")


def _compare(metric: Metric, a: Summary, b: Summary) -> MetricComparison:
    if a.kind != b.kind:
        return MetricComparison(metric.name, None, None, level(None), 0, f"{ENERGY_KINDS_DIFFER}: {a.kind} from, {b.kind} to")
    before, after = (a, b) if metric.lowerIsBetter else (b, a)
    p = p_improve(before.processes, after.processes)
    # a zero median (no allocations) has no ratio; pImprove still compares the runs
    ratio = after.median / before.median if before.median else None
    return MetricComparison(metric.name, ratio, p, level(p), min(a.n, b.n))


def _pair(a: MemberStats, b: MemberStats, interop: str) -> PairMetrics:
    both = tuple(_compare(m, a.metrics[m.name], b.metrics[m.name]) for m in METRICS
                 if m.name in a.metrics and m.name in b.metrics)
    by = {c.metric: c for c in both}
    time, alloc = by[TIME.name], by.get(ALLOCATIONS.name)
    return PairMetrics(a.itemId, b.itemId, time.ratio, time.pImprove, time.level, time.n,
                       alloc.ratio if alloc else None, interop, both)


def _kept(a: str, b: str, failed: set, verdicts: dict[str, Verdict]) -> bool:
    return a != b and frozenset((a, b)) not in failed and not lowers_status(verdicts.get(a), verdicts.get(b))


def build_evidence(groups: dict, rows: list[PrimitiveRow], measurements: dict[str, dict],
                   verdicts: dict[str, Verdict] | None) -> list[GroupEvidence]:
    """verdicts: the run-level screen verdicts by qualified name; a pair whose target lowers the status is left out."""
    v = verdicts or {}
    member_of = {groups["items"][str(m)]["qualified"]: g["id"] for g in groups["groups"] for m in g["members"]}
    configs: dict[str, dict[tuple, list[MemberStats]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        name = qualified(r.type, r.algorithm, r.provider)
        if name not in member_of:
            continue
        configs[member_of[name]][tuple(getattr(r, f) for f in WORK_FIELDS)].append(MemberStats(
            r.rowId, name, r.provider, r.algorithm, dict(measurements.get(r.rowId) or {})))

    out, failed = [], failed_pairs(groups)
    for g in sorted(groups["groups"], key=lambda g: g["id"]):
        cs = []
        for key, members in sorted(configs[g["id"]].items(), key=lambda kv: str(kv[0])):
            members = sorted(members, key=lambda s: s.itemId)
            measured = [s for s in members if all(m.name in s.metrics for m in METRICS if m.required)]
            pairs = tuple(_pair(a, b, pair_status(groups, a.itemId, b.itemId)) for a, b in permutations(measured, 2)
                          if _kept(a.itemId, b.itemId, failed, v))
            cs.append(Configuration(*key, tuple(members), pairs))
        engine = parse_qualified(groups["items"][str(g["members"][0])]["qualified"])[0]
        out.append(GroupEvidence(g["id"], g["description"], engine, g["family"], tuple(cs)))
    return out
