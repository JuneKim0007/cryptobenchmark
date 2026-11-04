"""perfMode is the only owner of what the guide measures: run.metrics is its metrics within what the harness can measure,
written into a generated config; a strict metric the harness cannot measure at all stops before any run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import run_dir as rd
from ..dto.event import LOG
from ..dto.metrics import ENERGY, METRICS, Metric
from ..dto.perf_mode import PerfMode
from ..files import read_yaml
from ..log import emit
from ..stop import terminate
from .selection import generated, relocated

DEFAULT_METRICS = ("TIME",)
ALLOCATION_RUN = "ALLOCATION"
ALLOCATION_PASS = "allocation"
# capture values that measure energy; a test set may still turn it on per case, so its absence only warns
CAPTURES = ("measured", "dry")


@dataclass(frozen=True)
class Harness:
    name: str
    metrics: tuple[str, ...]
    captures_energy: bool

    def can_measure(self, m: Metric) -> bool:
        return self.captures_energy if m is ENERGY else m.run in self.metrics


# HostHarness.METRICS in apps/benchmark/modules/benchmark run/HostHarness.kt; JetpackConfig.METRICS in apps/benchmark/modules/android, less CPU_EVENTS no perfMode selects
HOST = Harness("host JVM harness (--bench)", ("TIME",), captures_energy=False)
DEVICE = Harness("device harness (--device)", ("TIME", ALLOCATION_RUN), captures_energy=True)


def harness_of(on_device: bool) -> Harness:
    return DEVICE if on_device else HOST


def _capture(run: dict) -> str | None:
    return ((run.get("harness") or {}).get("energy") or {}).get("capture")


def switched_on(doc: dict) -> set[str]:
    """The registry `run` switches a global.yaml turns on: run.metrics, and energy when the run captures it."""
    run = doc.get("run") or {}
    on = set(run.get("metrics") or DEFAULT_METRICS)
    return on | ({ENERGY.run} if _capture(run) in CAPTURES else set())


def run_metrics(perf: PerfMode, harness: Harness) -> list[str]:
    """What run.metrics says for this perfMode on this harness; a required metric always, the config refuses a list without it."""
    return [m.run for m in METRICS if m.run in harness.metrics and (m.required or m in perf.metrics)]


def _owned_run(run: dict, perf: PerfMode, harness: Harness) -> dict:
    """The run section with perfMode's metrics, and what the config or the harness would refuse beside them taken out."""
    metrics = run_metrics(perf, harness)
    owned = {**run, "metrics": metrics}
    passes = run.get("passes") or {}
    # RunSettings.kt refuses an allocation pass without ALLOCATION in run.metrics
    if ALLOCATION_PASS in passes and ALLOCATION_RUN not in metrics:
        owned["passes"] = {k: v for k, v in passes.items() if k != ALLOCATION_PASS}
    if not harness.captures_energy and _capture(run) in CAPTURES:
        section = run["harness"]
        owned["harness"] = {**section, "energy": {**section["energy"], "capture": "none"}}
    return owned


def _beside_metrics_changed(run: dict, owned: dict) -> bool:
    return any(run.get(k) != owned.get(k) for k in ("passes", "harness"))


def _metrics_changed(run: dict, owned: dict) -> bool:
    return set(run.get("metrics") or DEFAULT_METRICS) != set(owned["metrics"])


def owned_config(base: Path, folder: Path, perf: PerfMode, on_device: bool) -> Path:
    """base when it already measures what perfMode needs, so its digest stays; else <folder>/metrics-global.yaml, which
    the device stage then treats as its base."""
    path = Path(folder) / rd.METRICS_CONFIG
    run = ((read_yaml(base) or {}).get("run") or {}) if Path(base).is_file() else {}
    owned = _owned_run(run, perf, harness_of(on_device))
    if not Path(base).is_file() or not (_metrics_changed(run, owned) or _beside_metrics_changed(run, owned)):
        path.unlink(missing_ok=True)
        return Path(base)
    path.parent.mkdir(parents=True, exist_ok=True)
    return generated(path, base, "perfMode owns run.metrics", {**relocated(base), "run": owned})


def _named(metrics) -> str:
    return ", ".join(m.name for m in metrics)


def _impossible(harness: Harness, perf: PerfMode, required: tuple[Metric, ...]) -> None:
    hard = [m for m in required if not harness.can_measure(m)]
    if hard:
        terminate("perf_mode_unmeasured", f"perfMode {perf.name} requires {_named(hard)}; the {harness.name} measures only "
                  f"{_named(m for m in METRICS if harness.can_measure(m))}", stage="device", step="measures",
                  data={"items": [m.name for m in hard]})


def _maybe_no_energy(config: Path, harness: Harness, on: set[str], required: tuple[Metric, ...]) -> None:
    if ENERGY in required and harness.captures_energy and ENERGY.run not in on:
        terminate("perf_mode_maybe_unmeasured", f"{ENERGY.name} is selected but {config} does not set "
                  "run.harness.energy.capture: measured; only cases a test set turns it on for get it, the rest are "
                  "no_evidence", stage="device", step="measures", item=ENERGY.name)


def _overridden(config: Path, doc: dict, perf: PerfMode, harness: Harness) -> None:
    run = doc.get("run") or {}
    owned = _owned_run(run, perf, harness)
    if (run.get("metrics") and _metrics_changed(run, owned)) or _beside_metrics_changed(run, owned):
        terminate("run_metrics_overridden", f"{config} sets run.metrics {run.get('metrics') or list(DEFAULT_METRICS)}; perfMode "
                  f"{perf.name} measures {owned['metrics']} on the {harness.name}", stage="device", step="measures")


def _extra(config: Path, perf: PerfMode, harness: Harness, on: set[str]) -> None:
    if harness.captures_energy and ENERGY.run in on and ENERGY not in perf.metrics:
        emit("device", "measures", LOG, detail=f"perf_mode_extra: {config} measures {ENERGY.name}, which perfMode {perf.name} "
                                               "does not select; device time no decision reads")


def _said(perf: PerfMode, harness: Harness, on: set[str]) -> str:
    measured = [m for m in perf.metrics if m.run in run_metrics(perf, harness)
                or (m is ENERGY and harness.captures_energy and ENERGY.run in on)]
    left = [m for m in perf.metrics if m not in measured]
    return (f"measures: {_named(measured) or 'none selected'} on the {harness.name}, perfMode {perf.name}"
            + (f"; not measured: {_named(left)}" if left else ""))


def check_measures(config: Path, perf: PerfMode, on_device: bool = False, required: tuple[Metric, ...] | None = None) -> str:
    """required: the metrics a stop guards, perf's own by default; generic requires none, so it never stops here.
    Returns the line that says what this run measures."""
    harness = harness_of(on_device)
    required = perf.required if required is None else required
    _impossible(harness, perf, required)
    doc = (read_yaml(config) or {}) if Path(config).is_file() else {}
    on = switched_on(doc)
    _maybe_no_energy(config, harness, on, required)
    _overridden(config, doc, perf, harness)
    _extra(config, perf, harness, on)
    return _said(perf, harness, on)
