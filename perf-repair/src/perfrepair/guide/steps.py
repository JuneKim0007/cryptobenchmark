"""The guide's steps for one app, in order; each returns its status detail or raises Stop with a coded reason."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt import PromptLibrary
from ..ai.parse.grouping_assign.rekey import rekey
from ..ai.suggest.site_replace.command import replace
from ..app.__main__ import main as app_main
from ..app.facts.gate import open_apps
from ..app.facts.path_id import path_id
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..device.coverage import Coverage, coverage, no_rerun
from ..device.stage import probe_device
from ..dto.event import END
from ..dto.site import NOT_ON_DEVICE, NOT_ON_DEVICE_STEP
from ..files import read_json
from ..grouping.__main__ import main as grouping_main
from ..log import emit, step
from ..run_dir import GroupingPaths
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report, device_summary
from ..result.modes import Mode
from ..config.load import Loaded
from ..screen.catalog import Catalog, CatalogMismatch, screening_catalog

INBOUND = "python3 -m perfrepair.data_handler.inbound --device-results <device>"
GROUPING = ("python3 -m perfrepair.grouping build --device-results <device>, then "
            "`grouping assign --device-results <device>` and `grouping report --device-results <device>`")
NAMED = "or leave --device-results and device.id unset so the guide makes the device stage itself"


class Stop(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


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
    settings: Loaded | None = None
    echo: Callable[[str], None] = print
    catalog: Catalog | None = None
    root: Path | None = None
    on_device: bool = False
    grouping_args: tuple[str, ...] = ()

    @property
    def app_id(self) -> str | None:
        return path_id(self.app_root) if self.app_root else None

    @property
    def paths(self) -> rd.AppPaths:
        return rd.AppPaths(self.device, self.app_id)


def _exit(code: int, stop: str, what: str) -> None:
    if code != 0:
        raise Stop(stop, f"{what} exited {code}; its own lines above say why")


def prerequisites(g: Guide) -> str:
    # resolved and checked before any step runs, so a bad catalog stops the guide first
    g.catalog = screening_catalog(g.settings)
    if g.root is not None:
        g.device = probe_device(g.root, g.catalog, g.config, g.on_device, echo=g.echo).folder
    if not (g.device / rd.MANIFEST).is_file():
        raise Stop("missing_results", f"{g.device / rd.MANIFEST} absent; --device-results is a folder cryptobenchmark wrote")
    for path in (g.device / rd.ROWS, g.device / rd.MEASUREMENTS):
        if not path.is_file():
            raise Stop("missing_device_stage", f"{path} absent; inbound is a device-level stage, made once per device: "
                                               f"{INBOUND}, {NAMED}")
    problems = g.catalog.mismatch(rd.load_screen_catalog(GroupingPaths(g.device)))
    if problems:
        raise CatalogMismatch(problems[0])
    return f"device results {g.device}, catalog {g.catalog.source}"


def _no_decision(what: str) -> Stop:
    return Stop("missing_device_stage", f"{what}; grouping is a device-level stage, made once per device: {GROUPING}, {NAMED}")


def _regroup(g: Guide, seen: Coverage, every: bool) -> str:
    with step("device", "grouping") as s:
        if every or seen.pending:
            _exit(grouping_main(["assign", "--device-results", str(g.device), *g.grouping_args, *(("--refresh",) if every else ())]),
                  "grouping_failed", "grouping assign")
        _exit(grouping_main(["report", "--device-results", str(g.device), *g.grouping_args]), "grouping_failed", "grouping report")
        s.outcome = "ran"
        s.count(items=seen.asked, asked=seen.asked if every else len(seen.pending))
    if every:
        return f"ran: device.grouping.noRerun false, all {seen.asked} items asked again"
    return f"ran: {len(seen.pending)} of {seen.asked} items asked" if seen.pending else "rebuilt from the kept decisions, no item asked"


def grouping(g: Guide) -> str:
    """The guide's one device-level model step: only what coverage finds missing is asked."""
    paths = GroupingPaths(g.device)
    if not paths.items.is_file() and g.root is None:
        raise _no_decision(f"{paths.items} absent")
    rekey(paths, g.library)
    seen, every = coverage(paths), not no_rerun(g.settings)
    if seen.current and not every:
        emit("device", "grouping", END, outcome="reused", data={"counts": {"items": seen.asked}})
        return "reused"
    if seen.pending and g.root is None and not every:
        raise _no_decision(f"{len(seen.pending)} of {seen.asked} items have no decision")
    return _regroup(g, seen, every)


