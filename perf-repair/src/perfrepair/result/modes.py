"""The verdict rule over a perfMode's selected metrics, loaded from criteria.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto import MetricComparison, PairMetrics
from ..dto.perf_mode import PerfMode
from ..files import read_yaml

CRITERIA = Path(__file__).with_name("criteria.yaml")


@cache
def criteria() -> dict:
    return read_yaml(CRITERIA)


def worse_ratio(improving: float) -> float:
    return 1 / improving


@dataclass(frozen=True)
class Mode:
    perf: PerfMode
    rule: str
    improvingRatio: float

    @property
    def name(self) -> str:
        return self.perf.name

    @property
    def worseningRatio(self) -> float:
        return worse_ratio(self.improvingRatio)

    def _given(self, pair: PairMetrics) -> list[MetricComparison]:
        by = {c.metric: c for c in pair.metrics}
        return [by[m.name] for m in self.perf.metrics if m.name in by and by[m.name].ratio is not None]

    def missing(self, pair: PairMetrics) -> tuple[str, ...]:
        """The required metrics this pair has no ratio for; generic requires none."""
        given = {c.metric for c in self._given(pair)}
        return tuple(m.name for m in self.perf.required if m.name not in given)

    def judge(self, pair: PairMetrics) -> str:
        given = self._given(pair)
        if self.missing(pair) or not given:
            return "not_measured"
        if any(c.ratio >= self.worseningRatio for c in given):
            return "not_improving"
        return "improves" if any(c.ratio <= self.improvingRatio for c in given) else "not_improving"

    def improves(self, pair: PairMetrics) -> bool:
        return self.judge(pair) == "improves"

    def deciding(self, pair: PairMetrics) -> MetricComparison | None:
        """The improving selected metric with the most confidence; it grades the pair."""
        hits = [c for c in self._given(pair) if c.ratio <= self.improvingRatio]
        return max(hits, key=lambda c: -1.0 if c.pImprove is None else c.pImprove, default=None)


def mode_of(perf: PerfMode) -> Mode:
    return Mode(perf, criteria()["rule"], float(criteria()["improvingRatio"]))
