"""What the worthiness decision sees for one group: mode, run warnings, aliased members, per-configuration tables;
time in the display units, latency and, when selected, throughput as one metric."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ....dto import Configuration, GroupEvidence, MetricComparison, PairMetrics, Summary
from ....dto.metrics import METRICS, Metric
from ....dto.report import THROUGHPUT, has_views
from ....dto.units import DisplayUnits, number
from ....result.confidence import describe
from ....result.modes import Mode
from ....validation.evaluate.worthiness import aliases


def _num(x: float | None, fmt: str = "{:.0f}") -> str:
    return "-" if x is None else fmt.format(x)


@dataclass(frozen=True)
class Shown:
    """How one configuration shows a metric: its unit, a value converter, and the throughput column when selected."""
    metric: Metric
    unit: str
    value: Callable[[float], float]
    throughput: Callable[[float], float | None] | None = None


def _shown(metric: Metric, mode: Mode, units: DisplayUnits, input_size: int | None) -> Shown:
    if not has_views(metric):
        return Shown(metric, metric.unit, lambda x: x)
    def rate(ns: float) -> float | None:
        return units.throughput_of(ns, input_size)

    shows_rate = THROUGHPUT in mode.perf.views(metric) and rate(1.0) is not None
    return Shown(metric, units.latency_label, units.latency_of, rate if shows_rate else None)


def _stats(shown: Shown, s: Summary | None) -> str:
    metric, f = shown.metric, shown.value
    if s is None:
        return "not measured | | | | |" + (" |" if metric.kinds else "") + (" |" if shown.throughput else "")
    cells = [number(f(s.median)), f"{number(f(s.low))}..{number(f(s.high))}" if s.low is not None else "-",
             number(f(s.p25)), number(f(s.p75)), _num(s.cv, "{:.3f}"), str(s.n)]
    cells += [number(shown.throughput(s.median))] if shown.throughput else []
    return " | ".join(cells + ([s.kind] if metric.kinds else []))


def _ratio(c: MetricComparison | None) -> str:
    if c is None:
        return "- | - | -"
    if c.reason:
        return f"{c.reason} | - | -"
    return f"{_num(c.ratio, '{:.3f}')} | {describe(c.pImprove)} | {c.n}"


def _heads(shown: list[Shown], units: DisplayUnits) -> tuple[str, str]:
    members = " | ".join(f"{x.metric.name} median {x.unit} | 95% interval (bootstrap) | p25 | p75 | cv | n"
                         + (f" | throughput {units.throughput} (median)" if x.throughput else "")
                         + (" | kind" if x.metric.kinds else "") for x in shown)
    pairs = " | ".join(f"{x.metric.name} ratio | pImprove (confidence) | n" for x in shown)
    return f"  member | {members}", f"  pair from -> to | {pairs} | interop | improves"


def _pair(p: PairMetrics, shown: list[Shown], short: dict[str, str], mode: Mode) -> str:
    by = {x.metric: x for x in p.metrics}
    cells = " | ".join(_ratio(by.get(x.metric.name)) for x in shown)
    return f"  {short[p.fromItem]} -> {short[p.toItem]} | {cells} | {p.interop} | {mode.improves(p)}"


def _configuration(c: Configuration, short: dict[str, str], mode: Mode, units: DisplayUnits) -> list[str]:
    shown = [_shown(m, mode, units, c.inputSize) for m in METRICS if any(m.name in s.metrics for s in c.members)]
    member_head, pair_head = _heads(shown, units)
    lines = ["", f"CONFIGURATION {c.operation} key {c.keySize} input {c.inputSize} {c.phase} {c.variant}", member_head]
    lines += [f"  {short[s.itemId]} | " + " | ".join(_stats(x, s.metrics.get(x.metric.name)) for x in shown) for s in c.members]
    return lines + [pair_head] + [_pair(p, shown, short, mode) for p in c.pairs]


def render(e: GroupEvidence, mode: Mode, comparability: list[str], units: DisplayUnits = DisplayUnits()) -> str:
    lines = [f"MODE: {mode.name} — {mode.rule}", "RUN WARNINGS:"]
    lines += [f"  - {w}" for w in comparability] or ["  (none)"]
    lines += ["", f"GROUP {e.groupId} | {e.label} | {e.type} | family {e.family}"]
    alias = aliases(e)
    short = {m: a for a, m in alias.items()}
    lines += ["", "MEMBERS (answer with these names)"] + [f"  {a} = {m}" for a, m in alias.items()]
    for c in e.configurations:
        if c.pairs:
            lines += _configuration(c, short, mode, units)
    return "\n".join(lines)
