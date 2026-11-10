"""Display units: the benchmark's analysis.units, read by its charts and, from manifest.yaml, by perf-repair; storage stays ns/op."""
from __future__ import annotations

from dataclasses import dataclass

NS_PER = {"ms": 1e6, "us": 1e3, "ns": 1.0}
# bytes per unit, MB = 10^6 as in cryptobenchmark; ops/s counts calls, so it needs no input size
BYTES_PER = {"MB/s": 1e6, "MiB/s": 2 ** 20, "ops/s": None}
SIGNIFICANT = 4


@dataclass(frozen=True)
class DisplayUnits:
    """The defaults mirror AnalysisSettings.Units in cryptobenchmark's :config; a manifest before units has none."""
    latency: str = "ms"
    throughput: str = "MB/s"

    @classmethod
    def parse(cls, doc, where: str = "manifest units") -> "DisplayUnits":
        doc = doc or {}
        units = cls(doc.get("latency", cls.latency), doc.get("throughput", cls.throughput)) if isinstance(doc, dict) else None
        if units is None or set(doc) - {"latency", "throughput"} or units.latency not in NS_PER or units.throughput not in BYTES_PER:
            raise ValueError(f"invalid: {where} {doc!r}, latency one of {list(NS_PER)}, throughput one of {list(BYTES_PER)}")
        return units

    @property
    def latency_label(self) -> str:
        return f"{self.latency}/op"

    def latency_of(self, ns: float) -> float:
        return ns / NS_PER[self.latency]

    def throughput_of(self, ns: float, input_size: int | None) -> float | None:
        """None when the unit needs an input size the case has none of, or the time is not positive."""
        per = BYTES_PER[self.throughput]
        if not ns or ns <= 0 or (per is not None and not input_size):
            return None
        return 1e9 / ns * (1 if per is None else input_size / per)

    def to_json(self) -> dict:
        return {"latency": self.latency, "throughput": self.throughput}


def number(x: float | None, missing: str = "n/a") -> str:
    """Significant figures, so a sub-unit value never rounds to 0 (64 B AES-CBC is 0.000662 ms)."""
    return missing if x is None else f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.{SIGNIFICANT}g}"