def app(g: Guide) -> str:
    # raises the gate's reason here: the command would only print it, and a run of many apps needs it in the app's line
    open_apps(g.app_root)
    _exit(app_main(["--device-results", str(g.device), "--app", str(g.app_root)]), "app_failed", "perfrepair.app")
    if not g.paths.scopes.is_file():
        raise Stop("several_project_roots", f"{g.app_root} holds several; pass one of them as --app")
    return f"{len(read_json(g.paths.scopes)['scopes'])} scopes"


def dossiers(g: Guide) -> str:
    doc = dossier(g.device, g.app_id, g.app_root, g.catalog, echo=lambda _: None)
    if not doc["dossiers"]:
        reasons = sorted({n["reason"] for n in doc["noOptions"]})
        step = f"; {NOT_ON_DEVICE}: {NOT_ON_DEVICE_STEP}" if NOT_ON_DEVICE in reasons else ""
        raise Stop("no_options", f"none of {len(doc['noOptions'])} scopes has an option ({', '.join(reasons)}){step}")
    return f"{len(doc['dossiers'])} with options, {len(doc['noOptions'])} without"


def replacements(g: Guide) -> str:
    state = replace(g.device, g.app_id, g.conversations, g.library, g.limits, g.limit, echo=g.echo)
    chosen = sum(r.decision == "replace" for r in state.replacements.values())
    if not chosen:
        raise Stop("no_replacement", f"every one of {len(state.replacements)} scopes is kept")
    return f"{chosen} replace of {len(state.replacements)}"


def edits(g: Guide) -> str:
    _exit(repair_main(["edit", "--device-results", str(g.device), "--app", str(g.app_root)]),
          "edit_invalid", "repair edit")
    rows = read_json(g.paths.edits)["edits"]
    applied = sum(e["status"] == "applied" for e in rows)
    if not applied:
        reasons = sorted({e["reason"] for e in rows})
        raise Stop("no_edit_applied", f"{len(rows)} replacements, every edit rejected ({', '.join(reasons)})")
    return f"{applied} of {len(rows)} applied"


def harness(g: Guide) -> str:
    _exit(repair_main(["harness", "--device-results", str(g.device), "--app", str(g.app_root)]),
          "harness_invalid", "repair harness")
    return str(g.paths.harness)


def device(g: Guide) -> str:
    manifest = run_pipeline(g.config, g.paths.root, "device", harness=g.paths.harness, echo=g.echo)
    return str(manifest)


def report(g: Guide) -> str:
    doc = app_report(g.device, g.app_id, g.mode, echo=lambda _: None)
    return f"{g.paths.report}: {doc['funnel']['measured']} of {doc['funnel']['scopes']} scopes measured"


def summary(g: Guide) -> str:
    if not any((d / rd.REPORT).is_file() for d in rd.app_dirs(g.device)):
        return "no app has a report yet"
    doc = device_summary(g.device, echo=lambda _: None)
    return f"{g.device / rd.SUMMARY}: {len(doc['apps'])} apps, {doc['funnel']['measured']} scopes measured"


DEVICE_LEVEL = (("prerequisites", prerequisites), ("grouping", grouping))
APP_DRY = (("app", app), ("dossier", dossiers), ("replace", replacements), ("edit", edits), ("harness", harness))
APP_MEASURED = (("device", device), ("report", report))
