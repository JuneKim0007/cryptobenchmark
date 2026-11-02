"""probe_device(): the device's folder made current, each stage reused or rerun by its input digests (device/plan.py)."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..catalog.names import CATALOG
from ..data_handler.inbound import read_manifest
from ..data_handler.outbound.benchmark_runner import identify, run_pipeline
from ..dto.device import DeviceRecord, runtime_summary
from ..dto.event import END
from ..files import sha256_file
from ..grouping.build.stage import build_stage
from ..log import emit, step
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from .inbound import write_inbound
from .plan import STAGES, Seen, plan

# a device run installs and probes before it measures, so its probe is never the one already there
DEVICE_PROBES = "a device benchmark probes the device it measures"


@dataclass(frozen=True)
class DeviceStage:
    folder: Path
    steps: dict[str, str | None]

    @property
    def ran(self) -> list[str]:
        return [s for s, reason in self.steps.items() if reason]


def seen(folder: Path) -> Seen:
    manifest = read_manifest(folder / rd.MANIFEST)[0] if (folder / rd.MANIFEST).is_file() else None
    record, problem = rd.load_device_record(folder)
    grouping = GroupingPaths(folder)
    return Seen(manifest, sha256_file(folder / rd.MANIFEST), record, problem,
                rows=all((folder / f).is_file() for f in (rd.ROWS, rd.MEASUREMENTS, rd.RUN_LOG)),
                grouping=all(p.is_file() for p in (grouping.items, grouping.profiles, grouping.screen)))


def _measure(root: Path, folder: Path, config: Path | None, on_device: bool, steps: dict, echo, benchmark) -> None:
    # on a host, a kept probe is reused by the benchmark run itself, so the capture is the one the plan judged
    reuse = () if on_device or steps["probe"] else ("--discovery", "reuse")
    manifest = run_pipeline(config, root, "device" if on_device else "bench", benchmark=benchmark, echo=echo, extra=reuse)
    if manifest.parent.resolve() != folder.resolve():
        raise ValueError(f"device_id_changed: --identify named {folder.name}, the probe wrote {manifest.parent.name}")


@contextmanager
def _ran(stage: str, reason: str):
    with step("device", stage, detail=reason) as s:
        s.outcome, s.detail = "ran", reason
        yield


def _run(root: Path, folder: Path, steps: dict, catalog: Catalog, config: Path | None, on_device: bool, echo,
         benchmark) -> None:
    if steps["benchmark"]:
        with _ran("benchmark", steps["benchmark"]):
            _measure(root, folder, config, on_device, steps, echo, benchmark)
        if steps["probe"]:
            emit("device", "probe", END, outcome="ran", detail=steps["probe"], data={"ranWith": "benchmark"})
    if steps["inbound"]:
        with _ran("inbound", steps["inbound"]):
            for line in write_inbound(folder):
                echo(line)
    if steps["screen"]:
        with _ran("screen", steps["screen"]):
            build_stage(folder / rd.MANIFEST, folder, catalog, echo=echo)


def probe_device(root: Path, catalog: Catalog, config: Path | None = None, on_device: bool = False,
                 echo: Callable[[str], None] = print, benchmark: Path | str | None = None) -> DeviceStage:
    """No model call: grouping assign stays with its caller."""
    identity = identify(config, on_device, benchmark)
    folder = Path(root) / identity["deviceId"]
    current = {**identity["inputs"], "names": sha256_file(CATALOG), "screening": catalog.sha256}
    steps = plan(seen(folder), current)
    if on_device and steps["benchmark"] and not steps["probe"]:
        steps["probe"] = DEVICE_PROBES
    for stage in STAGES:
        if not steps[stage]:
            emit("device", stage, END, outcome="reused")
    if any(steps.values()):
        # a record exists only while every stage it vouches for is whole, so an interrupted run reruns them
        (folder / rd.DEVICE).unlink(missing_ok=True)
        _run(Path(root), folder, steps, catalog, config, on_device, echo, benchmark)
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    rd.write_device_record(folder, DeviceRecord(identity["deviceId"], identity["mode"], runtime_summary(manifest.runtime),
                                                current, sha256_file(folder / rd.MANIFEST)))
    for stage in STAGES:
        echo(f"device {stage}: " + (f"ran: {steps[stage]}" if steps[stage] else "reused"))
    return DeviceStage(folder, steps)
