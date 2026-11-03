"""dossiers.json's notOffered → the report's recommendations: classes above maxChange, never applied, and reject counts."""
from __future__ import annotations

from collections import Counter

from ..dto.change import CHANGES, DROP_IN, REJECTED


def recommendations(dossiers: dict | None) -> dict:
    kept = (dossiers or {}).get("notOffered") or []
    return {"maxChange": (dossiers or {}).get("maxChange", DROP_IN),
            "recommendations": [n for n in kept if n["change"] != REJECTED],
            "rejected": dict(sorted(Counter(r for n in kept for r in n["reasons"]).items()))}


def summed(reports: list[dict]) -> dict:
    """Per class the candidates the reports recommend, per reason those they reject; a report before them adds none."""
    found = [n["change"] for r in reports for n in r.get("recommendations") or []]
    rejected: Counter = Counter()
    for r in reports:
        rejected.update(r.get("rejected") or {})
    return {"recommendations": {c: found.count(c) for c in CHANGES if c in found}, "rejected": dict(sorted(rejected.items()))}
