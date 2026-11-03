"""perfMode: which registry metrics a decision is given; `generic` and `all` spell every key, with the overall-judgement rule."""
from __future__ import annotations

from dataclasses import dataclass

from .metrics import ALL_KEYS, METRICS, Metric

GENERIC = "generic"
ALL = "all"
KEYS = ALL_KEYS
SEPARATOR = "+"
# a selected metric without data: the reason code, never a proxy
NO_EVIDENCE = "no_evidence"


def no_evidence(names) -> str:
    return f"{NO_EVIDENCE}: {', '.join(names)}"


@dataclass(frozen=True)
class PerfMode:
    """keys: the selection, deduplicated in registry order. overall: the model may judge overall performance and pick
    a trade-off; False is the strict rule of a hand-written list, even one naming every key."""
    keys: tuple[str, ...] = KEYS
    overall: bool = False

    @classmethod
    def parse(cls, value) -> "PerfMode":
        """`generic`, `all`, a list of KEYS, or the same as one `+`- or `,`-joined text; anything else raises ValueError."""
        if value in (GENERIC, ALL):
            return cls(overall=True)
        listed = value.replace(",", SEPARATOR).split(SEPARATOR) if isinstance(value, str) else value
        if not isinstance(listed, (list, tuple)) or not listed or any(k not in KEYS for k in listed):
            raise ValueError(f"perfMode {value!r} is neither {GENERIC}, {ALL} nor a non-empty list of {list(KEYS)}")
        return cls(tuple(k for k in KEYS if k in listed))

    @classmethod
    def union(cls, modes) -> "PerfMode":
        """What a run must measure for several apps: every key any of them selects."""
        chosen = {k for m in modes for k in m.keys}
        return cls(tuple(k for k in KEYS if k in chosen))

    @property
    def name(self) -> str:
        return GENERIC if self.overall else SEPARATOR.join(self.keys)

    @property
    def metrics(self) -> tuple[Metric, ...]:
        return tuple(m for m in METRICS if set(m.selects) & set(self.keys))

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(m.name for m in self.metrics)

    @property
    def required(self) -> tuple[Metric, ...]:
        return self.metrics

    def views(self, metric: Metric) -> tuple[str, ...]:
        """The keys a selected metric is shown as: timeNs as latency, throughput or both, one estimate either way."""
        return tuple(k for k in metric.selects if k in self.keys)

    def to_json(self):
        return GENERIC if self.overall else list(self.keys)


GENERIC_MODE = PerfMode(overall=True)
