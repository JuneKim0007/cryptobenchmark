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
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..files import read_json
from ..grouping.paths import GroupingPaths
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report
from ..result.modes import Mode

MANIFEST = "manifest.yaml"
INBOUND = "python3 -m perfrepair.data_handler.inbound --manifest <results>/manifest.yaml -o <run>"
GROUPING = ("python3 -m perfrepair.grouping build --manifest <results>/manifest.yaml --run <run>, then "
            "`grouping assign --run <run>` and `grouping report --run <run>`")


class Stop(Exception):
    def __init__(self, code: str, detail: str):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}")


@dataclass
class Guide:
    run: Path
    app_root: Path
    name: str
    results: Path
    mode: Mode
    conversations: Conversations
    library: PromptLibrary
    limits: Limits = Limits()
    limit: int | None = None
    config: Path | None = None
    echo: Callable[[str], None] = print

    @property
    def paths(self) -> rd.AppPaths:
        return rd.AppPaths(self.run, self.name)


def _exit(code: int, stop: str, what: str) -> None:
    if code != 0:
        raise Stop(stop, f"{what} exited {code}; its own lines above say why")


def prerequisites(g: Guide) -> str:
    rd.app_dir(g.run, g.name)
    if not (g.results / MANIFEST).is_file():
        raise Stop("missing_results", f"{g.results / MANIFEST} absent; --results is a cryptobenchmark results directory")
    for path, how in ((g.run / rd.ROWS, INBOUND), (g.run / rd.MEASUREMENTS, INBOUND),
                      (GroupingPaths(g.run).groups, GROUPING)):
        if not path.is_file():
            raise Stop("missing_run_stage", f"{path} absent; inbound and grouping are run-level stages, made once "
                                            f"per run: {how}")
    return f"run {g.run}, results {g.results}"


def app(g: Guide) -> str:
    _exit(app_main(["--manifest", str(g.results / MANIFEST), "--app", str(g.app_root), "--run", str(g.run),
                    "--name", g.name]), "app_failed", "perfrepair.app")
    return f"{len(read_json(g.paths.scopes)['scopes'])} scopes"


def dossiers(g: Guide) -> str:
    doc = dossier(g.run, g.name, g.app_root, echo=lambda _: None)
    if not doc["dossiers"]:
        reasons = sorted({n["reason"] for n in doc["noOptions"]})
        raise Stop("no_options", f"none of {len(doc['noOptions'])} scopes has an option ({', '.join(reasons)})")
    return f"{len(doc['dossiers'])} with options, {len(doc['noOptions'])} without"


def replacements(g: Guide) -> str:
    state = replace(g.run, g.name, g.conversations, g.library, g.limits, g.limit, echo=g.echo)
    chosen = sum(r.decision == "replace" for r in state.replacements.values())
    if not chosen:
        raise Stop("no_replacement", f"every one of {len(state.replacements)} scopes is kept")
    return f"{chosen} replace of {len(state.replacements)}"


def edits(g: Guide) -> str:
    _exit(repair_main(["edit", "--run", str(g.run), "--app", g.name, "--source", str(g.app_root)]),
          "edit_invalid", "repair edit")
    rows = read_json(g.paths.edits)["edits"]
    applied = sum(e["status"] == "applied" for e in rows)
    if not applied:
        reasons = sorted({e["reason"] for e in rows})
        raise Stop("no_edit_applied", f"{len(rows)} replacements, every edit rejected ({', '.join(reasons)})")
    return f"{applied} of {len(rows)} applied"


def harness(g: Guide) -> str:
    _exit(repair_main(["harness", "--run", str(g.run), "--app", g.name]), "harness_invalid", "repair harness")
    return str(g.paths.harness)


def device(g: Guide) -> str:
    manifest = run_pipeline(g.config, g.paths.measured, "device", extra_args=["--harness", str(g.paths.harness)],
                            echo=g.echo)
    return str(manifest)


def report(g: Guide) -> str:
    doc = app_report(g.run, g.name, g.mode, echo=lambda _: None)
    return f"{g.paths.report}: {doc['funnel']['measured']} of {doc['funnel']['scopes']} scopes measured"


DRY = (("prerequisites", prerequisites), ("app", app), ("dossier", dossiers), ("replace", replacements),
       ("edit", edits), ("harness", harness))
DEVICE = (("device", device), ("report", report))
