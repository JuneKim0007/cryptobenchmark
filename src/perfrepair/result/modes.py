"""Improvement criteria. A mode fixes which measured metric decides whether a replacement improves.

No energy is measured (the benchmark records time and allocations), so battery mode is a proxy:
CPU time stands in for energy, and a replacement that allocates more per operation never counts
as an improvement, because collection work happens outside the timed region and still drains.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..dto import PairMetrics


@dataclass(frozen=True)
class Mode:
    name: str
    proxy: bool
    rule: str

    def improves(self, pair: PairMetrics) -> bool:
        if pair.timeRatio >= 1:
            return False
        if self.name == "battery":
            return pair.allocationRatio is not None and pair.allocationRatio <= 1
        return True


MODES = {
    "latency": Mode("latency", False,
                    "improves when time per operation is lower; allocations are context"),
    "battery": Mode("battery", True,
                    "proxy (no energy measured): improves when time per operation is lower and "
                    "allocations per operation are not higher"),
}
