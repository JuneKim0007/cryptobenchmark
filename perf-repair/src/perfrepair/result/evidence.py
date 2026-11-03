from __future__ import annotations

from collections import defaultdict
from itertools import permutations

from ..dto import Configuration, GroupEvidence, MemberStats, MetricComparison, PairMetrics, PrimitiveRow, Summary
from ..dto.grouping import parse_qualified, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.metrics import METRICS, Metric
from ..dto.perf_mode import PerfMode
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


def _pair(a: MemberStats, b: MemberStats, interop: str, perf: PerfMode) -> PairMetrics:
    both = tuple(_compare(m, a.metrics[m.name], b.metrics[m.name]) for m in perf.metrics
                 if m.name in a.metrics and m.name in b.metrics)
    return PairMetrics(a.itemId, b.itemId, interop, both)


def _kept(a: str, b: str, failed: set, verdicts: dict[str, Verdict]) -> bool:
    return a != b and frozenset((a, b)) not in failed and not lowers_status(verdicts.get(a), verdicts.get(b))


def _measured(s: MemberStats) -> bool:
    return all(m.name in s.metrics for m in METRICS if m.required)


def _selected(s: MemberStats, perf: PerfMode) -> MemberStats:
    return MemberStats(s.rowId, s.itemId, s.provider, s.algorithm, {k: v for k, v in s.metrics.items() if k in perf.names})


def _configurations(groups: dict, rows: list[PrimitiveRow], measurements: dict[str, dict]
                    ) -> dict[str, dict[tuple, list[MemberStats]]]:
    member_of = {groups["items"][str(m)]["qualified"]: g["id"] for g in groups["groups"] for m in g["members"]}
    configs: dict[str, dict[tuple, list[MemberStats]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        name = qualified(r.type, r.algorithm, r.provider)
        if name in member_of:
            configs[member_of[name]][tuple(getattr(r, f) for f in WORK_FIELDS)].append(MemberStats(
                r.rowId, name, r.provider, r.algorithm, dict(measurements.get(r.rowId) or {})))
    return configs


def build_evidence(groups: dict, rows: list[PrimitiveRow], measurements: dict[str, dict],
                   verdicts: dict[str, Verdict] | None, perf: PerfMode) -> list[GroupEvidence]:
    """verdicts: the run-level screen verdicts by qualified name; a pair whose target lowers the status is left out.
    Only perf's metrics reach the evidence, so a decision never sees another."""
    v = verdicts or {}
    configs = _configurations(groups, rows, measurements)
    out, failed = [], failed_pairs(groups)
    for g in sorted(groups["groups"], key=lambda g: g["id"]):
        cs = []
        for key, members in sorted(configs[g["id"]].items(), key=lambda kv: str(kv[0])):
            members = sorted(members, key=lambda s: s.itemId)
            measured = [_selected(s, perf) for s in members if _measured(s)]
            pairs = tuple(_pair(a, b, pair_status(groups, a.itemId, b.itemId), perf) for a, b in permutations(measured, 2)
                          if _kept(a.itemId, b.itemId, failed, v))
            cs.append(Configuration(*key, tuple(_selected(s, perf) for s in members), pairs))
        engine = parse_qualified(groups["items"][str(g["members"][0])]["qualified"])[0]
        out.append(GroupEvidence(g["id"], g["description"], engine, g["family"], tuple(cs)))
    return out
