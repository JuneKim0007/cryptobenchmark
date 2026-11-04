"""probe_device(): the device's folder made current, each stage reused or rerun by its input digests (device/plan.py)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..catalog.names import CATALOG
from ..data_handler.inbound import read_manifest
from ..data_handler.outbound.benchmark_runner import identify
from ..dto.bundled import BundledPolicy
from ..dto.device import DeviceRecord, runtime_summary
from ..dto.event import END
from ..files import sha256_file
from ..log import emit
from ..screen.catalog import Catalog
from ..dto.perf_mode import GENERIC_MODE, PerfMode
from .measures import check_measures
from .primitives import inputs as primitive_inputs
from .plan import STAGES
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
                 named: Callable[[Path], None] = lambda _: None) -> DeviceStage:
    """No model call: grouping assign stays with its caller; refresh rebuilds primitives.tsv. detect: the target apps'
    folders found on the probe (device.filterByApps); with it the benchmark measures their used set only, after the
    device.bundled step. perf: the run config must measure what it selects, checked before any device run. named: told
    the folder once known, so a failed first run still reports into it."""
    identity = identify(config, on_device, benchmark)
    check_measures(Path(identity["config"]), perf)
    folder = Path(root) / identity["deviceId"]
    named(folder)
    current = {**identity["inputs"], "names": sha256_file(CATALOG), "screening": catalog.sha256}
    before = seen(folder)
    r = Run(Path(root), folder, catalog, Path(identity["config"]), on_device, echo, benchmark, bundled=bundled)
    done = scoped_pass(r, before, current, refresh, detect) if detect else whole_pass(r, before, current, refresh)
    drop_record(folder, done.todo)
    steps = _reused(done, on_device)
    run_stages(done.run, done.todo)
    if done.apps is not None and done.todo["screen"]:
        write_used(folder, done.apps)
    _record(folder, identity, current, done)
    for stage in STAGES:
        echo(f"device {stage}: " + (f"ran: {steps[stage]}" if steps[stage] else "reused"))
    return DeviceStage(folder, steps)
