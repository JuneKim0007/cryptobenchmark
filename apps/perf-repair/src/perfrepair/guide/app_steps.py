"""The guide's steps for one app, in order; each returns its status detail or ends through terminate with its code."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..ai.select.command import select_units, select_upgrades, upgrade_counts
from ..inputs.table import APPS_REVIEW
from ..app.__main__ import main as app_main
from ..app.facts.gate import open_apps
from ..data_handler.outbound.benchmark_runner import run_pipeline
from ..device.bundled_config import harness_config
from ..device.missing_rows import measured_rows, site_rows, variant_rows
from ..dto.dossier import NOT_ON_DEVICE, NOT_ON_DEVICE_STEP
from ..dto.upgrade import UPGRADED
from ..repair.__main__ import main as repair_main
from ..repair.dossier import dossier
from ..report.command import app_report
from ..validation.finding import UNDECIDED, blocking
from ..validation.invariants import app_gate
from .state import Guide, check_exit, halt


def app(g: Guide) -> str:
    if g.app_id not in g.detected:
        # raises the gate's reason here: the command would only print it, and a run of many apps needs it in the app's line
        open_apps(g.app_root)
        try:
            check_exit(g, app_main(["--device-results", str(g.device), "--app", str(g.app_root)]), "app_failed",
                       "perfrepair.app")
        finally:
            # a not_on_device stop has written the app's files; its rows belong on the list it ends
            g.missing.put(f"sites {g.app_id}", site_rows(g.device, g.app_id))
    if not g.paths.scopes.is_file():
        halt(g, "several_project_roots", f"{g.app_root} holds several; pass one of them as --app")
    return f"{len(rd.read_scopes(g.paths.scopes)['scopes'])} scopes"


def dossiers(g: Guide) -> str:
    doc = dossier(g.device, g.app_id, g.app_root, g.catalog, g.mode.perf, echo=lambda _: None, max_change=g.max_change)
    g.missing.put(f"measured {g.app_id}", measured_rows(g.device, g.app_id))
    g.missing.put(f"variants {g.app_id}", variant_rows(g.device, g.app_id, doc["noOptions"]))
    if not doc["dossiers"] and not doc["upgrades"]:
        # a broken use with no option is still reported, and asks no model
        upgrades(g)
        reasons = sorted({n["reason"] for n in doc["noOptions"]})
        step = f"; {NOT_ON_DEVICE}: {NOT_ON_DEVICE_STEP}" if NOT_ON_DEVICE in reasons else ""
        halt(g, "no_options", f"none of {len(doc['noOptions'])} scopes has an option ({', '.join(reasons)}){step}")
    return f"{len(doc['dossiers'])} with options, {len(doc['noOptions'])} without"


def _review(g: Guide) -> bool:
    """apps.review from the run's settings; a guide built without settings asks no reviewer."""
    return bool(g.settings and g.settings.read(APPS_REVIEW))


def upgrades(g: Guide) -> str:
    return upgrade_counts(select_upgrades(g.device, g.app_id, g.conversations, g.library, g.limits, g.limit, echo=g.echo,
                                          review=_review(g)))


def replacements(g: Guide) -> str:
    found = app_gate(g.device, g.app_id, g.app_root)
    blocked, undecided = blocking(found), [v for v in found if v.severity == UNDECIDED]
    if blocked:
        halt(g, "invariant_failed", f"{len(blocked)} blocking: " + " | ".join(v.line() for v in blocked[:3]))
    if undecided:
        halt(g, "invariant_undecided", f"{len(undecided)} undecided: " + " | ".join(v.line() for v in undecided[:3]))
    state = select_units(g.device, g.app_id, g.conversations, g.library, g.limits, g.limit, echo=g.echo, review=_review(g))
    # a cap leaves units unasked: the app is not done, whatever its outcome
    asked = {d["scope"]["id"] for d in rd.read_dossiers(g.paths.dossiers)["dossiers"]}
    upgraded = rd.load_upgrades(g.paths.upgrades)
    wanted = {r["scope"]["id"] for r in rd.read_dossiers(g.paths.dossiers)["upgrades"]}
    g.unasked = len(asked - set(state.replacements)) + len(wanted - {u.scope for u in upgraded})
    chosen = sum(r.decision == "replace" for r in state.replacements.values()) + sum(u.status == UPGRADED for u in upgraded)
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


def device_config(g: Guide) -> Path | None:
    """The global.yaml the app's device step runs with; None: pipeline.py's own lookup."""
    return harness_config(g.device, g.app_config, g.paths.root) or g.config or g.base_config


def device(g: Guide) -> str:
    config = device_config(g)
    return str(run_pipeline(config, None, "device", harness=g.paths.harness, echo=g.echo, app=g.app_id, device=g.device))


def report(g: Guide) -> str:
    doc = app_report(g.device, g.app_id, g.mode, echo=lambda _: None)
    return f"{g.paths.report}: {doc['funnel']['interopPassed']} of {doc['funnel']['scopes']} scopes interop passed"


APP_DRY = (("app", app), ("dossier", dossiers), ("upgrade", upgrades), ("replace", replacements), ("edit", edits), ("harness", harness))
APP_DEVICE = (("device", device), ("report", report))
