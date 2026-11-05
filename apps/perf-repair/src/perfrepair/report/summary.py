"""Every <app>/report.json of a device → summary.json: the funnel summed, the modes, the pattern counts, broken uses and
the candidates not offered."""
from __future__ import annotations

from ..dto.report import BROKEN_USES, FUNNEL, SCHEMA_VERSION, pattern_counts
from .recommendations import summed
from ..stop.halt import Coded


def _broken(reports: list[dict]) -> dict:
    by_app = {r["app"]: r[BROKEN_USES]["counts"] for r in reports}
    statuses = sorted({s for counts in by_app.values() for s in counts})
    return {"all": {s: sum(c[s] for c in by_app.values()) for s in statuses}, "byApp": by_app}


def build_summary(reports: list[dict]) -> dict:
    if not reports:
        raise Coded("no_reports: no <app>/report.json in the device folder; run `python3 -m perfrepair.report app` first")
    by_app = {r["app"]: r["funnel"] for r in reports}
    return {"schemaVersion": SCHEMA_VERSION, "modes": {r["app"]: r["mode"] for r in reports},
            "apps": sorted(by_app), "named": {r["app"]: {"project": r["project"], "source": r["source"]} for r in reports},
            "funnel": {k: sum(f[k] for f in by_app.values()) for k in FUNNEL}, "byApp": by_app,
            "patterns": pattern_counts(reports), BROKEN_USES: _broken(reports), **summed(reports)}
