"""The run config's measurements against the perfMode: a selected metric nothing measures is perf_mode_unmeasured before
the device runs, one measured but not selected is device time spent for nothing and is logged. The config is never
rewritten."""
from __future__ import annotations

from pathlib import Path

from ..dto.event import LOG
from ..dto.metrics import METRICS, Metric
from ..dto.perf_mode import PerfMode
from ..files import read_yaml
from ..log import emit
from ..stop import terminate

DEFAULT_METRICS = ("TIME",)
ENERGY_RUN = "energy"
# capture values that measure energy; a test set may still turn it on per case, so its absence only warns
CAPTURES = ("measured", "dry")


def switched_on(doc: dict) -> set[str]:
    """The registry `run` switches a global.yaml turns on: run.metrics, and energy when the run captures it."""
    run = doc.get("run") or {}
    on = set(run.get("metrics") or DEFAULT_METRICS)
    capture = ((run.get("harness") or {}).get("energy") or {}).get("capture")
    return on | ({ENERGY_RUN} if capture in CAPTURES else set())


def _switch(m: Metric) -> str:
    return "run.harness.energy.capture: measured" if m.run == ENERGY_RUN else f"{m.run} in run.metrics"


def _missing(config: Path, perf: PerfMode, on: set[str]) -> None:
    missing = [m for m in perf.metrics if m.run not in on]
    _unmeasured(config, perf, [m for m in missing if m.run != ENERGY_RUN])
    for m in (m for m in missing if m.run == ENERGY_RUN):
        terminate("perf_mode_maybe_unmeasured", f"{m.name} is selected but {config} does not set {_switch(m)}; only "
                  "cases a test set turns it on for get it, the rest are no_evidence", stage="device", step="measures",
                  item=m.name)


def _unmeasured(config: Path, perf: PerfMode, hard: list[Metric]) -> None:
    if hard:
        terminate("perf_mode_unmeasured", f"perfMode {perf.name} selects {', '.join(m.name for m in hard)}; {config} "
                  f"measures none of it; add {', '.join(_switch(m) for m in hard)}", stage="device", step="measures",
                  data={"items": [m.name for m in hard]})


def _extra(config: Path, perf: PerfMode, on: set[str]) -> None:
    extra = [m for m in METRICS if m.run in on and m not in perf.metrics and not m.required]
    if extra:
        emit("device", "measures", LOG, detail=f"perf_mode_extra: {config} measures {', '.join(m.name for m in extra)}, "
                                               f"which perfMode {perf.name} does not select; device time no decision reads")


def check_measures(config: Path, perf: PerfMode) -> None:
    """generic measures what the config says and decides on what was measured, so it checks nothing."""
    if perf.generic or not Path(config).is_file():
        return
    on = switched_on(read_yaml(config) or {})
    _missing(config, perf, on)
    _extra(config, perf, on)
