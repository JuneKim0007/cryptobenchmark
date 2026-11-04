"""Pass: what one probe_device call reports and reruns, for the whole selection or, with detect, the targets' used set."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from .. import run_dir as rd
from ..data_handler.inbound import RunContext, read_manifest
from ..dto.bundled import entries_digest
from ..dto.event import END
from ..dto.grouping import read_items
from ..files import read_json
from ..log import emit, step
from ..run_dir import GroupingPaths
from .bundled import check_bundled
from .bundled_config import bundled_config, configured
from .plan import STAGES, Seen, mapped_inputs, plan
from .selection import FILTER_OFF, exclusions, lacking, measured, write_config
from .stage_run import Run, run_probe
from .used import write_used

# a device run installs and probes before it measures, so its probe is never the one already there
DEVICE_PROBES = "a device benchmark probes the device it measures"
NO_ITEM = "no target app reaches a device item: the base selection is measured"
APPLIED_CHANGED = "the providers.bundled entries device.bundled.fromApps applies changed"
BUNDLED_UNPROBED = "the probe does not hold the providers.bundled this run measures"


def _probe_current(r: Run, steps: dict, base: Path) -> dict:
    """The bundled step chooses providers after the first probe; items and groups must hold them before the used set."""
    harness = RunContext.load(r.folder / rd.MANIFEST).probe.harness_artifacts()
    if set(harness.values()) == set(configured(base)):
        return steps
    (r.folder / rd.DEVICE).unlink(missing_ok=True)
    run_probe(replace(r, config=base), {"probe": BUNDLED_UNPROBED, "screen": BUNDLED_UNPROBED})
    return {**steps, "probe": steps["probe"] or BUNDLED_UNPROBED, "screen": steps["screen"] or BUNDLED_UNPROBED}


def _measured_set(r: Run, keep: frozenset[str], base: Path) -> Path:
    with step("device", "selection") as s:
        paths = GroupingPaths(r.folder)
        items = read_items(read_json(paths.items))
        rules = exclusions(items, rd.load_screen(paths), keep)
        path = write_config(base, r.folder, rules)
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
    # the digest of the providers.bundled entries device.bundled.fromApps applied; None: none
    applied: str | None = None


def drop_record(folder: Path, steps: dict) -> None:
    # a record exists only while every stage it vouches for is whole, so an interrupted run reruns them
    if any(steps.values()):
        (folder / rd.DEVICE).unlink(missing_ok=True)


def whole_pass(r: Run, before: Seen, current: dict, refresh: bool) -> Pass:
    bundled_config(r.config, r.folder, [])
    steps = plan(before, current, refresh, {"benchmark": FILTER_OFF} if before.scoped else None)
    todo = with_device_probe(steps, steps, r.on_device)
    return Pass(todo, todo, r)


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


def scoped_pass(r: Run, before: Seen, current: dict, refresh: bool, detect: Callable[[Path], list[str]]) -> Pass:
    """Probe and screen first, so the apps resolve against today's items; then the used set, and the benchmark only for
    what it lacks."""
    steps = plan(before, current, refresh)
    drop_record(r.folder, steps)
    run_probe(r, steps)
    apps = detect(r.folder)
    entries = check_bundled(r.folder, apps, r.config, r.bundled, r.echo)
    applied = entries_digest(entries)
    base = bundled_config(r.config, r.folder, entries)
    steps = _probe_current(r, steps, base)
    used = write_used(r.folder, apps)
    manifest, _ = read_manifest(r.folder / rd.MANIFEST)
    lack = lacking(used.names, before.record, mapped_inputs(manifest.inputs, before.record).get("config"), current["config"])
    changed = APPLIED_CHANGED if applied != before.applied else None
    forced = lack or changed
    todo = _left(plan(before, current, refresh, {"benchmark": forced} if forced else None))
    keep = _keep(used.names, before, todo)
    config = _measured_set(r, keep, base) if keep else base
    reported = {s: steps[s] if s in ("probe", "screen") and steps[s] else todo[s] for s in STAGES}
    return Pass(reported, todo, replace(r, config=config, probed=True), keep, apps, before.kept, applied)


def with_device_probe(steps: dict, todo: dict, on_device: bool) -> dict:
    if on_device and todo["benchmark"] and not steps["probe"]:
        return {**steps, "probe": DEVICE_PROBES}
    return steps
