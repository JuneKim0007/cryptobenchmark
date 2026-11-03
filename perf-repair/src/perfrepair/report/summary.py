"""Every <app>/report.json of a device → summary.json: the funnel summed, and per selected metric the apps improved,
unchanged or worse by the median of their measured scopes' ratios."""
from __future__ import annotations

import statistics

from ..dto.measurement import ESTIMATED
from ..dto.metrics import BY_NAME
from ..dto.report import CHANGES, FUNNEL, SCHEMA_VERSION
from ..dto.perf_mode import PerfMode
from ..result.modes import mode_of
from .recommendations import summed
from ..stop.halt import Coded


def app_ratio(report: dict, metric: str) -> float | None:
    ratios = [m["ratio"] for s in report["scopes"] for m in s["metrics"]
              if m["metric"] == metric and m["measured"] and m["ratio"] is not None]
    return statistics.median(ratios) if ratios else None


def _estimated_in(reports: list[dict], metric: str) -> dict:
    apps = sorted(r["app"] for r in reports for s in r["scopes"] for m in s["metrics"]
                  if m["metric"] == metric and m.get("kind") == ESTIMATED)
    return {"estimatedIn": sorted(set(apps))} if apps else {}


def change(ratio: float | None, improving: float) -> str:
    """improving is criteria.yaml's improvingRatio; its inverse bounds `worse` the same way."""
    if ratio is None:
        return "notMeasured"
    return "improved" if ratio <= improving else "worse" if ratio >= 1 / improving else "unchanged"


def build_summary(reports: list[dict]) -> dict:
    if not reports:
        raise Coded("no_reports: no <app>/report.json in the device folder; run `python3 -m perfrepair.report app` first")
    modes = sorted({r["mode"] for r in reports})
    if len(modes) != 1:
        raise Coded(f"mixed_modes: the app reports were built in modes {modes}; rebuild them in one mode")
    mode = mode_of(PerfMode.parse(modes[0]))
    improving = mode.improvingRatio
    by_app = {r["app"]: r["funnel"] for r in reports}
    metrics = {}
    for metric in mode.perf.names:
        unit = BY_NAME[metric].unit
        ratios = {r["app"]: app_ratio(r, metric) for r in reports}
        measured = [v for v in ratios.values() if v is not None]
        metrics[metric] = {"unit": unit, "ratios": ratios,
                           "apps": {c: sorted(a for a, v in ratios.items() if change(v, improving) == c)
                                    for c in CHANGES},
                           "medianChange": statistics.median(measured) - 1 if measured else None,
                           **_estimated_in(reports, metric)}
    return {"schemaVersion": SCHEMA_VERSION, "mode": modes[0], "improvingRatio": improving, "apps": sorted(by_app),
            "funnel": {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}, "byApp": by_app, "metrics": metrics,
            **summed(reports)}
