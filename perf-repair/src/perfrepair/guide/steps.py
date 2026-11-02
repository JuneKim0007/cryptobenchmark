"""The guide's steps for one app, in order; each returns its status detail or raises Stop with a coded reason."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.prompt import PromptLibrary
from ..ai.suggest.site_replace.command import replace
from ..app.__main__ import main as app_main
from ..app.path_id import path_id
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..files import read_json
from ..run_dir import GroupingPaths
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report
from ..result.modes import Mode
from ..config.load import Loaded
from ..screen.catalog import Catalog, CatalogMismatch, screening_catalog

INBOUND = "python3 -m perfrepair.data_handler.inbound --device-results <device>"
GROUPING = ("python3 -m perfrepair.grouping build --device-results <device>, then "
            "`grouping assign --device-results <device>` and `grouping report --device-results <device>`")


class Stop(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


@dataclass
class Guide:
    device: Path
    app_root: Path
    mode: Mode
    conversations: Conversations
    library: PromptLibrary
    limits: Limits = Limits()
    limit: int | None = None
    config: Path | None = None
    settings: Loaded | None = None
    echo: Callable[[str], None] = print
    catalog: Catalog | None = None

    @property
    def app_id(self) -> str:
        return path_id(self.app_root)

    @property
    def paths(self) -> rd.AppPaths:
        return rd.AppPaths(self.device, self.app_id)


def _exit(code: int, stop: str, what: str) -> None:
    if code != 0:
        raise Stop(stop, f"{what} exited {code}; its own lines above say why")


def prerequisites(g: Guide) -> str:
    if not (g.device / rd.MANIFEST).is_file():
        raise Stop("missing_results", f"{g.device / rd.MANIFEST} absent; --device-results is a folder cryptobenchmark wrote")
    for path, how in ((g.device / rd.ROWS, INBOUND), (g.device / rd.MEASUREMENTS, INBOUND),
                      (GroupingPaths(g.device).groups, GROUPING)):
        if not path.is_file():
            raise Stop("missing_device_stage", f"{path} absent; inbound and grouping are device-level stages, made once "
                                               f"per device: {how}")
    # resolved and checked before any step runs, so a bad catalog stops the guide first
    g.catalog = screening_catalog(g.settings)
    problems = g.catalog.mismatch(rd.load_screen_catalog(GroupingPaths(g.device)))
    if problems:
        raise CatalogMismatch(problems[0])
    return f"device results {g.device}, catalog {g.catalog.source}"


def app(g: Guide) -> str:
    _exit(app_main(["--device-results", str(g.device), "--app", str(g.app_root)]), "app_failed", "perfrepair.app")
    if not g.paths.scopes.is_file():
        raise Stop("several_project_roots", f"{g.app_root} holds several; pass one of them as --app")
    return f"{len(read_json(g.paths.scopes)['scopes'])} scopes"


def dossiers(g: Guide) -> str:
    doc = dossier(g.device, g.app_id, g.app_root, g.catalog, echo=lambda _: None)
    if not doc["dossiers"]:
        reasons = sorted({n["reason"] for n in doc["noOptions"]})
        raise Stop("no_options", f"none of {len(doc['noOptions'])} scopes has an option ({', '.join(reasons)})")
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


DRY = (("prerequisites", prerequisites), ("app", app), ("dossier", dossiers), ("replace", replacements),
       ("edit", edits), ("harness", harness))
DEVICE = (("device", device), ("report", report))
