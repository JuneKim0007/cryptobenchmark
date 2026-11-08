"""<device>/<app>/: every step's file → report.json: a row per scope and the app's funnel. A step whose file is absent
is `not_run`; sites.json and scopes.json are required."""
from __future__ import annotations

from ..dto.report import BROKEN_USES, SCHEMA_VERSION, stayed, unit_counts
from ..dto.unit import read_units, units_by_scope
from ..dto.upgrade import STATUSES as UPGRADE_STATUSES, UPGRADED
from ..files import read_json, read_yaml
from ..result.modes import Mode
from ..app.facts.project import project_name
from ..run_dir import AppPaths, load_upgrades, read_scopes, read_sites
from ..stop.halt import Coded
from .device_check import read_device_check
from .recommendations import recommendations
from .scope_row import scope_row


def _optional(path, read=read_json) -> dict | None:
    return read(path) if path.is_file() else None


def funnel(sites: int, rows: list[dict], with_options: int) -> dict:
    units = unit_counts(rows)
    return {"sites": sites, "scopes": len(rows), "units": units["units"], "withOptions": with_options,
            "recommend": sum(r["decision"]["decision"] == "recommend" for r in rows),
            "replace": sum(r["decision"]["decision"] == "replace" for r in rows), "unitsReplace": units["unitsReplace"],
            "applied": sum(r["edit"]["status"] == "applied" for r in rows),
            "compiled": sum(r["compile"]["status"] == "compiled" for r in rows),
            "interopPassed": sum(r["interop"]["status"] == "passed" for r in rows)}


def _with_units(rows: list[dict], of_unit: dict) -> list[dict]:
    rows = [{**r, "unit": of_unit[r["scope"]].id, "sharedFunction": list(of_unit[r["scope"]].sharedFunction)} for r in rows]
    stays = stayed(rows)
    return [{**r, "stayed": stays[r["unit"]]} for r in rows]


def _named(paths: AppPaths) -> dict:
    """The project and source beside the id: two projects can share a last folder name."""
    doc = _optional(paths.facts) or {}
    root = doc.get("root")
    return {"project": project_name(root) if root else paths.app, "source": root}


def _broken_uses(upgrades: list, scopes: list[dict]) -> dict:
    """Each broken use found and what it became, a count per status."""
    sites = {s["id"]: s for s in scopes}
    rows = [{**u.to_json(), "file": sites[u.scope]["file"], "line": sites[u.scope]["line"], "function": sites[u.scope]["function"]}
            for u in sorted(upgrades, key=lambda u: (sites[u.scope]["file"], sites[u.scope]["line"], u.scope))]
    return {"counts": {s: sum(r["status"] == s for r in rows) for s in UPGRADE_STATUSES}, "rows": rows}


def build_report(paths: AppPaths, mode: Mode) -> dict:
    for required in (paths.sites, paths.scopes, paths.units):
        if not required.is_file():
            raise Coded(f"missing_step: {required} absent; run `python3 -m perfrepair.app` first")
    sites = read_sites(paths.sites)["sites"]
    scopes = read_scopes(paths.scopes)["scopes"]
    of_unit = units_by_scope(read_units(read_json(paths.units)))
    dossiers_doc = _optional(paths.dossiers)
    found = (dossiers_doc or {}).get("dossiers") or []
    dossiers = {d["scope"]["id"]: d for d in found + ((dossiers_doc or {}).get("upgrades") or [])}
    replaced = _optional(paths.replacements) or {}
    replacements = {r["scope"]: r for r in replaced.get("replacements") or []}
    sources = replaced.get("sources") or {}
    upgrades = load_upgrades(paths.upgrades)
    applied = [u for u in upgrades if u.status == UPGRADED]
    replacements |= {u.scope: u.replacement().to_json() for u in applied}
    sources = {**sources, **{u.scope: u.source for u in applied}}
    edits_doc = _optional(paths.edits)
    edits = {e["scope"]: e for e in (edits_doc or {}).get("edits") or []}
    harness = _optional(paths.harness, read_yaml) or {}
    inputs = {s["id"]: s.get("inputs") for s in harness.get("scopes") or []}
    check = read_device_check(paths, list(inputs))
    rows = _with_units([scope_row(s, dossiers.get(s["id"]), replacements.get(s["id"]), sources.get(s["id"]),
                                  edits.get(s["id"]), edits_doc is not None, check, inputs.get(s["id"]))
                        for s in sorted(scopes, key=lambda s: (s["file"], s["line"], s["id"]))], of_unit)
    return {"schemaVersion": SCHEMA_VERSION, "app": paths.app, **_named(paths), "mode": mode.name,
            "funnel": funnel(len(sites), rows, len(dossiers)), **recommendations(dossiers_doc), BROKEN_USES: _broken_uses(upgrades, scopes),
            "scopes": rows}
