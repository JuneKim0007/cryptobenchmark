"""Every <app>/report.json of a device → summary.json: the funnel summed, and per selected metric the apps improved,
unchanged or worse by the median of their measured scopes' ratios, under each app's own perfMode; the labels, the swaps."""
from __future__ import annotations

import statistics

from ..dto.measurement import ESTIMATED
from ..dto.metrics import BY_NAME, NAMES
from ..dto.report import CHANGES, FUNNEL, SCHEMA_VERSION, THERMAL_MISMATCH, THERMAL_THROTTLED
from ..dto.perf_mode import PerfMode
from ..result.modes import criteria
from .recommendations import summed
from .swaps import label_counts, swaps
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


def _metrics(reports: list[dict], improving: float, selected: dict[str, tuple[str, ...]]) -> dict:
    """The selected metrics of any app; an app counts under the metrics its own perfMode selected."""
    chosen = [m for m in NAMES if any(m in names for names in selected.values())]
    return {metric: _metric(reports, metric, improving, selected) for metric in chosen}


def _metric(reports: list[dict], metric: str, improving: float, selected: dict[str, tuple[str, ...]]) -> dict:
    ratios = {r["app"]: app_ratio(r, metric) if metric in selected[r["app"]] else None for r in reports}
    measured = [v for v in ratios.values() if v is not None]
    return {"unit": BY_NAME[metric].unit, "ratios": ratios,
            "apps": {c: sorted(a for a, v in ratios.items() if change(v, improving) == c) for c in CHANGES},
            "medianChange": statistics.median(measured) - 1 if measured else None, **_estimated_in(reports, metric)}


def _thermal(reports: list[dict]) -> dict:
    rows = [(s.get("thermal") or {}).get("labels") or () for r in reports for s in r["scopes"]]
    return {THERMAL_MISMATCH: sum(THERMAL_MISMATCH in x for x in rows), THERMAL_THROTTLED: sum(THERMAL_THROTTLED in x for x in rows)}


def build_summary(reports: list[dict]) -> dict:
    if not reports:
        raise Coded("no_reports: no <app>/report.json in the device folder; run `python3 -m perfrepair.report app` first")
    improving = float(criteria()["improvingRatio"])
    by_app = {r["app"]: r["funnel"] for r in reports}
    selected = {r["app"]: PerfMode.parse(r["mode"]).names for r in reports}
    return {"schemaVersion": SCHEMA_VERSION, "modes": {r["app"]: r["mode"] for r in reports}, "improvingRatio": improving,
            "apps": sorted(by_app), "named": {r["app"]: {"project": r["project"], "source": r["source"]} for r in reports},
            "funnel": {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}, "byApp": by_app,
            "metrics": _metrics(reports, improving, selected), "labels": label_counts(reports), "swaps": swaps(reports),
            "thermal": _thermal(reports), **summed(reports)}
