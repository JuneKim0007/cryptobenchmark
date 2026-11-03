"""The guide's steps for one app, in order; each returns its status detail or ends through terminate with its code."""
from __future__ import annotations

from dataclasses import dataclass, field, replace as with_fields
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt import PromptLibrary
from ..ai.parse.grouping_assign.rekey import rekey
from ..ai.suggest.site_replace.command import replace, stale_problem
from ..app.__main__ import main as app_main
from ..app.facts.gate import open_apps
from ..app.facts.path_id import path_id
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..device.bundled_config import harness_config
from ..device.coverage import Coverage, coverage, no_rerun
from ..device.energy import report_invalid
from ..device.stage import probe_device
from ..device.used import clear_used, write_used
from ..dto.bundled import BundledPolicy
from ..dto.change import DROP_IN
from ..dto.event import END
from ..dto.site import NOT_ON_DEVICE, NOT_ON_DEVICE_STEP
from ..failure import FAILURES, last_failure
from ..files import read_json
from ..grouping.__main__ import main as grouping_main
from ..log import emit, step
from ..run_dir import GroupingPaths
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report, device_summary
from ..result.modes import Mode
from ..review.sheet import write_sheet
from ..config.load import Loaded
from ..screen.catalog import Catalog, screening_catalog
from ..stop import terminate

INBOUND = "python3 -m perfrepair.data_handler.inbound --device-results <device>"
GROUPING = ("python3 -m perfrepair.grouping build --device-results <device>, then "
            "`grouping assign --device-results <device>` and `grouping report --device-results <device>`")
NAMED = "or leave --device-results and device.id unset so the guide makes the device stage itself"


@dataclass
class Guide:
    """device: the named device folder; with root instead, prerequisites makes it by probe_device() and sets it.
    app_root: None for the device-level steps, which run once before the apps."""
    device: Path | None
    app_root: Path | None
    mode: Mode
    conversations: Conversations
    library: PromptLibrary
    limits: Limits = Limits()
    limit: int | None = None
    config: Path | None = None
    # the per-app device step; None uses config
    app_config: Path | None = None
    settings: Loaded | None = None
    echo: Callable[[str], None] = print
    catalog: Catalog | None = None
    root: Path | None = None
    on_device: bool = False
    grouping_args: tuple[str, ...] = ()
    refresh: bool = False
    targets: tuple[Path, ...] = ()
    # the command sets it from device.filterByApps
    filter_by_apps: bool = False
    # the command sets it from device.bundled
    bundled: BundledPolicy = BundledPolicy()
    # app ids whose app step ran before the benchmark, shared by every app's copy
    detected: set = field(default_factory=set)
    max_change: str = DROP_IN
    # the running step's name, set by run_step, so a stop's line says where
    step: str | None = None

    @property
    def app_id(self) -> str | None:
        return path_id(self.app_root) if self.app_root else None

    @property
    def paths(self) -> rd.AppPaths:
        return rd.AppPaths(self.device, self.app_id)


def halt(g: Guide, code: str, detail: str, inner: str | None = None) -> None:
    terminate(code, detail, stage="guide", step=g.step or "guide", app=g.app_id, inner=inner)


def _exit(g: Guide, code: int, stop: str, what: str) -> None:
    """A command run in-process wrote no error event: its coded failure is the inner code of this one line."""
    if code != 0:
        inner = last_failure()
        said = f": {inner.detail}" if inner and inner.detail else "; its own lines above say why"
        halt(g, stop, f"{what} exited {code}" + said, inner.code if inner else None)


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


