"""probe_device(): the device's folder made current, each stage reused or rerun by its input digests (device/plan.py)."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..catalog.names import CATALOG
from ..data_handler.inbound import read_manifest
from ..data_handler.outbound.benchmark_runner import identify, run_pipeline
from ..dto.device import DeviceRecord, runtime_summary
from ..dto.event import END
from ..dto.grouping import read_items
from ..files import read_json, sha256_file
from ..grouping.build.stage import build_stage
from ..log import emit, step
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..dto.perf_mode import PerfMode
from .energy import report_invalid
from .inbound import write_inbound
from .measures import check_measures
from .primitives import inputs as primitive_inputs, write_primitives
from .plan import STAGES, Seen, plan
from .selection import FILTER_OFF, exclusions, lacking, measured, section, write_config
from .used import write_used

# a device run installs and probes before it measures, so its probe is never the one already there
DEVICE_PROBES = "a device benchmark probes the device it measures"
NO_ITEM = "no target app reaches a device item: the base selection is measured"


@dataclass(frozen=True)
class DeviceStage:
    folder: Path
    steps: dict[str, str | None]

    @property
    def ran(self) -> list[str]:
        return [s for s, reason in self.steps.items() if reason]


@dataclass(frozen=True)
class Run:
    """What one probe_device call runs with; probed: the probe is current before the benchmark, so a host run reuses it."""
    root: Path
    folder: Path
    catalog: Catalog
    config: Path | None
    on_device: bool
    echo: Callable[[str], None]
    benchmark: Path | str | None
    probed: bool = False


def _inbound(folder: Path) -> str | None:
    missing = [f for f in (rd.ROWS, rd.MEASUREMENTS, rd.RUN_LOG) if not (folder / f).is_file()]
    if missing:
        return f"{missing[0]} missing"
    try:
        rd.load_measurements(folder)
    except (ValueError, KeyError, TypeError) as e:
        return f"{rd.MEASUREMENTS} unreadable ({e})"
    return None


def seen(folder: Path) -> Seen:
    manifest = read_manifest(folder / rd.MANIFEST)[0] if (folder / rd.MANIFEST).is_file() else None
    record, problem = rd.load_device_record(folder)
    grouping = GroupingPaths(folder)
    return Seen(manifest, sha256_file(folder / rd.MANIFEST), record, problem,
                inbound=_inbound(folder),
                grouping=all(p.is_file() for p in (grouping.items, grouping.profiles, grouping.screen)),
                primitives=(folder / rd.PRIMITIVES).is_file(), made_from=primitive_inputs(folder))


def _same_folder(manifest: Path, folder: Path) -> None:
    if manifest.parent.resolve() != folder.resolve():
        raise ValueError(f"device_id_changed: --identify named {folder.name}, the probe wrote {manifest.parent.name}")


def _measure(r: Run, steps: dict) -> None:
    # on a host, a kept probe is reused by the benchmark run itself, so the capture is the one the plan judged
    fresh = steps["probe"] and not r.probed
    reuse = () if r.on_device or fresh else ("--discovery", "reuse")
    manifest = run_pipeline(r.config, r.root, "device" if r.on_device else "bench", benchmark=r.benchmark, echo=r.echo,
                            extra=reuse, device=r.folder)
    _same_folder(manifest, r.folder)
    report_invalid(manifest)


@contextmanager
def _ran(stage: str, reason: str):
    with step("device", stage, detail=reason) as s:
        s.outcome, s.detail = "ran", reason
        yield


def _run(r: Run, steps: dict) -> None:
    if steps["benchmark"]:
        with _ran("benchmark", steps["benchmark"]):
            _measure(r, steps)
        if steps["probe"] and not r.probed:
            emit("device", "probe", END, outcome="ran", detail=steps["probe"], data={"ranWith": "benchmark"})
    if steps["inbound"]:
        with _ran("inbound", steps["inbound"]):
            for line in write_inbound(r.folder):
                r.echo(line)
    if steps["screen"]:
        with _ran("screen", steps["screen"]):
            build_stage(r.folder / rd.MANIFEST, r.folder, r.catalog, echo=r.echo)
    if steps["primitives"]:
        with _ran("primitives", steps["primitives"]):
            r.echo(write_primitives(r.folder))


def _probed(r: Run, steps: dict) -> None:
    if steps["probe"]:
        with _ran("probe", steps["probe"]):
            _same_folder(run_pipeline(r.config, r.root, "device" if r.on_device else "configure", benchmark=r.benchmark,
                                      echo=r.echo, extra=("--probe",), device=r.folder), r.folder)
    if steps["screen"]:
        with _ran("screen", steps["screen"]):
            build_stage(r.folder / rd.MANIFEST, r.folder, r.catalog, echo=r.echo)


def _measured_set(r: Run, keep: frozenset[str]) -> Path:
    with step("device", "selection") as s:
        paths = GroupingPaths(r.folder)
        items = read_items(read_json(paths.items))
        rules = exclusions(items, rd.load_screen(paths), keep)
        path = write_config(Path(r.config), r.folder, rules)
        s.count(deviceItems=len(items), measured=len(keep), excluded=len(rules))
        s.wrote(path)
    return path


@dataclass(frozen=True)
class Pass:
    """steps: what the lines report; todo: what is left to run; keep: the set measured now; kept: device.yaml's section
    when nothing is measured."""
    steps: dict
    todo: dict
    run: Run
    keep: frozenset[str] | None = None
    apps: list[str] | None = None
    kept: dict = field(default_factory=dict)


def _drop_record(folder: Path, steps: dict) -> None:
    # a record exists only while every stage it vouches for is whole, so an interrupted run reruns them
    if any(steps.values()):
        (folder / rd.DEVICE).unlink(missing_ok=True)


def _whole(r: Run, before: Seen, current: dict, refresh: bool) -> Pass:
    scoped = before.record.benchmark if before.record else {}
    steps = plan(before, current, refresh, {"benchmark": FILTER_OFF} if scoped else None)
    return Pass(steps, steps, r)


def _keep(used: frozenset[str], before: Seen, todo: dict) -> frozenset[str] | None:
    if not todo["benchmark"]:
        return None
    keep = used | (measured(before.record) or frozenset())
    if not keep:
        emit("device", "selection", END, outcome="ok", detail=NO_ITEM)
    return keep or None


def _left(todo: dict) -> dict:
    """The probe ran first, and the screen too unless the benchmark reruns, which a screen reads."""
    return {**todo, "probe": None, "screen": todo["screen"] if todo["benchmark"] else None}


def _scoped(r: Run, before: Seen, current: dict, refresh: bool, detect: Callable[[Path], list[str]]) -> Pass:
    """Probe and screen first, so the apps resolve against today's items; then the used set, and the benchmark only for
    what it lacks."""
    steps = plan(before, current, refresh)
    _drop_record(r.folder, steps)
    _probed(r, steps)
    apps = detect(r.folder)
    used = write_used(r.folder, apps)
    manifest, _ = read_manifest(r.folder / rd.MANIFEST)
    lack = lacking(used.names, before.record, manifest.inputs.get("config"), current["config"])
    todo = _left(plan(before, current, refresh, {"benchmark": lack} if lack else None))
    keep = _keep(used.names, before, todo)
    config = _measured_set(r, keep) if keep else r.config
    reported = {s: steps[s] if s in ("probe", "screen") and steps[s] else todo[s] for s in STAGES}
    return Pass(reported, todo, replace(r, config=config, probed=True), keep, apps,
                before.record.benchmark if before.record else {})


def _reused(done: Pass, on_device: bool) -> dict:
    steps = done.steps
    if on_device and done.todo["benchmark"] and not steps["probe"]:
        steps["probe"] = DEVICE_PROBES
    for stage in STAGES:
        if not steps[stage]:
            emit("device", stage, END, outcome="reused")
    return steps


def _record(folder: Path, identity: dict, current: dict, done: Pass) -> None:
    manifest, _ = read_manifest(folder / rd.MANIFEST)
    scoped = section(manifest.inputs.get("config"), done.keep) if done.keep else done.kept
    rd.write_device_record(folder, DeviceRecord(identity["deviceId"], identity["mode"], runtime_summary(manifest.runtime),
                                                current, sha256_file(folder / rd.MANIFEST), primitive_inputs(folder), scoped))


def probe_device(root: Path, catalog: Catalog, config: Path | None = None, on_device: bool = False,
                 echo: Callable[[str], None] = print, benchmark: Path | str | None = None,
                 refresh: bool = False, detect: Callable[[Path], list[str]] | None = None,
                 perf: PerfMode = PerfMode()) -> DeviceStage:
    """No model call: grouping assign stays with its caller; refresh rebuilds primitives.tsv. detect: the target apps'
    folders found on the probe (device.filterByApps); with it the benchmark measures their used set only. perf: the run
    config must measure what it selects, checked before any device run."""
    identity = identify(config, on_device, benchmark)
    check_measures(Path(identity["config"]), perf)
    folder = Path(root) / identity["deviceId"]
    current = {**identity["inputs"], "names": sha256_file(CATALOG), "screening": catalog.sha256}
    before = seen(folder)
    r = Run(Path(root), folder, catalog, Path(identity["config"]), on_device, echo, benchmark)
    done = _scoped(r, before, current, refresh, detect) if detect else _whole(r, before, current, refresh)
    _drop_record(folder, done.todo)
    steps = _reused(done, on_device)
    _run(done.run, done.todo)
    if done.apps is not None and done.todo["screen"]:
        write_used(folder, done.apps)
    _record(folder, identity, current, done)
    for stage in STAGES:
        echo(f"device {stage}: " + (f"ran: {steps[stage]}" if steps[stage] else "reused"))
    return DeviceStage(folder, steps)
