"""The guide's device-level steps, once per device: prerequisites (the probe and the used set), targets, grouping, the
summary."""
from __future__ import annotations

from dataclasses import replace as with_fields
from pathlib import Path

from .. import run_dir as rd
from ..ai.parse.grouping_assign.rekey import rekey
from ..device.coverage import Coverage, coverage, no_rerun
from ..device.missing_rows import measured_rows
from ..device.stage import probe_device
from ..device.used import clear_used, write_used
from ..dto.coded import InputError
from ..dto.event import END
from ..dto.metrics import METRICS, Metric
from ..dto.perf_mode import PerfMode
from ..failure import FAILURES
from ..files import sha256_file
from ..grouping.__main__ import main as grouping_main
from ..log import emit, step
from ..report.command import device_summary
from ..review.sheet import write_sheet
from ..run_dir import GroupingPaths
from ..run_dir.run_record import RunRecord
from ..screen.catalog import screening_catalog
from .app_steps import app
from .index import write_index
from .state import Guide, check_exit, halt
from .target_file import write_targets

INBOUND = "python3 -m perfrepair.data_handler.inbound --device-results <device>"
GROUPING = ("python3 -m perfrepair.grouping build --device-results <device>, then "
            "`grouping assign --device-results <device>` and `grouping report --device-results <device>`")
NAMED = "or leave --device-results and device.id unset so the guide makes the device stage itself"


def detect_targets(g: Guide, device: Path) -> list[str]:
    """Each target's app step on the probe, before the benchmark; one that fails stops later at its own app step."""
    g.device, found = device, []
    for root in g.targets:
        one = with_fields(g, app_root=root)
        try:
            detail = app(one) if root.is_dir() else None
        except FAILURES as e:
            emit("guide", "detect", END, app=one.app_id, outcome="stop", detail=str(e))
            continue
        if detail is not None:
            g.detected.add(one.app_id)
            found.append(one.app_id)
            emit("guide", "detect", END, app=one.app_id, outcome="ok", detail=detail)
    return found


def _used(g: Guide) -> str:
    if not g.filter_by_apps:
        clear_used(g.device)
        return ""
    if g.root is None and not GroupingPaths(g.device).items.is_file():
        return ""
    used = write_used(g.device, detect_targets(g, g.device)) if g.root is None else rd.load_used(g.device)
    return f", used set {len(used.items)} of {used.deviceItems} items for {len(used.apps)} app folders"


def _modes(g: Guide) -> list[PerfMode]:
    return [g.app_modes.get(r, g.mode).perf for r in g.targets] or [g.mode.perf]


def _measured(g: Guide) -> PerfMode:
    """What the one benchmark must measure: every key of every target's own perfMode."""
    modes = _modes(g)
    return modes[0] if len({m.name for m in modes}) == 1 else PerfMode.union(modes)


def _required(g: Guide) -> tuple[Metric, ...]:
    """A union reads as a strict list; only the targets that are strict make a metric required."""
    modes = _modes(g)
    return tuple(m for m in METRICS if any(m in mode.required for mode in modes))


def open_record(g: Guide, folder: Path) -> None:
    """The run's record on the folder, once: its lock taken and --on-existing applied before any stage reads it."""
    g.device = folder
    if g.record is not None:
        return
    config = {"config": sha256_file(g.config) if g.config else None,
              "settings": sha256_file(g.settings.file) if g.settings and g.settings.file else None}
    try:
        g.record = RunRecord.open(folder, g.run_id, g.on_existing, {**config, "screening": g.catalog.sha256},
                                  g.run_settings)
    except InputError as e:
        if e.code not in ("run_exists", "device_busy"):
            raise
        halt(g, e.code, str(e).split(": ", 1)[1])
    g.missing.open(folder)