def prerequisites(g: Guide) -> str:
    # resolved and checked before any step runs, so a bad catalog stops the guide first
    g.catalog = screening_catalog(g.settings)
    if g.root is not None:
        detect = (lambda folder: detect_targets(g, folder)) if g.filter_by_apps else None
        # named: a stop inside it still finds the folder its log goes to
        g.device = probe_device(g.root, g.catalog, g.config, g.on_device, echo=g.echo, refresh=g.refresh,
                                detect=detect, perf=g.mode.perf, bundled=g.bundled,
                                named=lambda folder: setattr(g, "device", folder)).folder
    if not (g.device / rd.MANIFEST).is_file():
        halt(g, "missing_results", f"{g.device / rd.MANIFEST} absent; --device-results is a folder cryptobenchmark wrote")
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
            _exit(g, grouping_main(["assign", "--device-results", str(g.device), *g.grouping_args,
                                    *(("--refresh",) if every else ())]), "grouping_failed", "grouping assign")
        _exit(g, grouping_main(["report", "--device-results", str(g.device), *g.grouping_args]), "grouping_failed",
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
    if seen.pending and g.root is None and not every:
        _no_decision(g, f"{len(seen.pending)} of {seen.asked} items have no decision")
    return _regroup(g, seen, every)


def app(g: Guide) -> str:
    if g.app_id not in g.detected:
        # raises the gate's reason here: the command would only print it, and a run of many apps needs it in the app's line
        open_apps(g.app_root)
        _exit(g, app_main(["--device-results", str(g.device), "--app", str(g.app_root)]), "app_failed",
              "perfrepair.app")
    if not g.paths.scopes.is_file():
        halt(g, "several_project_roots", f"{g.app_root} holds several; pass one of them as --app")
    return f"{len(read_json(g.paths.scopes)['scopes'])} scopes"


def dossiers(g: Guide) -> str:
    doc = dossier(g.device, g.app_id, g.app_root, g.catalog, g.mode.perf, echo=lambda _: None, max_change=g.max_change)
    if not doc["dossiers"]:
        reasons = sorted({n["reason"] for n in doc["noOptions"]})
        step = f"; {NOT_ON_DEVICE}: {NOT_ON_DEVICE_STEP}" if NOT_ON_DEVICE in reasons else ""
        halt(g, "no_options", f"none of {len(doc['noOptions'])} scopes has an option ({', '.join(reasons)}){step}")
    return f"{len(doc['dossiers'])} with options, {len(doc['noOptions'])} without"


def replacements(g: Guide) -> str:
    state = replace(g.device, g.app_id, g.conversations, g.library, g.limits, g.limit, echo=g.echo, refresh=g.refresh)
    stale = stale_problem(state)
    if stale:
        halt(g, "dossier_changed", stale.split(": ", 1)[1] + " (guide --refresh)")
    chosen = sum(r.decision == "replace" for r in state.replacements.values())
    if not chosen:
        halt(g, "no_replacement", f"every one of {len(state.replacements)} scopes is kept")
    return f"{chosen} replace of {len(state.replacements)}"


def edits(g: Guide) -> str:
    _exit(g, repair_main(["edit", "--device-results", str(g.device), "--app", str(g.app_root)]), "edit_invalid",
          "repair edit")
    rows = read_json(g.paths.edits)["edits"]
    applied = sum(e["status"] == "applied" for e in rows)
    if not applied:
        reasons = sorted({e["reason"] for e in rows})
        halt(g, "no_edit_applied", f"{len(rows)} replacements, every edit rejected ({', '.join(reasons)})")
    return f"{applied} of {len(rows)} applied"


def harness(g: Guide) -> str:
    _exit(g, repair_main(["harness", "--device-results", str(g.device), "--app", str(g.app_root)]), "harness_invalid",
          "repair harness")
    return str(g.paths.harness)


def device(g: Guide) -> str:
    config = harness_config(g.device, g.app_config, g.paths.root) or g.config
    manifest = run_pipeline(config, None, "device", harness=g.paths.harness, echo=g.echo, app=g.app_id, device=g.device)
    invalid = report_invalid(manifest, g.app_id)
    return str(manifest) + (f", {invalid} energy cases invalid" if invalid else "")


def report(g: Guide) -> str:
    doc = app_report(g.device, g.app_id, g.mode, echo=lambda _: None)
    return f"{g.paths.report}: {doc['funnel']['measured']} of {doc['funnel']['scopes']} scopes measured"


def summary(g: Guide) -> str:
    # the accuracy sheet covers every decision this run made, also when no app reached its report
    write_sheet(g.device)
    if not any((d / rd.REPORT).is_file() for d in rd.app_dirs(g.device)):
        return "no app has a report yet"
    doc = device_summary(g.device, echo=lambda _: None)
    return f"{g.device / rd.SUMMARY}: {len(doc['apps'])} apps, {doc['funnel']['measured']} scopes measured"


DEVICE_LEVEL = (("prerequisites", prerequisites), ("grouping", grouping))
APP_DRY = (("app", app), ("dossier", dossiers), ("replace", replacements), ("edit", edits), ("harness", harness))
APP_MEASURED = (("device", device), ("report", report))
