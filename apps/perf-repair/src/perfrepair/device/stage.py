"""probe_device(): the device's folder made current, each stage reused or rerun by its input digests (device/plan.py)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from cryptobench.catalogue.names import CATALOG
from ..data_handler.inbound import read_manifest
from ..data_handler.outbound.benchmark_runner import check_dependencies, identify
from ..dto.bundled import BundledPolicy
from ..dto.device import DeviceRecord, runtime_summary
from ..dto.event import END
from ..dto.metrics import Metric
from ..dto.perf_mode import GENERIC_MODE, PerfMode
from ..dto.primitives_missing import NOT_SCREENED
from ..files import sha256_file
from ..log import emit
from ..result.primitives import NotScreened
from ..run_dir.lock import DeviceLock
from ..screen.catalog import Catalog
from .measures import check_measures, owned_config
from .missing_rows import not_screened_rows
from .plan import STAGES
from .primitives import inputs as primitive_inputs
from .primitives_missing import MissingList
from .seen import seen
from .selection import section
from .stage_pass import Pass, drop_record, scoped_pass, whole_pass, with_device_probe
from .stage_run import Run, run_stages
from .used import write_used

REUSED = "its inputs match device.yaml"


@dataclass(frozen=True)
class DeviceStage:
    folder: Path
    steps: dict[str, str | None]
    # the global.yaml the run was named, before perfMode's run.metrics
    config: Path | None = None

    @property
    def ran(self) -> list[str]:
        return [s for s, reason in self.steps.items() if reason]


def _reused(done: Pass, on_device: bool) -> dict:
    steps = with_device_probe(done.steps, done.todo, on_device)
    for stage in STAGES:
        if not steps[stage]:
            emit("device", stage, END, outcome="reused", detail=REUSED)
    return steps


def _record(folder: Path, identity: dict, current: dict, done: Pass) -> None:
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    scoped = section(manifest.inputs.get("config"), done.keep) if done.keep else done.kept
    bundled = {"applied": done.applied, "bundled": manifest.inputs.get("bundled"),
               "config": manifest.inputs.get("config")} if done.applied else {}
    rd.write_device_record(folder, DeviceRecord(identity["deviceId"], identity["mode"], runtime_summary(manifest.runtime),
                                                current, sha256_file(folder / rd.MANIFEST), primitive_inputs(folder), scoped,
                                                bundled))


def probe_device(root: Path, catalog: Catalog, config: Path | None = None, on_device: bool = False,
                 echo: Callable[[str], None] = print, benchmark: Path | str | None = None,
                 refresh: bool = False, detect: Callable[[Path], list[str]] | None = None,
                 perf: PerfMode = GENERIC_MODE, bundled: BundledPolicy = BundledPolicy(),
                 named: Callable[[Path], None] = lambda _: None, required: tuple[Metric, ...] | None = None,
                 missing: MissingList | None = None) -> DeviceStage:
    """No model call: grouping assign stays with its caller; refresh rebuilds primitives.tsv. detect: the target apps'
    folders found on the probe (device.filterByApps); with it the benchmark measures their used set only, after the
    device.bundled step. perf: owns run.metrics (device/measures.py); required: the metrics that stop when unmeasurable,
    perf's own by default. named: told the folder once known, so a failed first run still reports into it.
    missing: told each primitive the run finds unavailable; None: nothing is listed."""
    check_dependencies(config, on_device, benchmark)
    identity = identify(config, on_device, benchmark)
    base = Path(identity["config"])
    echo(check_measures(base, perf, on_device, required))
    folder = Path(root) / identity["deviceId"]
    named(folder)
    # a second run on the folder stops here, device_busy, before it reads or drops anything
    with DeviceLock.take(folder):
        measured = owned_config(base, folder, perf, on_device)
        # the plan compares the digests of the config that measures, so a perfMode that changes run.metrics reruns the benchmark
        identity = identify(measured, on_device, benchmark) if measured != base else identity
        r = Run(Path(root), folder, catalog, Path(identity["config"]), on_device, echo, benchmark, bundled=bundled,
                missing=missing or MissingList())
        return replace(_made(r, identity, refresh, detect), config=base)


def _made(r: Run, identity: dict, refresh: bool, detect: Callable[[Path], list[str]] | None) -> DeviceStage:
    folder, echo, on_device = r.folder, r.echo, r.on_device
    current = {**identity["inputs"], "names": sha256_file(CATALOG), "screening": r.catalog.sha256}
    before = seen(folder)
    done = scoped_pass(r, before, current, refresh, detect) if detect else whole_pass(r, before, current, refresh)
    drop_record(folder, done.todo)
    steps = _reused(done, on_device)
    try:
        run_stages(done.run, done.todo)
    except NotScreened as e:
        r.missing.put(NOT_SCREENED, not_screened_rows(folder, e.names, done.apps or []))
        raise
    if done.apps is not None and done.todo["screen"]:
        write_used(folder, done.apps)
    _record(folder, identity, current, done)
    for stage in STAGES:
        echo(f"device {stage}: " + (f"ran: {steps[stage]}" if steps[stage] else "reused"))
    return DeviceStage(folder, steps)
