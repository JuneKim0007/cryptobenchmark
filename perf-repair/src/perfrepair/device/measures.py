"""The run config's measurements against the perfMode: a selected metric nothing measures stops before the device runs,
one measured but not selected is device time spent for nothing and is logged. The config is never rewritten."""
from __future__ import annotations

from pathlib import Path

from ..dto.event import LOG
from ..dto.metrics import METRICS, Metric
from ..dto.perf_mode import PerfMode
from ..files import read_yaml
from ..log import emit

DEFAULT_METRICS = ("TIME",)
ENERGY_RUN = "energy"
# capture values that measure energy; a test set may still turn it on per case, so its absence only warns
CAPTURES = ("measured", "dry")


class PerfModeUnmeasured(ValueError):
    pass


def switched_on(doc: dict) -> set[str]:
    """The registry `run` switches a global.yaml turns on: run.metrics, and energy when the run captures it."""
    run = doc.get("run") or {}
    on = set(run.get("metrics") or DEFAULT_METRICS)
    capture = ((run.get("harness") or {}).get("energy") or {}).get("capture")
    return on | ({ENERGY_RUN} if capture in CAPTURES else set())


def _switch(m: Metric) -> str:
    return "run.harness.energy.capture: measured" if m.run == ENERGY_RUN else f"{m.run} in run.metrics"


def check_measures(config: Path, perf: PerfMode) -> None:
    """generic measures what the config says and decides on what was measured, so it checks nothing."""
    if perf.generic or not Path(config).is_file():
        return
    on = switched_on(read_yaml(config) or {})
    missing = [m for m in perf.metrics if m.run not in on]
    hard = [m for m in missing if m.run != ENERGY_RUN]
    if hard:
        raise PerfModeUnmeasured(f"perf_mode_unmeasured: perfMode {perf.name} selects {', '.join(m.name for m in hard)}; "
                                 f"{config} measures none of it; add {', '.join(_switch(m) for m in hard)}")
    for m in missing:
        emit("device", "measures", LOG, detail=f"perf_mode_unmeasured: {m.name} is selected but {config} does not set "
                                               f"{_switch(m)}; only cases a test set turns it on for get it, the rest are no_evidence")
    extra = [m for m in METRICS if m.run in on and m not in perf.metrics and not m.required]
    if extra:
        emit("device", "measures", LOG, detail=f"perf_mode_extra: {config} measures {', '.join(m.name for m in extra)}, "
                                               f"which perfMode {perf.name} does not select; device time no decision reads")
