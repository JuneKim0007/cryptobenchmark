"""<device>/<app>/: every step's file → report.json: a row per scope and the app's funnel. A step whose file is absent
is `not_run`; sites.json and scopes.json are required."""
from __future__ import annotations

from ..dto.report import MEASURABLE, SCHEMA_VERSION
from ..files import read_json, read_yaml
from ..result.modes import Mode
from ..run_dir import AppPaths
from .measured import read_measured
from .scope_row import scope_row


def _optional(path, read=read_json) -> dict | None:
    return read(path) if path.is_file() else None


def _measured(row: dict) -> bool:
    return row["interop"]["status"] in MEASURABLE and any(m["measured"] for m in row["metrics"])


def funnel(sites: int, rows: list[dict], with_options: int) -> dict:
    return {"sites": sites, "scopes": len(rows), "withOptions": with_options,
            "replace": sum(r["decision"]["decision"] == "replace" for r in rows),
            "applied": sum(r["edit"]["status"] == "applied" for r in rows),
            "compiled": sum(r["compile"]["status"] == "compiled" for r in rows),
            "interopPassed": sum(r["interop"]["status"] == "passed" for r in rows),
            "measured": sum(_measured(r) for r in rows),
            "measuredUnchecked": sum(_measured(r) and r["interop"]["status"] == "unchecked" for r in rows)}


def build_report(paths: AppPaths, mode: Mode) -> dict:
    for required in (paths.sites, paths.scopes):
        if not required.is_file():
            raise FileNotFoundError(f"missing_step: {required} absent; run `python3 -m perfrepair.app` first")
    sites = read_json(paths.sites)["sites"]
    scopes = read_json(paths.scopes)["scopes"]
    dossiers = {d["scope"]["id"]: d for d in (_optional(paths.dossiers) or {}).get("dossiers") or []}
    replaced = _optional(paths.replacements) or {}
    replacements = {r["scope"]: r for r in replaced.get("replacements") or []}
    sources = replaced.get("sources") or {}
    edits_doc = _optional(paths.edits)
    edits = {e["scope"]: e for e in (edits_doc or {}).get("edits") or []}
    harness = _optional(paths.harness, read_yaml) or {}
    inputs = {s["id"]: s.get("inputs") for s in harness.get("scopes") or []}
    measured = read_measured(paths, list(inputs))
    rows = [scope_row(s, dossiers.get(s["id"]), replacements.get(s["id"]), sources.get(s["id"]),
                      edits.get(s["id"]), edits_doc is not None, measured, mode, inputs.get(s["id"]))
            for s in sorted(scopes, key=lambda s: (s["file"], s["line"], s["id"]))]
    return {"schemaVersion": SCHEMA_VERSION, "app": paths.app, "mode": mode.name,
            "measuredFrom": str(paths.scoped_benchmark.relative_to(paths.root)) if measured.cases else None,
            "funnel": funnel(len(sites), rows, len(dossiers)), "scopes": rows}
