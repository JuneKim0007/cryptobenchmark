"""The metric registry: every metric perf-repair reads, by its benchmark.json name; no other file lists them."""
from __future__ import annotations

from dataclasses import dataclass

MEASURED, ESTIMATED = "measured", "estimated"


@dataclass(frozen=True)
class Metric:
    name: str
    unit: str
    lowerIsBetter: bool
    # the values its `kind` takes, the first when benchmark.json gives none; () has no kind
    kinds: tuple[str, ...]
    # perfMode keys that select it, in display order; throughput is timeNs per second, never a metric of its own
    selects: tuple[str, ...]
    required: bool
    positive: bool
    # what cryptobenchmark's run.metrics or harness.energy.capture turns on to measure it
    run: str
    # the run.passes session that measures it
    passName: str = "timing"


TIME = Metric("timeNs", "ns/op", True, (), ("latency", "throughput"), required=True, positive=True, run="TIME")
ALLOCATIONS = Metric("allocationCount", "allocations/op", True, (), ("memAlloc",), required=False, positive=False,
                     run="ALLOCATION", passName="allocation")
ENERGY = Metric("energyJ", "J/op", True, (MEASURED, ESTIMATED), ("energy",), required=False, positive=False, run="energy",
                passName="energy")
METRICS = (TIME, ALLOCATIONS, ENERGY)
NAMES = tuple(m.name for m in METRICS)
BY_NAME = {m.name: m for m in METRICS}
# every perfMode key in registry order: what `generic` and `all` expand to, a new metric included
ALL_KEYS = tuple(k for m in METRICS for k in m.selects)
