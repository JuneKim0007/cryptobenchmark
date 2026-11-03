"""<device>/<app>/: every step's file → report.json: a row per scope and the app's funnel. A step whose file is absent
is `not_run`; sites.json and scopes.json are required."""
from __future__ import annotations

from ..dto.report import MEASURABLE, SCHEMA_VERSION, stayed, unit_counts
from ..dto.unit import read_units, units_by_scope
from ..dto.units import DisplayUnits
from ..files import read_json, read_yaml
from ..result.modes import Mode
from ..app.facts.project import project_name
from ..run_dir import AppPaths, read_scopes, read_sites
from .measured import read_measured
from .recommendations import recommendations
from .scope_row import scope_row


def _optional(path, read=read_json) -> dict | None:
    return read(path) if path.is_file() else None


def _measured(row: dict) -> bool:
    return row["interop"]["status"] in MEASURABLE and any(m["measured"] for m in row["metrics"])


def funnel(sites: int, rows: list[dict], with_options: int) -> dict:
    units = unit_counts(rows)
    return {"sites": sites, "scopes": len(rows), "units": units["units"], "withOptions": with_options,
            "replace": sum(r["decision"]["decision"] == "replace" for r in rows), "unitsReplace": units["unitsReplace"],
            "applied": sum(r["edit"]["status"] == "applied" for r in rows),
            "compiled": sum(r["compile"]["status"] == "compiled" for r in rows),
            "interopPassed": sum(r["interop"]["status"] == "passed" for r in rows),
            "measured": sum(_measured(r) for r in rows),
            "measuredUnchecked": sum(_measured(r) and r["interop"]["status"] == "unchecked" for r in rows)}


def _with_units(rows: list[dict], of_unit: dict) -> list[dict]:
    rows = [{**r, "unit": of_unit[r["scope"]].id, "sharedFunction": list(of_unit[r["scope"]].sharedFunction)} for r in rows]
    stays = stayed(rows)
    return [{**r, "stayed": stays[r["unit"]]} for r in rows]


def _named(paths: AppPaths) -> dict:
    """The project and source beside the id: two projects can share a last folder name."""
    doc = _optional(paths.facts) or {}
    root = doc.get("root")
    return {"project": project_name(root) if root else paths.app, "source": root}


def build_report(paths: AppPaths, mode: Mode, units: DisplayUnits) -> dict:
    for required in (paths.sites, paths.scopes, paths.units):
        if not required.is_file():
            raise FileNotFoundError(f"missing_step: {required} absent; run `python3 -m perfrepair.app` first")
    sites = read_sites(paths.sites)["sites"]
    scopes = read_scopes(paths.scopes)["scopes"]
    of_unit = units_by_scope(read_units(read_json(paths.units)))
    dossiers_doc = _optional(paths.dossiers)
    dossiers = {d["scope"]["id"]: d for d in (dossiers_doc or {}).get("dossiers") or []}
    replaced = _optional(paths.replacements) or {}
    replacements = {r["scope"]: r for r in replaced.get("replacements") or []}
    sources = replaced.get("sources") or {}
    stale = set(replaced.get("stale", ()))
    edits_doc = _optional(paths.edits)
    edits = {e["scope"]: e for e in (edits_doc or {}).get("edits") or []}
    harness = _optional(paths.harness, read_yaml) or {}
    inputs = {s["id"]: s.get("inputs") for s in harness.get("scopes") or []}
    measured = read_measured(paths, list(inputs))
    rows = _with_units([scope_row(s, dossiers.get(s["id"]), replacements.get(s["id"]), sources.get(s["id"]),
                                  edits.get(s["id"]), edits_doc is not None, measured, mode, inputs.get(s["id"]), units,
                                  s["id"] in stale)
                        for s in sorted(scopes, key=lambda s: (s["file"], s["line"], s["id"]))], of_unit)
    return {"schemaVersion": SCHEMA_VERSION, "app": paths.app, **_named(paths), "mode": mode.name, "units": units.to_json(),
            "measuredFrom": str(paths.scoped_benchmark.relative_to(paths.root)) if measured.cases else None,
            "funnel": funnel(len(sites), rows, len(dossiers)), **recommendations(dossiers_doc), "scopes": rows}
