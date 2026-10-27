"""Improvement criteria per mode, loaded from criteria.yaml; a mode differs only in its entry there."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..dto import PairMetrics
from ..files import read_yaml

CRITERIA = Path(__file__).with_name("criteria.yaml")
JUDGEMENTS = ("improves", "not_improving", "not_measured")


@dataclass(frozen=True)
class Mode:
    name: str
    proxy: bool
    rule: str
    allocationsMustNotRise: bool
    improvingRatio: float

    def judge(self, pair: PairMetrics) -> str:
        if pair.timeRatio > self.improvingRatio:
            return "not_improving"
        if not self.allocationsMustNotRise:
            return "improves"
        # GC runs outside the timed region yet still costs energy, so allocations are a criterion here
        if pair.allocationRatio is None:
            return "not_measured"
        return "improves" if pair.allocationRatio <= 1 else "not_improving"

    def improves(self, pair: PairMetrics) -> bool:
        return self.judge(pair) == "improves"


def load_modes(path: Path = CRITERIA) -> dict[str, Mode]:
    doc = read_yaml(path)
    ratio = float(doc["improvingRatio"])
    return {m["name"]: Mode(m["name"], bool(m["proxy"]), m["rule"], bool(m["allocationsMustNotRise"]), ratio)
            for m in doc["modes"]}


MODES = load_modes()