def prerequisites(g: Guide) -> str:
    # resolved and checked before any step runs, so a bad catalog stops the guide first
    g.catalog = screening_catalog(g.settings)
    if g.root is not None:
        detect = (lambda folder: detect_targets(g, folder)) if g.filter_by_apps else None
        # named: a stop inside it still finds the folder its log goes to
        made = probe_device(g.root, g.catalog, g.config, g.on_device, echo=g.echo, refresh=g.refresh,
                            detect=detect, perf=_measured(g), required=_required(g), bundled=g.bundled,
                            named=lambda folder: open_record(g, folder), missing=g.missing)
        g.device, g.base_config = made.folder, made.config
        for app_id in sorted(g.detected):
            g.missing.put(f"measured {app_id}", measured_rows(g.device, app_id))
    if not (g.device / rd.MANIFEST).is_file():
        halt(g, "missing_results", f"{g.device / rd.MANIFEST} absent; --device-results is a folder cryptobenchmark wrote")
    open_record(g, g.device)
    for path in (g.device / rd.ROWS, g.device / rd.MEASUREMENTS):
        if not path.is_file():
            halt(g, "missing_device_stage", f"{path} absent; inbound is a device-level stage, made once per device: "
                                            f"{INBOUND}, {NAMED}")
    problems = g.catalog.mismatch(rd.load_screen_catalog(GroupingPaths(g.device)))
    if problems:
        halt(g, "screening_catalog_mismatch", problems[0].split(": ", 1)[1])
    return f"device results {g.device}, catalog {g.catalog.source}" + _used(g)


REUSED_GROUPING = "every item decided, saved files current"


def _no_decision(g: Guide, what: str) -> None:
    halt(g, "missing_device_stage", f"{what}; grouping is a device-level stage, made once per device: {GROUPING}, {NAMED}")


def _regroup(g: Guide, seen: Coverage, every: bool) -> str:
    unused = "" if seen.not_used is None else f", {seen.not_used} not used by the targets"
    if every:
        said = f"ran: device.grouping.noRerun false, all {seen.asked} items asked again{unused}"
    elif seen.pending:
        said = f"ran: {len(seen.pending)} of {seen.asked} items asked{unused}"
    else:
        said = f"rebuilt from the kept decisions, no item asked{unused}"
    with step("device", "grouping") as s:
        if every or seen.pending:
            check_exit(g, grouping_main(["assign", "--device-results", str(g.device), *g.grouping_args,
                                         *(("--refresh",) if every else ())]), "grouping_failed", "grouping assign")
        check_exit(g, grouping_main(["report", "--device-results", str(g.device), *g.grouping_args]), "grouping_failed",
                   "grouping report")
        s.outcome, s.detail = "ran", said.removeprefix("ran: ")
        s.count(items=seen.asked, asked=seen.asked if every else len(seen.pending), **_not_used(seen))
    return said


def _not_used(seen: Coverage) -> dict:
    return {} if seen.not_used is None else {"notUsed": seen.not_used}


def grouping(g: Guide) -> str:
    """The guide's one device-level model step: only what coverage finds missing is asked."""
    paths = GroupingPaths(g.device)
    if not paths.items.is_file() and g.root is None:
        _no_decision(g, f"{paths.items} absent")
    rekey(paths, g.library)
    seen, every = coverage(paths), not no_rerun(g.settings)
    if seen.current and not every:
        emit("device", "grouping", END, outcome="reused", detail=REUSED_GROUPING,
             data={"counts": {"items": seen.asked, **_not_used(seen)}})
        return "reused"
    return _regroup(g, seen, every)


def summary(g: Guide) -> str:
    # the accuracy sheet covers every decision this run made, also when no app reached its report
    write_sheet(g.device)
    write_index(g.device)
    if not any((d / rd.REPORT).is_file() for d in rd.app_dirs(g.device)):
        return "no app has a report yet"
    doc = device_summary(g.device, echo=lambda _: None)
    return f"{g.device / rd.SUMMARY}: {len(doc['apps'])} apps, {doc['funnel']['measured']} scopes measured"


DEVICE_LEVEL = (("prerequisites", prerequisites), ("targets", write_targets), ("grouping", grouping))
# target detect, used set, benchmark, inbound: prerequisites alone calls no model
DEVICE_STAGE = DEVICE_LEVEL[:1]
