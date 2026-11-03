"""perfMode: which registry metrics a decision is given; `generic` gives every one and names those without data."""
from __future__ import annotations

from dataclasses import dataclass

from .metrics import METRICS, Metric

GENERIC = "generic"
KEYS = tuple(k for m in METRICS for k in m.selects)
SEPARATOR = "+"


@dataclass(frozen=True)
class PerfMode:
    """keys: the selection, deduplicated in registry order; () is generic."""
    keys: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value) -> "PerfMode":
        """`generic`, a list of KEYS, or the same as one `+`- or `,`-joined text; anything else raises ValueError."""
        if value == GENERIC:
            return cls()
        listed = value.replace(",", SEPARATOR).split(SEPARATOR) if isinstance(value, str) else value
        if not isinstance(listed, (list, tuple)) or not listed or any(k not in KEYS for k in listed):
            raise ValueError(f"perfMode {value!r} is neither {GENERIC} nor a non-empty list of {list(KEYS)}")
        return cls(tuple(k for k in KEYS if k in listed))

    @property
    def generic(self) -> bool:
        return not self.keys

    @property
    def name(self) -> str:
        return SEPARATOR.join(self.keys) or GENERIC

    @property
    def metrics(self) -> tuple[Metric, ...]:
        return tuple(m for m in METRICS if self.generic or set(m.selects) & set(self.keys))

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(m.name for m in self.metrics)

    @property
    def required(self) -> tuple[Metric, ...]:
        """The metrics a decision needs data for; generic decides on what was measured."""
        return () if self.generic else self.metrics

    def views(self, metric: Metric) -> tuple[str, ...]:
        """The keys a selected metric is shown as: timeNs as latency, throughput or both, one estimate either way."""
        return tuple(k for k in metric.selects if self.generic or k in self.keys)

    def to_json(self):
        return list(self.keys) or GENERIC
