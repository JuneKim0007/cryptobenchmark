"""The guide's steps for one app, in order; each returns its status detail or ends through terminate with its code."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.suggest.site_replace.command import replace, stale_problem
from ..app.__main__ import main as app_main
from ..app.facts.gate import open_apps
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..device.bundled_config import harness_config
from ..device.energy import report_invalid
from ..dto.dossier import NOT_ON_DEVICE, NOT_ON_DEVICE_STEP
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report
from .state import Guide, check_exit, halt


def app(g: Guide) -> str:
    if g.app_id not in g.detected:
        # raises the gate's reason here: the command would only print it, and a run of many apps needs it in the app's line
        open_apps(g.app_root)
        check_exit(g, app_main(["--device-results", str(g.device), "--app", str(g.app_root)]), "app_failed",
                   "perfrepair.app")
    if not g.paths.scopes.is_file():
        halt(g, "several_project_roots", f"{g.app_root} holds several; pass one of them as --app")
    return f"{len(rd.read_scopes(g.paths.scopes)['scopes'])} scopes"


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
    # a cap leaves units unasked: the app is not done, whatever its outcome
    asked = {d["scope"]["id"] for d in rd.read_dossiers(g.paths.dossiers)["dossiers"]}
    g.unasked = len(asked - set(state.replacements))
    chosen = sum(r.decision == "replace" for r in state.replacements.values())
    if not chosen:
        halt(g, "no_replacement", f"every one of {len(state.replacements)} scopes is kept")
    return f"{chosen} replace of {len(state.replacements)}"


def edits(g: Guide) -> str:
    check_exit(g, repair_main(["edit", "--device-results", str(g.device), "--app", str(g.app_root)]), "edit_invalid",
               "repair edit")
    rows = rd.read_edits(g.paths.edits)["edits"]
    applied = sum(e["status"] == "applied" for e in rows)
    if not applied:
        reasons = sorted({e["reason"] for e in rows})
        halt(g, "no_edit_applied", f"{len(rows)} replacements, every edit rejected ({', '.join(reasons)})")
    return f"{applied} of {len(rows)} applied"


def harness(g: Guide) -> str:
    check_exit(g, repair_main(["harness", "--device-results", str(g.device), "--app", str(g.app_root)]), "harness_invalid",
               "repair harness")
    return str(g.paths.harness)


def measured_config(g: Guide) -> Path | None:
    """The global.yaml the app's device step runs with; None: pipeline.py's own lookup."""
    return harness_config(g.device, g.app_config, g.paths.root) or g.config


def device(g: Guide) -> str:
    config = measured_config(g)
    manifest = run_pipeline(config, None, "device", harness=g.paths.harness, echo=g.echo, app=g.app_id, device=g.device)
    invalid = report_invalid(manifest, g.app_id)
    return str(manifest) + (f", {invalid} energy cases invalid" if invalid else "")


def report(g: Guide) -> str:
    doc = app_report(g.device, g.app_id, g.mode, echo=lambda _: None)
    return f"{g.paths.report}: {doc['funnel']['measured']} of {doc['funnel']['scopes']} scopes measured"


APP_DRY = (("app", app), ("dossier", dossiers), ("replace", replacements), ("edit", edits), ("harness", harness))
APP_MEASURED = (("device", device), ("report", report))
