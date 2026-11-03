"""What the worthiness decision sees for one group: mode, run warnings, aliased members, per-configuration tables."""
from __future__ import annotations

from ....dto import Configuration, GroupEvidence, MetricComparison, PairMetrics, Summary
from ....dto.metrics import METRICS, Metric
from ....result.confidence import describe
from ....result.modes import Mode
from ....validation.evaluate.worthiness import aliases


def _num(x: float | None, fmt: str = "{:.0f}") -> str:
    return "-" if x is None else fmt.format(x)


def _median(x: float) -> str:
    return f"{x:.4g}"


def _stats(metric: Metric, s: Summary | None) -> str:
    if s is None:
        return "not measured | | | | |" + (" |" if metric.kinds else "")
    cells = [_median(s.median), f"{_median(s.low)}..{_median(s.high)}" if s.low is not None else "-",
             _median(s.p25), _median(s.p75), _num(s.cv, "{:.3f}"), str(s.n)]
    return " | ".join(cells + ([s.kind] if metric.kinds else []))


def _ratio(c: MetricComparison | None) -> str:
    if c is None:
        return "- | - | -"
    if c.reason:
        return f"{c.reason} | - | -"
    return f"{_num(c.ratio, '{:.3f}')} | {describe(c.pImprove)} | {c.n}"


def _heads(shown: list[Metric]) -> tuple[str, str]:
    members = " | ".join(f"{m.name} median {m.unit} | 95% interval (bootstrap) | p25 | p75 | cv | n"
                         + (" | kind" if m.kinds else "") for m in shown)
    pairs = " | ".join(f"{m.name} ratio | pImprove (confidence) | n" for m in shown)
    return f"  member | {members}", f"  pair from -> to | {pairs} | interop | improves"


def _pair(p: PairMetrics, shown: list[Metric], short: dict[str, str], mode: Mode) -> str:
    by = {x.metric: x for x in p.metrics}
    cells = " | ".join(_ratio(by.get(m.name)) for m in shown)
    return f"  {short[p.fromItem]} -> {short[p.toItem]} | {cells} | {p.interop} | {mode.improves(p)}"


def _configuration(c: Configuration, short: dict[str, str], mode: Mode) -> list[str]:
    shown = [m for m in METRICS if any(m.name in s.metrics for s in c.members)]
    member_head, pair_head = _heads(shown)
    lines = ["", f"CONFIGURATION {c.operation} key {c.keySize} input {c.inputSize} {c.phase}", member_head]
    lines += [f"  {short[s.itemId]} | " + " | ".join(_stats(m, s.metrics.get(m.name)) for m in shown) for s in c.members]
    return lines + [pair_head] + [_pair(p, shown, short, mode) for p in c.pairs]


def render(e: GroupEvidence, mode: Mode, comparability: list[str]) -> str:
    lines = [f"MODE: {mode.name} — {mode.rule}", "RUN WARNINGS:"]
    lines += [f"  - {w}" for w in comparability] or ["  (none)"]
    lines += ["", f"GROUP {e.groupId} | {e.label} | {e.type} | family {e.family}"]
    alias = aliases(e)
    short = {m: a for a, m in alias.items()}
    lines += ["", "MEMBERS (answer with these names)"] + [f"  {a} = {m}" for a, m in alias.items()]
    for c in e.configurations:
        if c.pairs:
            lines += _configuration(c, short, mode)
    return "\n".join(lines)
